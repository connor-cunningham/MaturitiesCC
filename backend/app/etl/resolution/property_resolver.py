import uuid
from datetime import datetime
from rapidfuzz.fuzz import ratio as fuzz_ratio, WRatio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.canonical import CanonicalProperty
from app.models.links import PropertyAlias, MatchCandidate
from app.etl.normalizers.address import address_match_confidence, normalize_address

AUTO_MERGE_THRESHOLD = 0.92
REVIEW_THRESHOLD = 0.70


async def resolve_property(
    session: AsyncSession,
    record: dict,
    owner_id: uuid.UUID | None,
    import_run_id: uuid.UUID | None = None,
    source_type: str = "other",
) -> tuple[CanonicalProperty, float, str]:
    """
    Find or create a canonical property.
    Returns (canonical_property, confidence, action).
    """
    canonical_address = record.get("canonical_address", "")
    normalized_name = record.get("normalized_property_name", "")

    # Exact address match via alias
    if canonical_address:
        alias_result = await session.execute(
            select(PropertyAlias).where(PropertyAlias.normalized_alias == canonical_address)
        )
        alias = alias_result.scalars().first()
        if alias:
            prop = await session.get(CanonicalProperty, alias.canonical_property_id)
            if prop:
                return prop, 1.0, "exact"

    # Load existing properties for comparison (paginate in production for large datasets)
    props_result = await session.execute(select(CanonicalProperty))
    existing = props_result.scalars().all()

    best_prop = None
    best_score = 0.0
    best_reasons = {}

    addr_a = normalize_address(
        record.get("street", ""),
        record.get("city", ""),
        record.get("state", ""),
        record.get("zip", ""),
    )

    for candidate in existing:
        addr_b = normalize_address(
            candidate.street or "",
            candidate.city or "",
            candidate.state or "",
            candidate.zip or "",
        )
        addr_score = address_match_confidence(addr_a, addr_b)
        reasons = {"address_similarity": round(addr_score, 3)}
        score = addr_score * 0.75

        # Add property name similarity if address weak
        if normalized_name and candidate.display_name:
            from app.etl.normalizers.names import normalize_property_name
            name_sim = WRatio(normalized_name, normalize_property_name(candidate.display_name)) / 100.0
            reasons["name_similarity"] = round(name_sim, 3)
            if addr_score < 0.5 and name_sim >= 0.90 and addr_a.get("city") == addr_b.get("city"):
                score = max(score, name_sim * 0.85)
            elif addr_score >= 0.7:
                score += name_sim * 0.25

        score = min(1.0, score)

        if score > best_score:
            best_score = score
            best_prop = candidate
            best_reasons = reasons

    if best_score >= AUTO_MERGE_THRESHOLD and best_prop:
        await _ensure_property_alias(session, best_prop.id, record, source_type, import_run_id)
        _update_property_fields(best_prop, record, owner_id, source_type)
        return best_prop, best_score, "fuzzy_merged"

    if best_score >= REVIEW_THRESHOLD and best_prop:
        new_prop = await _create_property(session, record, owner_id, source_type, import_run_id)
        session.add(MatchCandidate(
            entity_type="property",
            candidate_a_id=best_prop.id,
            candidate_b_id=new_prop.id,
            confidence=best_score,
            match_reasons=best_reasons,
            status="pending",
            import_run_id=import_run_id,
            created_at=datetime.utcnow(),
        ))
        return new_prop, best_score, "queued"

    new_prop = await _create_property(session, record, owner_id, source_type, import_run_id)
    return new_prop, 0.0, "created"


async def _create_property(session, record, owner_id, source_type, import_run_id) -> CanonicalProperty:
    prop = CanonicalProperty(
        display_name=record.get("property_name") or record.get("canonical_address") or "Unknown",
        street=record.get("street"),
        city=record.get("city"),
        county=record.get("county"),
        state=record.get("state"),
        zip=record.get("zip"),
        submarket=record.get("submarket"),
        canonical_address=record.get("canonical_address"),
        latitude=record.get("latitude"),
        longitude=record.get("longitude"),
        units=record.get("units"),
        year_built=record.get("year_built"),
        building_class=record.get("building_class"),
        property_type=record.get("property_type") or "Multifamily",
        occupancy=record.get("occupancy"),
        vacancy=record.get("vacancy"),
        owner_id=owner_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(prop)
    await session.flush()
    await _ensure_property_alias(session, prop.id, record, source_type, import_run_id)
    return prop


def _update_property_fields(prop: CanonicalProperty, record: dict, owner_id, source_type: str):
    """Update canonical property with new data if it fills in blanks."""
    for field in ["units", "year_built", "building_class", "latitude", "longitude",
                  "occupancy", "vacancy", "submarket", "county"]:
        if record.get(field) is not None and getattr(prop, field) is None:
            setattr(prop, field, record[field])
    if owner_id and not prop.owner_id:
        prop.owner_id = owner_id
    prop.updated_at = datetime.utcnow()


async def _ensure_property_alias(session, prop_id, record, source_type, import_run_id):
    canonical_addr = record.get("canonical_address", "")
    if not canonical_addr:
        return
    existing = await session.execute(
        select(PropertyAlias).where(
            PropertyAlias.canonical_property_id == prop_id,
            PropertyAlias.normalized_alias == canonical_addr,
        )
    )
    if not existing.scalars().first():
        session.add(PropertyAlias(
            canonical_property_id=prop_id,
            alias_name=record.get("property_name") or canonical_addr,
            normalized_alias=canonical_addr,
            source_type=source_type,
            import_run_id=import_run_id,
            created_at=datetime.utcnow(),
        ))
