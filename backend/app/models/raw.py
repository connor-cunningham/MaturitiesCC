import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Text, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import enum


class SourceType(str, enum.Enum):
    costar = "costar"
    msci = "msci"
    internal = "internal"
    other = "other"


class ImportStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    complete = "complete"
    failed = "failed"


class SourceFile(Base):
    __tablename__ = "source_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename: Mapped[str] = mapped_column(String(500))
    stored_path: Mapped[str] = mapped_column(String(1000))
    source_type: Mapped[str] = mapped_column(String(50))
    file_size: Mapped[int | None] = mapped_column(Integer)
    mime_type: Mapped[str | None] = mapped_column(String(200))
    sheet_count: Mapped[int | None] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    import_runs: Mapped[list["ImportRun"]] = relationship(back_populates="source_file")


class ImportRun(Base):
    __tablename__ = "import_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_file_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("source_files.id"))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    mapping_config: Mapped[dict | None] = mapped_column(JSON)
    rows_processed: Mapped[int] = mapped_column(Integer, default=0)
    rows_inserted: Mapped[int] = mapped_column(Integer, default=0)
    rows_merged: Mapped[int] = mapped_column(Integer, default=0)
    rows_skipped: Mapped[int] = mapped_column(Integer, default=0)
    rows_queued: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[list | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    source_file: Mapped["SourceFile | None"] = relationship(back_populates="import_runs")
    raw_loan_records: Mapped[list["RawLoanRecord"]] = relationship(back_populates="import_run")
    raw_property_records: Mapped[list["RawPropertyRecord"]] = relationship(back_populates="import_run")
    raw_owner_records: Mapped[list["RawOwnerRecord"]] = relationship(back_populates="import_run")


class RawLoanRecord(Base):
    __tablename__ = "raw_loan_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("import_runs.id"))
    source_type: Mapped[str] = mapped_column(String(50))
    row_index: Mapped[int | None] = mapped_column(Integer)
    raw_data: Mapped[dict] = mapped_column(JSON)
    normalized_data: Mapped[dict | None] = mapped_column(JSON)
    canonical_loan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical_loans.id"), nullable=True)
    match_confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    import_run: Mapped["ImportRun"] = relationship(back_populates="raw_loan_records")


class RawPropertyRecord(Base):
    __tablename__ = "raw_property_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("import_runs.id"))
    source_type: Mapped[str] = mapped_column(String(50))
    row_index: Mapped[int | None] = mapped_column(Integer)
    raw_data: Mapped[dict] = mapped_column(JSON)
    normalized_data: Mapped[dict | None] = mapped_column(JSON)
    canonical_property_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical_properties.id"), nullable=True)
    match_confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    import_run: Mapped["ImportRun"] = relationship(back_populates="raw_property_records")


class RawOwnerRecord(Base):
    __tablename__ = "raw_owner_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("import_runs.id"))
    source_type: Mapped[str] = mapped_column(String(50))
    row_index: Mapped[int | None] = mapped_column(Integer)
    raw_data: Mapped[dict] = mapped_column(JSON)
    normalized_data: Mapped[dict | None] = mapped_column(JSON)
    canonical_owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical_owners.id"), nullable=True)
    match_confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    import_run: Mapped["ImportRun"] = relationship(back_populates="raw_owner_records")
