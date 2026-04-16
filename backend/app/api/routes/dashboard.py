from datetime import date, datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.core.database import get_db
from app.models.canonical import CanonicalLoan, CanonicalProperty, CanonicalOwner

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    today = date.today()

    # Totals
    total_loans = await db.scalar(select(func.count(CanonicalLoan.id)))
    total_properties = await db.scalar(select(func.count(CanonicalProperty.id)))
    total_owners = await db.scalar(select(func.count(CanonicalOwner.id)))

    # Total original balance
    total_balance = await db.scalar(
        select(func.sum(CanonicalLoan.original_amount)).where(CanonicalLoan.original_amount.isnot(None))
    )

    # Maturities by window
    windows = {
        "within_6mo": (today, _add_months(today, 6)),
        "within_12mo": (today, _add_months(today, 12)),
        "within_24mo": (today, _add_months(today, 24)),
        "within_36mo": (today, _add_months(today, 36)),
    }
    maturity_counts = {}
    maturity_volumes = {}
    for key, (start, end) in windows.items():
        count = await db.scalar(
            select(func.count(CanonicalLoan.id)).where(
                and_(CanonicalLoan.maturity_date >= start, CanonicalLoan.maturity_date <= end)
            )
        )
        volume = await db.scalar(
            select(func.sum(CanonicalLoan.original_amount)).where(
                and_(
                    CanonicalLoan.maturity_date >= start,
                    CanonicalLoan.maturity_date <= end,
                    CanonicalLoan.original_amount.isnot(None),
                )
            )
        )
        maturity_counts[key] = count or 0
        maturity_volumes[key] = float(volume or 0)

    # Maturity timeline by month (next 24 months)
    timeline = await _get_maturity_timeline(db, today)

    # Top owners by maturity volume
    top_owners = await _get_top_owners(db, today)

    # Top states
    top_states = await _get_top_states(db, today)

    # Top lenders
    top_lenders = await _get_top_lenders(db, today)

    return {
        "totals": {
            "loans": total_loans or 0,
            "properties": total_properties or 0,
            "owners": total_owners or 0,
            "original_balance": float(total_balance or 0),
        },
        "maturity_counts": maturity_counts,
        "maturity_volumes": maturity_volumes,
        "timeline": timeline,
        "top_owners": top_owners,
        "top_states": top_states,
        "top_lenders": top_lenders,
    }


async def _get_maturity_timeline(db, today):
    """Monthly maturity counts for next 24 months."""
    result = await db.execute(
        select(
            func.date_trunc("month", CanonicalLoan.maturity_date).label("month"),
            func.count(CanonicalLoan.id).label("count"),
            func.sum(CanonicalLoan.original_amount).label("volume"),
        )
        .where(
            and_(
                CanonicalLoan.maturity_date >= today,
                CanonicalLoan.maturity_date <= _add_months(today, 24),
            )
        )
        .group_by("month")
        .order_by("month")
    )
    return [
        {
            "month": str(row.month)[:7],
            "count": row.count,
            "volume": float(row.volume or 0),
        }
        for row in result
    ]


async def _get_top_owners(db, today):
    end = _add_months(today, 36)
    result = await db.execute(
        select(
            CanonicalOwner.id,
            CanonicalOwner.display_name,
            func.count(CanonicalLoan.id).label("loan_count"),
            func.sum(CanonicalLoan.original_amount).label("total_volume"),
        )
        .join(CanonicalLoan, CanonicalLoan.owner_id == CanonicalOwner.id)
        .where(
            and_(
                CanonicalLoan.maturity_date >= today,
                CanonicalLoan.maturity_date <= end,
            )
        )
        .group_by(CanonicalOwner.id, CanonicalOwner.display_name)
        .order_by(func.sum(CanonicalLoan.original_amount).desc())
        .limit(10)
    )
    return [
        {"id": str(r.id), "name": r.display_name, "loan_count": r.loan_count, "total_volume": float(r.total_volume or 0)}
        for r in result
    ]


async def _get_top_states(db, today):
    end = _add_months(today, 36)
    result = await db.execute(
        select(
            CanonicalProperty.state,
            func.count(CanonicalLoan.id).label("loan_count"),
            func.sum(CanonicalLoan.original_amount).label("total_volume"),
        )
        .join(CanonicalLoan, CanonicalLoan.property_id == CanonicalProperty.id)
        .where(
            and_(
                CanonicalLoan.maturity_date >= today,
                CanonicalLoan.maturity_date <= end,
                CanonicalProperty.state.isnot(None),
            )
        )
        .group_by(CanonicalProperty.state)
        .order_by(func.sum(CanonicalLoan.original_amount).desc())
        .limit(10)
    )
    return [
        {"state": r.state, "loan_count": r.loan_count, "total_volume": float(r.total_volume or 0)}
        for r in result
    ]


async def _get_top_lenders(db, today):
    end = _add_months(today, 36)
    result = await db.execute(
        select(
            CanonicalLoan.lender,
            func.count(CanonicalLoan.id).label("count"),
            func.sum(CanonicalLoan.original_amount).label("volume"),
        )
        .where(
            and_(
                CanonicalLoan.maturity_date >= today,
                CanonicalLoan.maturity_date <= end,
                CanonicalLoan.lender.isnot(None),
            )
        )
        .group_by(CanonicalLoan.lender)
        .order_by(func.sum(CanonicalLoan.original_amount).desc())
        .limit(10)
    )
    return [{"lender": r.lender, "count": r.count, "volume": float(r.volume or 0)} for r in result]


def _add_months(d: date, months: int) -> date:
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    return date(year, month, min(d.day, 28))
