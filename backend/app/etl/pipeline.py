"""
ETL pipeline orchestrator.
Receives parsed row records, runs normalization + resolution, persists everything.
"""
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.raw import RawLoanRecord, RawPropertyRecord, RawOwnerRecord, ImportRun
from app.models.canonical import CanonicalLoan
from app.etl.resolution.owner_resolver import resolve_owner
from app.etl.resolution.property_resolver import resolve_property
from app.etl.resolution.loan_resolver import resolve_loan


async def run_import_pipeline(
    session: AsyncSession,
    import_run: ImportRun,
    parsed_records: list[dict],
    source_type: str,
) -> dict:
    """
    Process a list of parsed row records:
    1. Save raw records
    2. Resolve owners
    3. Resolve properties
    4. Resolve loans
    5. Update import_run stats
    """
    stats = {"inserted": 0, "merged": 0, "queued": 0, "skipped": 0, "errors": []}
    import_run_id = import_run.id

    for record in parsed_records:
        if record.get("error"):
            stats["errors"].append({"row": record.get("row_index"), "error": record["error"]})
            stats["skipped"] += 1
            continue

        try:
            # --- Owner resolution ---
            owner = None
            normalized_owner = record.get("normalized_owner_name", "")
            display_owner = record.get("owner_name", "")
            if normalized_owner or display_owner:
                raw_owner_rec = RawOwnerRecord(
                    import_run_id=import_run_id,
                    source_type=source_type,
                    row_index=record.get("row_index"),
                    raw_data={"owner_name": display_owner},
                    normalized_data={"normalized_name": normalized_owner},
                    created_at=datetime.utcnow(),
                )
                session.add(raw_owner_rec)
                await session.flush()

                owner, owner_conf, owner_action = await resolve_owner(
                    session,
                    normalized_name=normalized_owner,
                    display_name=display_owner,
                    city=record.get("city", ""),
                    state=record.get("state", ""),
                    import_run_id=import_run_id,
                    source_type=source_type,
                )
                raw_owner_rec.canonical_owner_id = owner.id
                raw_owner_rec.match_confidence = owner_conf

            # --- Property resolution ---
            raw_prop_rec = RawPropertyRecord(
                import_run_id=import_run_id,
                source_type=source_type,
                row_index=record.get("row_index"),
                raw_data=record.get("raw_data", {}),
                normalized_data={k: v for k, v in record.items() if k not in ("raw_data",)
                                 and isinstance(v, (str, int, float, bool, type(None)))},
                created_at=datetime.utcnow(),
            )
            session.add(raw_prop_rec)
            await session.flush()

            property_, prop_conf, prop_action = await resolve_property(
                session,
                record=record,
                owner_id=owner.id if owner else None,
                import_run_id=import_run_id,
                source_type=source_type,
            )
            raw_prop_rec.canonical_property_id = property_.id
            raw_prop_rec.match_confidence = prop_conf

            # --- Loan resolution (only if we have a maturity date) ---
            if record.get("maturity_date"):
                raw_loan_rec = RawLoanRecord(
                    import_run_id=import_run_id,
                    source_type=source_type,
                    row_index=record.get("row_index"),
                    raw_data=record.get("raw_data", {}),
                    normalized_data={k: v for k, v in record.items()
                                     if k not in ("raw_data",)
                                     and isinstance(v, (str, int, float, bool, type(None)))},
                    created_at=datetime.utcnow(),
                )
                session.add(raw_loan_rec)
                await session.flush()

                loan, loan_conf, loan_action = await resolve_loan(
                    session,
                    record=record,
                    property_id=property_.id,
                    owner_id=owner.id if owner else None,
                    raw_loan_id=raw_loan_rec.id,
                    import_run_id=import_run_id,
                    source_type=source_type,
                )
                raw_loan_rec.canonical_loan_id = loan.id
                raw_loan_rec.match_confidence = loan_conf

                if loan_action == "created":
                    stats["inserted"] += 1
                elif loan_action == "merged":
                    stats["merged"] += 1
                elif loan_action == "queued":
                    stats["queued"] += 1
            else:
                stats["inserted"] += 1  # property/owner created without loan

        except Exception as e:
            stats["errors"].append({"row": record.get("row_index"), "error": str(e)})
            stats["skipped"] += 1

    # Finalize import run stats
    import_run.rows_processed = len(parsed_records)
    import_run.rows_inserted = stats["inserted"]
    import_run.rows_merged = stats["merged"]
    import_run.rows_queued = stats["queued"]
    import_run.rows_skipped = stats["skipped"]
    import_run.errors = stats["errors"]
    import_run.status = "complete"
    import_run.finished_at = datetime.utcnow()

    await session.commit()
    return stats
