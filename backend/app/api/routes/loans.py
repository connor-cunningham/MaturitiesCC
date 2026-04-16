from datetime import date
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from app.core.database import get_db
from app.models.canonical import CanonicalLoan, CanonicalProperty, CanonicalOwner

router = APIRouter(prefix="/loans", tags=["loans"])


class LoanUpdate(BaseModel):
    lender: Optional[str] = None
    originator: Optional[str] = None
    servicer: Optional[str] = None
    rate_type: Optional[str] = None
    coupon: Optional[float] = None
    io_flag: Optional[bool] = None
    maturity_date: Optional[date] = None
    original_amount: Optional[float] = None
    current_balance: Optional[float] = None
    status: Optional[str] = None
    internal_notes: Optional[str] = None


@router.get("")
async def list_loans(
    maturity_start: Optional[date] = None,
    maturity_end: Optional[date] = None,
    owner_id: Optional[UUID] = None,
    property_id: Optional[UUID] = None,
    lender: Optional[str] = None,
    state: Optional[str] = None,
    rate_type: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    io_flag: Optional[bool] = None,
    loan_type: Optional[str] = None,
    status: Optional[str] = "active",
    sort_by: str = "maturity_date",
    sort_dir: str = "asc",
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(CanonicalLoan)
        .options(
            selectinload(CanonicalLoan.property),
            selectinload(CanonicalLoan.owner),
        )
    )
    filters = []

    if maturity_start:
        filters.append(CanonicalLoan.maturity_date >= maturity_start)
    if maturity_end:
        filters.append(CanonicalLoan.maturity_date <= maturity_end)
    if owner_id:
        filters.append(CanonicalLoan.owner_id == owner_id)
    if property_id:
        filters.append(CanonicalLoan.property_id == property_id)
    if lender:
        filters.append(CanonicalLoan.lender.ilike(f"%{lender}%"))
    if rate_type:
        filters.append(CanonicalLoan.rate_type.ilike(f"%{rate_type}%"))
    if min_amount:
        filters.append(CanonicalLoan.original_amount >= min_amount)
    if max_amount:
        filters.append(CanonicalLoan.original_amount <= max_amount)
    if io_flag is not None:
        filters.append(CanonicalLoan.io_flag == io_flag)
    if loan_type:
        filters.append(CanonicalLoan.loan_type.ilike(f"%{loan_type}%"))
    if status:
        filters.append(CanonicalLoan.status == status)
    if state:
        query = query.join(CanonicalProperty, CanonicalLoan.property_id == CanonicalProperty.id)
        filters.append(CanonicalProperty.state == state.upper())

    if filters:
        query = query.where(and_(*filters))

    sort_col = getattr(CanonicalLoan, sort_by, CanonicalLoan.maturity_date)
    query = query.order_by(sort_col.asc() if sort_dir == "asc" else sort_col.desc())

    total = await db.scalar(select(func.count()).select_from(query.subquery()))

    offset = (page - 1) * limit
    result = await db.execute(query.offset(offset).limit(limit))
    loans = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [_serialize_loan(l) for l in loans],
    }


@router.get("/{loan_id}")
async def get_loan(loan_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CanonicalLoan)
        .options(
            selectinload(CanonicalLoan.property),
            selectinload(CanonicalLoan.owner),
            selectinload(CanonicalLoan.source_mappings),
        )
        .where(CanonicalLoan.id == loan_id)
    )
    loan = result.scalars().first()
    if not loan:
        raise HTTPException(404, "Loan not found")
    return _serialize_loan(loan, detail=True)


@router.patch("/{loan_id}")
async def update_loan(loan_id: UUID, body: LoanUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CanonicalLoan).where(CanonicalLoan.id == loan_id))
    loan = result.scalars().first()
    if not loan:
        raise HTTPException(404, "Loan not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(loan, k, v)
    from datetime import datetime
    loan.updated_at = datetime.utcnow()
    await db.commit()
    return _serialize_loan(loan)


def _serialize_loan(loan: CanonicalLoan, detail: bool = False) -> dict:
    today = date.today()
    months_to_maturity = None
    if loan.maturity_date:
        months_to_maturity = round((loan.maturity_date - today).days / 30.44, 1)

    d = {
        "id": str(loan.id),
        "display_name": loan.display_name,
        "property_id": str(loan.property_id) if loan.property_id else None,
        "property_name": loan.property.display_name if loan.property else None,
        "property_city": loan.property.city if loan.property else None,
        "property_state": loan.property.state if loan.property else None,
        "owner_id": str(loan.owner_id) if loan.owner_id else None,
        "owner_name": loan.owner.display_name if loan.owner else None,
        "lender": loan.lender,
        "originator": loan.originator,
        "servicer": loan.servicer,
        "origination_date": str(loan.origination_date) if loan.origination_date else None,
        "maturity_date": str(loan.maturity_date) if loan.maturity_date else None,
        "months_to_maturity": months_to_maturity,
        "original_amount": loan.original_amount,
        "current_balance": loan.current_balance,
        "rate_type": loan.rate_type,
        "coupon": loan.coupon,
        "io_flag": loan.io_flag,
        "amortization": loan.amortization,
        "term": loan.term,
        "loan_type": loan.loan_type,
        "recourse": loan.recourse,
        "prepay_structure": loan.prepay_structure,
        "status": loan.status,
        "priority_score": loan.priority_score,
        "source_precedence": loan.source_precedence,
        "internal_notes": loan.internal_notes,
        "created_at": str(loan.created_at),
        "updated_at": str(loan.updated_at),
    }
    if detail:
        d["provenance"] = loan.provenance
        d["source_mappings"] = [
            {"id": str(m.id), "source_type": m.source_type}
            for m in (loan.source_mappings or [])
        ]
    return d
