"""
Rules-based opportunity scoring engine.
Scores are computed per loan and rolled up to property/owner.
All factor weights come from the active ScoreConfig in the DB.
"""
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.canonical import CanonicalLoan, CanonicalProperty, CanonicalOwner
from app.models.scoring import ScoreConfig, ScoreResult, DEFAULT_FACTOR_WEIGHTS
import uuid


# --- Factor scoring functions (each returns 0-100) ---

def score_months_to_maturity(maturity_date: date | None) -> float:
    if not maturity_date:
        return 0.0
    today = date.today()
    months = (maturity_date - today).days / 30.44
    if months < 0:
        return 5.0  # already matured
    if months < 6:
        return 100.0
    if months < 12:
        return 85.0
    if months < 18:
        return 70.0
    if months < 24:
        return 55.0
    if months < 36:
        return 35.0
    return 10.0


def score_loan_amount(amount: float | None) -> float:
    if not amount:
        return 0.0
    if amount >= 50_000_000:
        return 100.0
    if amount >= 20_000_000:
        return 80.0
    if amount >= 10_000_000:
        return 60.0
    if amount >= 5_000_000:
        return 40.0
    return 20.0


def score_rate_type(rate_type: str | None) -> float:
    if not rate_type:
        return 20.0
    rt = rate_type.lower()
    if "float" in rt or "sofr" in rt or "libor" in rt or "arm" in rt:
        return 100.0
    if "variable" in rt or "adjust" in rt:
        return 75.0
    return 20.0


def score_io_flag(io_flag: bool | None) -> float:
    if io_flag is True:
        return 100.0
    return 20.0


def score_portfolio_concentration(concentration_count: int) -> float:
    if concentration_count >= 3:
        return 100.0
    if concentration_count == 2:
        return 60.0
    return 20.0


def score_building_class(building_class: str | None) -> float:
    if not building_class:
        return 40.0
    bc = building_class.upper()
    if bc.startswith("C"):
        return 80.0
    if bc.startswith("B"):
        return 50.0
    if bc.startswith("A"):
        return 30.0
    return 40.0


def score_outreach_status(outreach_stage: str | None) -> float:
    stage_map = {
        "cold": 80.0,
        "identified": 75.0,
        "researched": 65.0,
        "outreach_sent": 50.0,
        "contacted": 30.0,
        "meeting_scheduled": 20.0,
        "active": 15.0,
        "warm": 100.0,
        "closed": 5.0,
        "pass": 0.0,
        "do_not_contact": 0.0,
    }
    return stage_map.get((outreach_stage or "cold").lower(), 50.0)


def score_market_tier(state: str | None, city: str | None) -> float:
    primary_states = {"NY", "CA", "TX", "FL", "IL", "WA"}
    primary_cities = {"new york", "los angeles", "chicago", "houston", "miami",
                      "dallas", "san francisco", "seattle", "boston", "denver"}
    if city and city.lower() in primary_cities:
        return 80.0
    if state and state.upper() in primary_states:
        return 60.0
    return 40.0


def compute_loan_score(
    loan: CanonicalLoan,
    owner_maturity_count: int,
    weights: dict,
    outreach_stage: str | None = None,
    state: str | None = None,
    city: str | None = None,
) -> tuple[float, dict]:
    """
    Returns (total_score 0-100, factor_breakdown).
    """
    w = {**DEFAULT_FACTOR_WEIGHTS, **weights}

    factors = {
        "months_to_maturity": score_months_to_maturity(loan.maturity_date),
        "loan_amount": score_loan_amount(loan.original_amount or loan.current_balance),
        "rate_type": score_rate_type(loan.rate_type),
        "io_flag": score_io_flag(loan.io_flag),
        "portfolio_concentration": score_portfolio_concentration(owner_maturity_count),
        "building_class": score_building_class(loan.property.building_class if loan.property else None),
        "outreach_status": score_outreach_status(outreach_stage),
        "market_tier": score_market_tier(state, city),
    }

    total = sum(factors[k] * w.get(k, 0) for k in factors)
    weight_sum = sum(w.get(k, 0) for k in factors)
    normalized = (total / weight_sum) if weight_sum > 0 else 0.0

    return round(normalized, 2), factors


async def get_active_config(session: AsyncSession) -> ScoreConfig:
    result = await session.execute(
        select(ScoreConfig).where(ScoreConfig.is_active == True).order_by(ScoreConfig.created_at.desc())
    )
    config = result.scalars().first()
    if not config:
        config = ScoreConfig(
            name="Default",
            description="Default scoring configuration",
            factor_weights=DEFAULT_FACTOR_WEIGHTS,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(config)
        await session.flush()
    return config


async def run_scoring(session: AsyncSession) -> int:
    """
    (Re)compute scores for all active canonical loans.
    Updates canonical_loans.priority_score and inserts score_results.
    Returns count of loans scored.
    """
    config = await get_active_config(session)
    weights = config.factor_weights or DEFAULT_FACTOR_WEIGHTS

    # Count maturities per owner (within next 36 months) for portfolio concentration
    today = date.today()
    from datetime import timedelta
    cutoff = date(today.year + 3, today.month, today.day)

    loans_result = await session.execute(
        select(CanonicalLoan).where(
            CanonicalLoan.status == "active",
            CanonicalLoan.maturity_date.isnot(None),
        )
    )
    loans = loans_result.scalars().all()

    # Build per-owner count
    owner_counts: dict[uuid.UUID, int] = {}
    for loan in loans:
        if loan.owner_id and loan.maturity_date and loan.maturity_date <= cutoff:
            owner_counts[loan.owner_id] = owner_counts.get(loan.owner_id, 0) + 1

    scored = 0
    for loan in loans:
        owner_count = owner_counts.get(loan.owner_id, 1) if loan.owner_id else 1
        state = loan.property.state if loan.property else None
        city = loan.property.city if loan.property else None
        outreach_stage = loan.owner.outreach_stage if loan.owner else None

        total_score, factors = compute_loan_score(
            loan, owner_count, weights, outreach_stage, state, city
        )

        loan.priority_score = total_score

        result = ScoreResult(
            entity_type="loan",
            entity_id=loan.id,
            config_id=config.id,
            total_score=total_score,
            factor_scores=factors,
            computed_at=datetime.utcnow(),
        )
        session.add(result)
        scored += 1

    # Roll up to owner level (average of their loans)
    owners_result = await session.execute(select(CanonicalOwner))
    owners = owners_result.scalars().all()
    for owner in owners:
        if owner.loans:
            scores = [l.priority_score for l in owner.loans if l.priority_score is not None]
            if scores:
                owner.priority_score = round(max(scores), 2)  # use max loan score for owner

    await session.commit()
    return scored
