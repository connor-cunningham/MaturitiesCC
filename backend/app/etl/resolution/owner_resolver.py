import uuid
from datetime import datetime
from rapidfuzz.fuzz import WRatio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.canonical import CanonicalOwner
from app.models.links import OwnerAlias, MatchCandidate
from app.etl.normalizers.names import normalize_owner_name

AUTO_MERGE_THRESHOLD = 0.92
REVIEW_THRESHOLD = 0.70


async def resolve_owner(
    session: AsyncSession,
    normalized_name: str,
    display_name: str,
    city: str = "",
    state: str = "",
    import_run_id: uuid.UUID | None = None,
    source_type: str = "other",
) -> tuple[CanonicalOwner, float, str]:
    """
    Find or create a canonical owner for the given normalized name.
    Returns (canonical_owner, confidence, action) where action is:
      'exact' | 'fuzzy_merged' | 'queued' | 'created'
    """
    if not normalized_name:
        owner = await _create_owner(session, display_name, normalized_name, city, state, source_type)
        return owner, 0.0, "created"

    # Check existing aliases for exact match
    alias_result = await session.execute(
        select(OwnerAlias).where(OwnerAlias.normalized_alias == normalized_name)
    )
    alias = alias_result.scalars().first()
    if alias:
        owner = await session.get(CanonicalOwner, alias.canonical_owner_id)
        if owner:
            return owner, 1.0, "exact"

    # Load all existing owners for fuzzy comparison
    owners_result = await session.execute(select(CanonicalOwner))
    existing = owners_result.scalars().all()

    best_owner = None
    best_score = 0.0
    best_reasons = {}

    for candidate in existing:
        base = WRatio(normalized_name, candidate.normalized_name) / 100.0
        score = base
        reasons = {"name_similarity": round(base, 3)}

        if base >= 0.80:
            if city and candidate.hq_city and city.lower() == candidate.hq_city.lower():
                score = min(1.0, score + 0.10)
                reasons["city_match"] = True
            if state and candidate.hq_state and state.upper() == candidate.hq_state.upper():
                score = min(1.0, score + 0.05)
                reasons["state_match"] = True

        if score > best_score:
            best_score = score
            best_owner = candidate
            best_reasons = reasons

    if best_score >= AUTO_MERGE_THRESHOLD and best_owner:
        # Add alias if not already present
        await _ensure_alias(session, best_owner.id, display_name, normalized_name, source_type, import_run_id)
        return best_owner, best_score, "fuzzy_merged"

    if best_score >= REVIEW_THRESHOLD and best_owner:
        # Create new owner but queue the pair for manual review
        new_owner = await _create_owner(session, display_name, normalized_name, city, state, source_type)
        candidate_rec = MatchCandidate(
            entity_type="owner",
            candidate_a_id=best_owner.id,
            candidate_b_id=new_owner.id,
            confidence=best_score,
            match_reasons=best_reasons,
            status="pending",
            import_run_id=import_run_id,
            created_at=datetime.utcnow(),
        )
        session.add(candidate_rec)
        return new_owner, best_score, "queued"

    # No match — create fresh
    new_owner = await _create_owner(session, display_name, normalized_name, city, state, source_type)
    return new_owner, 0.0, "created"


async def _create_owner(session, display_name, normalized_name, city, state, source_type) -> CanonicalOwner:
    owner = CanonicalOwner(
        display_name=display_name or normalized_name,
        normalized_name=normalized_name,
        hq_city=city or None,
        hq_state=state.upper() if state else None,
        outreach_stage="cold",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(owner)
    await session.flush()
    await _ensure_alias(session, owner.id, display_name, normalized_name, source_type, None)
    return owner


async def _ensure_alias(session, owner_id, display_name, normalized_alias, source_type, import_run_id):
    existing = await session.execute(
        select(OwnerAlias).where(
            OwnerAlias.canonical_owner_id == owner_id,
            OwnerAlias.normalized_alias == normalized_alias,
        )
    )
    if not existing.scalars().first():
        alias = OwnerAlias(
            canonical_owner_id=owner_id,
            alias_name=display_name or normalized_alias,
            normalized_alias=normalized_alias,
            source_type=source_type,
            import_run_id=import_run_id,
            created_at=datetime.utcnow(),
        )
        session.add(alias)
