import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.canonical import CanonicalLoan
from app.models.links import LoanSourceMapping
from app.etl.normalizers.fields import higher_precedence, SOURCE_PRECEDENCE

AUTO_MERGE_THRESHOLD = 0.90


async def resolve_loan(
    session: AsyncSession,
    record: dict,
    property_id: uuid.UUID | None,
    owner_id: uuid.UUID | None,
    raw_loan_id: uuid.UUID,
    import_run_id: uuid.UUID | None,
    source_type: str,
) -> tuple[CanonicalLoan, float, str]:
    """
    Find or create canonical loan. Returns (loan, confidence, action).
    Strategy: match by (property_id + maturity_date + amount proximity).
    """
    maturity_date = record.get("maturity_date")
    original_amount = record.get("original_amount")

    # If we have a property, look for loans on the same property
    if property_id and maturity_date:
        loans_result = await session.execute(
            select(CanonicalLoan).where(CanonicalLoan.property_id == property_id)
        )
        candidates = loans_result.scalars().all()

        for candidate in candidates:
            score, reasons = _score_loan_match(candidate, maturity_date, original_amount)
            if score >= AUTO_MERGE_THRESHOLD:
                _merge_loan_fields(candidate, record, source_type)
                await session.flush()
                await _add_source_mapping(session, candidate.id, raw_loan_id, source_type, record)
                return candidate, score, "merged"

    # Create new
    loan = await _create_loan(session, record, property_id, owner_id, source_type)
    await _add_source_mapping(session, loan.id, raw_loan_id, source_type, record)
    return loan, 0.0, "created"


def _score_loan_match(candidate: CanonicalLoan, maturity_date, original_amount) -> tuple[float, dict]:
    score = 0.0
    reasons = {}

    if not candidate.maturity_date or not maturity_date:
        return 0.0, reasons

    days_diff = abs((candidate.maturity_date - maturity_date).days)
    if days_diff == 0:
        score += 0.6
        reasons["maturity_exact"] = True
    elif days_diff <= 30:
        score += 0.5
        reasons["maturity_diff_days"] = days_diff
    elif days_diff <= 90:
        score += 0.3
        reasons["maturity_diff_days"] = days_diff
    else:
        return 0.0, reasons

    if original_amount and candidate.original_amount:
        pct_diff = abs(original_amount - candidate.original_amount) / max(candidate.original_amount, 1)
        if pct_diff <= 0.02:
            score += 0.4
            reasons["amount_match"] = True
        elif pct_diff <= 0.10:
            score += 0.25
            reasons["amount_pct_diff"] = round(pct_diff, 3)
        elif pct_diff <= 0.20:
            score += 0.10
    else:
        score += 0.20  # no amount to compare, give partial credit

    return min(1.0, score), reasons


def _merge_loan_fields(loan: CanonicalLoan, record: dict, source_type: str):
    """Update canonical loan fields respecting source precedence."""
    current_prec = SOURCE_PRECEDENCE.get(loan.source_precedence or "", -1)
    incoming_prec = SOURCE_PRECEDENCE.get(source_type, 0)

    provenance = loan.provenance or {}

    for field in ["lender", "originator", "servicer", "rate_type", "coupon",
                  "io_flag", "amortization", "term", "loan_type", "recourse",
                  "prepay_structure", "current_balance", "original_amount"]:
        incoming_val = record.get(field)
        if incoming_val is None:
            continue
        existing_val = getattr(loan, field)
        existing_field_prec = SOURCE_PRECEDENCE.get(provenance.get(field, ""), -1)
        if existing_val is None or incoming_prec > existing_field_prec:
            setattr(loan, field, incoming_val)
            provenance[field] = source_type

    loan.provenance = provenance
    if incoming_prec > current_prec:
        loan.source_precedence = source_type
    loan.updated_at = datetime.utcnow()


async def _create_loan(session, record, property_id, owner_id, source_type) -> CanonicalLoan:
    loan = CanonicalLoan(
        property_id=property_id,
        owner_id=owner_id,
        lender=record.get("lender"),
        originator=record.get("originator"),
        servicer=record.get("servicer"),
        origination_date=record.get("origination_date"),
        maturity_date=record.get("maturity_date"),
        original_amount=record.get("original_amount"),
        current_balance=record.get("current_balance"),
        rate_type=record.get("rate_type"),
        coupon=record.get("coupon"),
        io_flag=record.get("io_flag"),
        amortization=record.get("amortization"),
        term=record.get("term"),
        loan_type=record.get("loan_type"),
        recourse=record.get("recourse"),
        prepay_structure=record.get("prepay_structure"),
        status="active",
        source_precedence=source_type,
        provenance={
            f: source_type
            for f in ["lender", "originator", "servicer", "rate_type", "coupon",
                      "io_flag", "amortization", "term", "loan_type", "maturity_date",
                      "original_amount", "current_balance"]
            if record.get(f) is not None
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    prop_name = record.get("property_name", "")
    city = record.get("city", "")
    if prop_name:
        loan.display_name = f"{prop_name}{' - ' + city if city else ''}"
    session.add(loan)
    await session.flush()
    return loan


async def _add_source_mapping(session, loan_id, raw_loan_id, source_type, record):
    mapping = LoanSourceMapping(
        canonical_loan_id=loan_id,
        raw_loan_record_id=raw_loan_id,
        source_type=source_type,
        field_provenance={
            f: source_type for f in record if record.get(f) is not None
        },
        created_at=datetime.utcnow(),
    )
    session.add(mapping)
