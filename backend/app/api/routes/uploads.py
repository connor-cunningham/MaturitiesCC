import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.config import settings
from app.models.raw import SourceFile, ImportRun
from app.etl.parsers.costar import CoStarParser
from app.etl.parsers.msci import MSCIParser
from app.etl.parsers.internal import InternalParser
from app.etl.pipeline import run_import_pipeline
import json

router = APIRouter(prefix="/uploads", tags=["uploads"])

PARSERS = {
    "costar": CoStarParser(),
    "msci": MSCIParser(),
    "internal": InternalParser(),
    "other": InternalParser(),
}


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    source_type: str = Form("other"),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file and return its preview (sheets + columns). Does not trigger import."""
    allowed = {"costar", "msci", "internal", "other"}
    if source_type not in allowed:
        raise HTTPException(400, f"source_type must be one of {allowed}")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in (".xlsx", ".xls", ".csv"):
        raise HTTPException(400, "Only .xlsx, .xls, and .csv files are supported")

    stored_name = f"{uuid.uuid4()}{ext}"
    stored_path = settings.upload_path / stored_name
    with stored_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = stored_path.stat().st_size

    # Get sheet preview
    parser = PARSERS.get(source_type, PARSERS["other"])
    try:
        preview = parser.get_sheet_preview(stored_path)
    except Exception as e:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(400, f"Could not read file: {e}")

    source_file = SourceFile(
        original_filename=file.filename,
        stored_path=str(stored_path),
        source_type=source_type,
        file_size=file_size,
        mime_type=file.content_type,
        sheet_count=len(preview.get("sheets", [])),
        uploaded_at=datetime.utcnow(),
    )
    db.add(source_file)
    await db.commit()
    await db.refresh(source_file)

    return {
        "source_file_id": str(source_file.id),
        "filename": file.filename,
        "source_type": source_type,
        "file_size": file_size,
        **preview,
    }


@router.get("/{source_file_id}/preview")
async def get_file_preview(source_file_id: uuid.UUID, sheet: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    sf = await db.get(SourceFile, source_file_id)
    if not sf:
        raise HTTPException(404, "File not found")
    parser = PARSERS.get(sf.source_type, PARSERS["other"])
    preview = parser.get_sheet_preview(sf.stored_path)
    return preview


@router.post("/import")
async def start_import(
    background_tasks: BackgroundTasks,
    source_file_id: uuid.UUID = Form(...),
    sheet_name: Optional[str] = Form(None),
    mapping_config: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Start an import run for a previously uploaded file."""
    sf = await db.get(SourceFile, source_file_id)
    if not sf:
        raise HTTPException(404, "Source file not found")

    mapping = None
    if mapping_config:
        try:
            mapping = json.loads(mapping_config)
        except json.JSONDecodeError:
            raise HTTPException(400, "mapping_config must be valid JSON")

    import_run = ImportRun(
        source_file_id=source_file_id,
        status="processing",
        mapping_config=mapping,
        started_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.add(import_run)
    await db.commit()
    await db.refresh(import_run)

    # Run pipeline synchronously for v1 (background task for large files later)
    parser = PARSERS.get(sf.source_type, PARSERS["other"])
    try:
        records = parser.parse(sf.stored_path, sheet_name=sheet_name, mapping_config=mapping)
        stats = await run_import_pipeline(db, import_run, records, sf.source_type)
    except Exception as e:
        import_run.status = "failed"
        import_run.errors = [{"error": str(e)}]
        import_run.finished_at = datetime.utcnow()
        await db.commit()
        raise HTTPException(500, f"Import failed: {e}")

    # Recompute scores after import
    from app.scoring.engine import run_scoring
    await run_scoring(db)

    return {
        "import_run_id": str(import_run.id),
        "status": import_run.status,
        "stats": stats,
    }


@router.get("/imports")
async def list_imports(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ImportRun).order_by(ImportRun.created_at.desc()).limit(50)
    )
    runs = result.scalars().all()
    return [_serialize_run(r) for r in runs]


@router.get("/imports/{run_id}")
async def get_import_run(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    run = await db.get(ImportRun, run_id)
    if not run:
        raise HTTPException(404, "Import run not found")
    return _serialize_run(run)


@router.get("/imports/{run_id}/queue")
async def get_match_queue(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Return pending match candidates for manual review."""
    from app.models.links import MatchCandidate
    result = await db.execute(
        select(MatchCandidate)
        .where(MatchCandidate.import_run_id == run_id, MatchCandidate.status == "pending")
    )
    candidates = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "entity_type": c.entity_type,
            "candidate_a_id": str(c.candidate_a_id),
            "candidate_b_id": str(c.candidate_b_id),
            "confidence": c.confidence,
            "match_reasons": c.match_reasons,
        }
        for c in candidates
    ]


@router.post("/imports/{run_id}/resolve")
async def resolve_match_candidates(
    run_id: uuid.UUID,
    decisions: list[dict],
    db: AsyncSession = Depends(get_db),
):
    """
    Accept or reject match candidates.
    decisions: [{"candidate_id": "...", "decision": "merge"|"reject"}]
    """
    from app.models.links import MatchCandidate
    from datetime import datetime

    for decision in decisions:
        cid = uuid.UUID(decision["candidate_id"])
        candidate = await db.get(MatchCandidate, cid)
        if not candidate:
            continue
        action = decision.get("decision", "reject")
        candidate.status = "merged" if action == "merge" else "rejected"
        candidate.resolved_at = datetime.utcnow()

    await db.commit()
    return {"resolved": len(decisions)}


def _serialize_run(run: ImportRun) -> dict:
    return {
        "id": str(run.id),
        "source_file_id": str(run.source_file_id) if run.source_file_id else None,
        "status": run.status,
        "rows_processed": run.rows_processed,
        "rows_inserted": run.rows_inserted,
        "rows_merged": run.rows_merged,
        "rows_skipped": run.rows_skipped,
        "rows_queued": run.rows_queued,
        "errors": run.errors,
        "started_at": str(run.started_at) if run.started_at else None,
        "finished_at": str(run.finished_at) if run.finished_at else None,
        "created_at": str(run.created_at),
    }
