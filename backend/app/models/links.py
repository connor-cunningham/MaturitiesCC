import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, JSON, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class OwnerAlias(Base):
    __tablename__ = "owner_aliases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical_owners.id"))
    alias_name: Mapped[str] = mapped_column(String(500))
    normalized_alias: Mapped[str] = mapped_column(String(500), index=True)
    source_type: Mapped[str | None] = mapped_column(String(50))
    import_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("import_runs.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner: Mapped["CanonicalOwner"] = relationship(back_populates="aliases")  # type: ignore[name-defined]


class PropertyAlias(Base):
    __tablename__ = "property_aliases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical_properties.id"))
    alias_name: Mapped[str] = mapped_column(String(500))
    normalized_alias: Mapped[str] = mapped_column(String(500), index=True)
    source_type: Mapped[str | None] = mapped_column(String(50))
    import_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("import_runs.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    property: Mapped["CanonicalProperty"] = relationship(back_populates="aliases")  # type: ignore[name-defined]


class LoanSourceMapping(Base):
    __tablename__ = "loan_source_mappings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_loan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical_loans.id"))
    raw_loan_record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("raw_loan_records.id"))
    source_type: Mapped[str] = mapped_column(String(50))
    field_provenance: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    canonical_loan: Mapped["CanonicalLoan"] = relationship(back_populates="source_mappings")  # type: ignore[name-defined]


class MatchCandidate(Base):
    """Pairs of entities that may be duplicates, queued for manual review."""
    __tablename__ = "match_candidates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String(50))  # owner / property / loan
    candidate_a_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    candidate_b_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    confidence: Mapped[float] = mapped_column(Float)
    match_reasons: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending / merged / rejected
    import_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("import_runs.id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ManualMatchOverride(Base):
    """User-confirmed manual entity links."""
    __tablename__ = "manual_match_overrides"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String(50))
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    canonical_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
