from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from app.core.database import get_db
from app.models.canonical import CanonicalProperty, CanonicalOwner, CanonicalLoan

router = APIRouter(prefix="/properties", tags=["properties"])


class PropertyUpdate(BaseModel):
    display_name: Optional[str] = None
    submarket: Optional[str] = None
    units: Optional[int] = None
    year_built: Optional[int] = None
    building_class: Optional[str] = None
    property_type: Optional[str] = None
    occupancy: Optional[float] = None
    vacancy: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    internal_notes: Optional[str] = None


@router.get("")
async def list_properties(
    state: Optional[str] = None,
    city: Optional[str] = None,
    submarket: Optional[str] = None,
    owner_id: Optional[UUID] = None,
    building_class: Optional[str] = None,
    property_type: Optional[str] = None,
    min_units: Optional[int] = None,
    max_units: Optional[int] = None,
    sort_by: str = "display_name",
    sort_dir: str = "asc",
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(CanonicalProperty).options(selectinload(CanonicalProperty.owner))
    filters = []

    if state:
        filters.append(CanonicalProperty.state == state.upper())
    if city:
        filters.append(CanonicalProperty.city.ilike(f"%{city}%"))
    if submarket:
        filters.append(CanonicalProperty.submarket.ilike(f"%{submarket}%"))
    if owner_id:
        filters.append(CanonicalProperty.owner_id == owner_id)
    if building_class:
        filters.append(CanonicalProperty.building_class.ilike(f"%{building_class}%"))
    if property_type:
        filters.append(CanonicalProperty.property_type.ilike(f"%{property_type}%"))
    if min_units:
        filters.append(CanonicalProperty.units >= min_units)
    if max_units:
        filters.append(CanonicalProperty.units <= max_units)

    if filters:
        query = query.where(and_(*filters))

    sort_col = getattr(CanonicalProperty, sort_by, CanonicalProperty.display_name)
    query = query.order_by(sort_col.asc() if sort_dir == "asc" else sort_col.desc())

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    offset = (page - 1) * limit
    result = await db.execute(query.offset(offset).limit(limit))
    props = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [_serialize_property(p) for p in props],
    }


@router.get("/map-pins")
async def get_map_pins(
    state: Optional[str] = None,
    min_units: Optional[int] = None,
    building_class: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Lightweight endpoint for map rendering — only returns lat/lng + basic info."""
    query = select(
        CanonicalProperty.id,
        CanonicalProperty.display_name,
        CanonicalProperty.latitude,
        CanonicalProperty.longitude,
        CanonicalProperty.city,
        CanonicalProperty.state,
        CanonicalProperty.units,
        CanonicalProperty.building_class,
        CanonicalProperty.owner_id,
        CanonicalProperty.priority_score,
    ).where(
        CanonicalProperty.latitude.isnot(None),
        CanonicalProperty.longitude.isnot(None),
    )
    filters = []
    if state:
        filters.append(CanonicalProperty.state == state.upper())
    if min_units:
        filters.append(CanonicalProperty.units >= min_units)
    if building_class:
        filters.append(CanonicalProperty.building_class.ilike(f"%{building_class}%"))
    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query)
    rows = result.all()
    return [
        {
            "id": str(r.id),
            "name": r.display_name,
            "lat": r.latitude,
            "lng": r.longitude,
            "city": r.city,
            "state": r.state,
            "units": r.units,
            "building_class": r.building_class,
            "owner_id": str(r.owner_id) if r.owner_id else None,
            "priority_score": r.priority_score,
        }
        for r in rows
    ]


@router.get("/{property_id}")
async def get_property(property_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CanonicalProperty)
        .options(
            selectinload(CanonicalProperty.owner),
            selectinload(CanonicalProperty.loans),
            selectinload(CanonicalProperty.aliases),
        )
        .where(CanonicalProperty.id == property_id)
    )
    prop = result.scalars().first()
    if not prop:
        raise HTTPException(404, "Property not found")
    return _serialize_property(prop, detail=True)


@router.patch("/{property_id}")
async def update_property(property_id: UUID, body: PropertyUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CanonicalProperty).where(CanonicalProperty.id == property_id))
    prop = result.scalars().first()
    if not prop:
        raise HTTPException(404, "Property not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(prop, k, v)
    from datetime import datetime
    prop.updated_at = datetime.utcnow()
    await db.commit()
    return _serialize_property(prop)


def _serialize_property(prop: CanonicalProperty, detail: bool = False) -> dict:
    d = {
        "id": str(prop.id),
        "display_name": prop.display_name,
        "street": prop.street,
        "city": prop.city,
        "county": prop.county,
        "state": prop.state,
        "zip": prop.zip,
        "submarket": prop.submarket,
        "canonical_address": prop.canonical_address,
        "latitude": prop.latitude,
        "longitude": prop.longitude,
        "units": prop.units,
        "year_built": prop.year_built,
        "renovated_year": prop.renovated_year,
        "building_class": prop.building_class,
        "property_type": prop.property_type,
        "occupancy": prop.occupancy,
        "vacancy": prop.vacancy,
        "last_sale_date": str(prop.last_sale_date) if prop.last_sale_date else None,
        "last_sale_price": prop.last_sale_price,
        "owner_id": str(prop.owner_id) if prop.owner_id else None,
        "owner_name": prop.owner.display_name if prop.owner else None,
        "priority_score": prop.priority_score,
        "internal_notes": prop.internal_notes,
        "created_at": str(prop.created_at),
        "updated_at": str(prop.updated_at),
    }
    if detail:
        from datetime import date
        today = date.today()
        d["loans"] = [
            {
                "id": str(l.id),
                "display_name": l.display_name,
                "maturity_date": str(l.maturity_date) if l.maturity_date else None,
                "months_to_maturity": round((l.maturity_date - today).days / 30.44, 1) if l.maturity_date else None,
                "original_amount": l.original_amount,
                "lender": l.lender,
                "rate_type": l.rate_type,
                "io_flag": l.io_flag,
                "priority_score": l.priority_score,
            }
            for l in (prop.loans or [])
        ]
        d["aliases"] = [a.alias_name for a in (prop.aliases or [])]
    return d
