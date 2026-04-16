import uuid
from datetime import datetime, date
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Date, Text, JSON, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class CanonicalOwner(Base):
    __tablename__ = "canonical_owners"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    normalized_name: Mapped[str] = mapped_column(String(500), index=True)
    display_name: Mapped[str] = mapped_column(String(500))
    parent_company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical_owners.id"), nullable=True)
    ownership_type: Mapped[str | None] = mapped_column(String(100))
    hq_city: Mapped[str | None] = mapped_column(String(200))
    hq_state: Mapped[str | None] = mapped_column(String(50))
    website: Mapped[str | None] = mapped_column(String(500))
    tags: Mapped[list | None] = mapped_column(JSON)

    outreach_stage: Mapped[str] = mapped_column(String(100), default="cold")
    last_contact_date: Mapped[date | None] = mapped_column(Date)
    next_followup_date: Mapped[date | None] = mapped_column(Date)
    relationship_strength: Mapped[str | None] = mapped_column(String(50))
    priority_score: Mapped[float | None] = mapped_column(Float)
    target_tier: Mapped[str | None] = mapped_column(String(50))
    internal_notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    properties: Mapped[list["CanonicalProperty"]] = relationship(back_populates="owner")
    loans: Mapped[list["CanonicalLoan"]] = relationship(back_populates="owner")
    aliases: Mapped[list["OwnerAlias"]] = relationship(back_populates="owner")
    children: Mapped[list["CanonicalOwner"]] = relationship(foreign_keys=[parent_company_id])


class CanonicalProperty(Base):
    __tablename__ = "canonical_properties"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str] = mapped_column(String(500))
    street: Mapped[str | None] = mapped_column(String(500))
    city: Mapped[str | None] = mapped_column(String(200), index=True)
    county: Mapped[str | None] = mapped_column(String(200))
    state: Mapped[str | None] = mapped_column(String(50), index=True)
    zip: Mapped[str | None] = mapped_column(String(20))
    submarket: Mapped[str | None] = mapped_column(String(200))
    canonical_address: Mapped[str | None] = mapped_column(String(1000))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    units: Mapped[int | None] = mapped_column(Integer)
    year_built: Mapped[int | None] = mapped_column(Integer)
    renovated_year: Mapped[int | None] = mapped_column(Integer)
    building_class: Mapped[str | None] = mapped_column(String(10))
    property_type: Mapped[str | None] = mapped_column(String(100))
    occupancy: Mapped[float | None] = mapped_column(Float)
    vacancy: Mapped[float | None] = mapped_column(Float)
    last_sale_date: Mapped[date | None] = mapped_column(Date)
    last_sale_price: Mapped[float | None] = mapped_column(Float)

    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical_owners.id"), nullable=True)
    priority_score: Mapped[float | None] = mapped_column(Float)
    internal_notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner: Mapped["CanonicalOwner | None"] = relationship(back_populates="properties")
    loans: Mapped[list["CanonicalLoan"]] = relationship(back_populates="property")
    aliases: Mapped[list["PropertyAlias"]] = relationship(back_populates="property")


class CanonicalLoan(Base):
    __tablename__ = "canonical_loans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str | None] = mapped_column(String(500))

    property_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical_properties.id"), nullable=True)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical_owners.id"), nullable=True)

    lender: Mapped[str | None] = mapped_column(String(500))
    originator: Mapped[str | None] = mapped_column(String(500))
    servicer: Mapped[str | None] = mapped_column(String(500))

    origination_date: Mapped[date | None] = mapped_column(Date)
    maturity_date: Mapped[date | None] = mapped_column(Date, index=True)

    original_amount: Mapped[float | None] = mapped_column(Float)
    current_balance: Mapped[float | None] = mapped_column(Float)

    rate_type: Mapped[str | None] = mapped_column(String(50))
    coupon: Mapped[float | None] = mapped_column(Float)
    io_flag: Mapped[bool | None] = mapped_column(Boolean)
    amortization: Mapped[int | None] = mapped_column(Integer)
    term: Mapped[int | None] = mapped_column(Integer)
    loan_type: Mapped[str | None] = mapped_column(String(100))
    recourse: Mapped[bool | None] = mapped_column(Boolean)
    prepay_structure: Mapped[str | None] = mapped_column(String(200))

    status: Mapped[str] = mapped_column(String(50), default="active")
    source_precedence: Mapped[str | None] = mapped_column(String(50))
    provenance: Mapped[dict | None] = mapped_column(JSON)

    priority_score: Mapped[float | None] = mapped_column(Float)
    internal_notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property: Mapped["CanonicalProperty | None"] = relationship(back_populates="loans")
    owner: Mapped["CanonicalOwner | None"] = relationship(back_populates="loans")
    source_mappings: Mapped[list["LoanSourceMapping"]] = relationship(back_populates="canonical_loan")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
