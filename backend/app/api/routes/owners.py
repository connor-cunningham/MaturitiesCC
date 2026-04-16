from datetime import date
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from app.core.database import get_db
from app.models.canonical import CanonicalOwner, CanonicalProperty, CanonicalLoan

router = APIRouter(prefix="/owners", tags=["owners"])


class OwnerUpdate(BaseModel):
    display_name: Optional[str] = None
    ownership_type: Optional[str] = None
    hq_city: Optional[str] = None
    hq_state: Optional[str] = None
    website: Optional[str] = None
    tags: Optional[list] = None
    outreach_stage: Optional[str] = None
    last_contact_date: Optional[date] = None
    next_followup_date: Optional[date] = None
    relationship_strength: Optional[str] = None
    target_tier: Optional[str] = None
    internal_notes: Optional[str] = None


@router.get("")
async def list_owners(
    state: Optional[str] = None,
    outreach_stage: Optional[str] = None,
    target_tier: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "priority_score",
    sort_dir: str = "desc",
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(CanonicalOwner).options(
        selectinload(CanonicalOwner.properties),
        selectinload(CanonicalOwner.loans),
    )
    filters = []

    if outreach_stage:
        filters.append(CanonicalOwner.outreach_stage == outreach_stage)
    if target_tier:
        filters.append(CanonicalOwner.target_tier == target_tier)
    if search:
        filters.append(CanonicalOwner.display_name.ilike(f"%{search}%"))
    if state:
        pass  # handled via join if needed

    if filters:
        query = query.where(and_(*filters))

    sort_col = getattr(CanonicalOwner, sort_by, CanonicalOwner.priority_score)
    if sort_dir == "desc":
        query = query.order_by(sort_col.desc().nullslast())
    else:
        query = query.order_by(sort_col.asc())

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    offset = (page - 1) * limit
    result = await db.execute(query.offset(offset).limit(limit))
    owners = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [_serialize_owner(o) for o in owners],
    }


@router.get("/{owner_id}")
async def get_owner(owner_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CanonicalOwner)
        .options(
            selectinload(CanonicalOwner.properties).selectinload(CanonicalProperty.loans),
            selectinload(CanonicalOwner.loans),
            selectinload(CanonicalOwner.aliases),
        )
        .where(CanonicalOwner.id == owner_id)
    )
    owner = result.scalars().first()
    if not owner:
        raise HTTPException(404, "Owner not found")
    return _serialize_owner(owner, detail=True)


@router.get("/{owner_id}/portfolio")
async def get_owner_portfolio(owner_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CanonicalOwner)
        .options(
            selectinload(CanonicalOwner.properties).selectinload(CanonicalProperty.loans),
            selectinload(CanonicalOwner.loans),
        )
        .where(CanonicalOwner.id == owner_id)
    )
    owner = result.scalars().first()
    if not owner:
        raise HTTPException(404, "Owner not found")

    today = date.today()
    loans = owner.loans or []
    properties = owner.properties or []

    total_units = sum(p.units or 0 for p in properties)
    total_original_amount = sum(l.original_amount or 0 for l in loans)
    total_current_balance = sum(l.current_balance or 0 for l in loans if l.current_balance)

    # Maturity ladder
    maturity_buckets = {"0-6mo": 0, "6-12mo": 0, "12-24mo": 0, "24-36mo": 0, "36mo+": 0}
    for loan in loans:
        if not loan.maturity_date:
            continue
        months = (loan.maturity_date - today).days / 30.44
        if months < 6:
            maturity_buckets["0-6mo"] += 1
        elif months < 12:
            maturity_buckets["6-12mo"] += 1
        elif months < 24:
            maturity_buckets["12-24mo"] += 1
        elif months < 36:
            maturity_buckets["24-36mo"] += 1
        else:
            maturity_buckets["36mo+"] += 1

    # Geographic exposure
    states = {}
    for prop in properties:
        if prop.state:
            states[prop.state] = states.get(prop.state, 0) + 1

    return {
        "owner": _serialize_owner(owner),
        "summary": {
            "total_properties": len(properties),
            "total_loans": len(loans),
            "total_units": total_units,
            "total_original_amount": total_original_amount,
            "total_current_balance": total_current_balance,
            "maturity_ladder": maturity_buckets,
            "geographic_exposure": states,
        },
        "properties": [
            {
                "id": str(p.id),
                "name": p.display_name,
                "city": p.city,
                "state": p.state,
                "units": p.units,
                "building_class": p.building_class,
                "loans": [
                    {
                        "id": str(l.id),
                        "maturity_date": str(l.maturity_date) if l.maturity_date else None,
                        "original_amount": l.original_amount,
                        "rate_type": l.rate_type,
                        "lender": l.lender,
                        "priority_score": l.priority_score,
                    }
                    for l in (p.loans or [])
                ],
            }
            for p in properties
        ],
    }


@router.patch("/{owner_id}")
async def update_owner(owner_id: UUID, body: OwnerUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CanonicalOwner).where(CanonicalOwner.id == owner_id))
    owner = result.scalars().first()
    if not owner:
        raise HTTPException(404, "Owner not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(owner, k, v)
    from datetime import datetime
    owner.updated_at = datetime.utcnow()
    await db.commit()
    return _serialize_owner(owner)


def _serialize_owner(owner: CanonicalOwner, detail: bool = False) -> dict:
    today = date.today()
    loans = owner.loans or []
    properties = owner.properties or []

    upcoming = [l for l in loans if l.maturity_date and l.maturity_date >= today]
    upcoming_12mo = [l for l in upcoming if (l.maturity_date - today).days <= 365]

    d = {
        "id": str(owner.id),
        "display_name": owner.display_name,
        "normalized_name": owner.normalized_name,
        "ownership_type": owner.ownership_type,
        "hq_city": owner.hq_city,
        "hq_state": owner.hq_state,
        "website": owner.website,
        "tags": owner.tags,
        "outreach_stage": owner.outreach_stage,
        "last_contact_date": str(owner.last_contact_date) if owner.last_contact_date else None,
        "next_followup_date": str(owner.next_followup_date) if owner.next_followup_date else None,
        "relationship_strength": owner.relationship_strength,
        "priority_score": owner.priority_score,
        "target_tier": owner.target_tier,
        "internal_notes": owner.internal_notes,
        "property_count": len(properties),
        "loan_count": len(loans),
        "total_units": sum(p.units or 0 for p in properties),
        "upcoming_maturities": len(upcoming),
        "maturities_12mo": len(upcoming_12mo),
        "total_upcoming_volume": sum(l.original_amount or 0 for l in upcoming),
        "created_at": str(owner.created_at),
        "updated_at": str(owner.updated_at),
    }
    if detail:
        d["aliases"] = [a.alias_name for a in (owner.aliases or [])]
    return d
