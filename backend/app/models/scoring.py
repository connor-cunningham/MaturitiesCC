import uuid
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

DEFAULT_FACTOR_WEIGHTS = {
    "months_to_maturity": 0.35,
    "loan_amount": 0.25,
    "portfolio_concentration": 0.15,
    "rate_type": 0.10,
    "io_flag": 0.05,
    "outreach_status": 0.05,
    "building_class": 0.03,
    "market_tier": 0.02,
}


class ScoreConfig(Base):
    __tablename__ = "score_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    factor_weights: Mapped[dict] = mapped_column(JSON, default=lambda: DEFAULT_FACTOR_WEIGHTS)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScoreResult(Base):
    __tablename__ = "score_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String(50))  # loan / property / owner
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    config_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    total_score: Mapped[float] = mapped_column(Float)
    factor_scores: Mapped[dict] = mapped_column(JSON)
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
