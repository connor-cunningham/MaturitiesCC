from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.core.database import get_db
from app.models.canonical import CanonicalLoan, CanonicalProperty, CanonicalOwner

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def global_search(q: str = Query(..., min_length=2), db: AsyncSession = Depends(get_db)):
    pattern = f"%{q}%"
    limit = 5

    loans = await db.execute(
        select(CanonicalLoan).where(
            or_(
                CanonicalLoan.display_name.ilike(pattern),
                CanonicalLoan.lender.ilike(pattern),
                CanonicalLoan.originator.ilike(pattern),
                CanonicalLoan.servicer.ilike(pattern),
            )
        ).limit(limit)
    )

    properties = await db.execute(
        select(CanonicalProperty).where(
            or_(
                CanonicalProperty.display_name.ilike(pattern),
                CanonicalProperty.street.ilike(pattern),
                CanonicalProperty.city.ilike(pattern),
            )
        ).limit(limit)
    )

    owners = await db.execute(
        select(CanonicalOwner).where(
            CanonicalOwner.display_name.ilike(pattern)
        ).limit(limit)
    )

    return {
        "loans": [
            {"id": str(l.id), "label": l.display_name or l.lender or str(l.id),
             "maturity_date": str(l.maturity_date) if l.maturity_date else None,
             "type": "loan"}
            for l in loans.scalars().all()
        ],
        "properties": [
            {"id": str(p.id), "label": p.display_name,
             "city": p.city, "state": p.state, "type": "property"}
            for p in properties.scalars().all()
        ],
        "owners": [
            {"id": str(o.id), "label": o.display_name, "type": "owner"}
            for o in owners.scalars().all()
        ],
    }
