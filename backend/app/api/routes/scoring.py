import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.core.database import get_db
from app.models.scoring import ScoreConfig, ScoreResult, DEFAULT_FACTOR_WEIGHTS
from app.scoring.engine import run_scoring

router = APIRouter(prefix="/scoring", tags=["scoring"])


class ScoreConfigCreate(BaseModel):
    name: str
    description: Optional[str] = None
    factor_weights: dict


class ScoreConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    factor_weights: Optional[dict] = None
    is_active: Optional[bool] = None


@router.get("/configs")
async def list_configs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScoreConfig).order_by(ScoreConfig.created_at.desc()))
    return [_serialize_config(c) for c in result.scalars().all()]


@router.post("/configs")
async def create_config(body: ScoreConfigCreate, db: AsyncSession = Depends(get_db)):
    config = ScoreConfig(
        name=body.name,
        description=body.description,
        factor_weights=body.factor_weights,
        is_active=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return _serialize_config(config)


@router.put("/configs/{config_id}")
async def update_config(config_id: uuid.UUID, body: ScoreConfigUpdate, db: AsyncSession = Depends(get_db)):
    config = await db.get(ScoreConfig, config_id)
    if not config:
        raise HTTPException(404, "Config not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(config, k, v)
    config.updated_at = datetime.utcnow()
    await db.commit()
    return _serialize_config(config)


@router.post("/run")
async def trigger_scoring(db: AsyncSession = Depends(get_db)):
    count = await run_scoring(db)
    return {"scored": count, "message": f"Computed scores for {count} loans"}


@router.get("/results/{entity_type}/{entity_id}")
async def get_score_results(entity_type: str, entity_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ScoreResult)
        .where(ScoreResult.entity_type == entity_type, ScoreResult.entity_id == entity_id)
        .order_by(ScoreResult.computed_at.desc())
        .limit(5)
    )
    return [
        {
            "id": str(r.id),
            "total_score": r.total_score,
            "factor_scores": r.factor_scores,
            "computed_at": str(r.computed_at),
        }
        for r in result.scalars().all()
    ]


@router.get("/defaults")
async def get_default_weights():
    return DEFAULT_FACTOR_WEIGHTS


def _serialize_config(c: ScoreConfig) -> dict:
    return {
        "id": str(c.id),
        "name": c.name,
        "description": c.description,
        "factor_weights": c.factor_weights,
        "is_active": c.is_active,
        "created_at": str(c.created_at),
        "updated_at": str(c.updated_at),
    }
