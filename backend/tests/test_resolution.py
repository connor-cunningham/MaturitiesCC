import pytest
from app.etl.normalizers.names import normalize_owner_name


def test_owner_normalize_similar_names_match():
    """Names that differ only by suffix should produce similar keys for fuzzy matching."""
    from rapidfuzz.fuzz import WRatio
    a = normalize_owner_name("Greystar Real Estate Partners LLC")
    b = normalize_owner_name("Greystar Real Estate Partners")
    score = WRatio(a, b)
    assert score >= 90, f"Expected high similarity, got {score}"


def test_owner_normalize_different_companies():
    from rapidfuzz.fuzz import WRatio
    a = normalize_owner_name("Greystar Real Estate Partners LLC")
    b = normalize_owner_name("Aimco Apartment Income REIT")
    score = WRatio(a, b)
    assert score < 60, f"Expected low similarity, got {score}"


def test_owner_name_abbreviation_variants():
    """Common abbreviation variants should score highly."""
    from rapidfuzz.fuzz import WRatio
    a = normalize_owner_name("ABC Apartments LLC")
    b = normalize_owner_name("ABC Apts LLC")
    # After normalization both become 'abc apartments' and 'abc apts' — should still score well
    score = WRatio(a, b)
    assert score >= 70


def test_property_name_normalization():
    from app.etl.normalizers.names import normalize_property_name
    a = normalize_property_name("The Monarch @ Midtown")
    b = normalize_property_name("Monarch at Midtown")
    from rapidfuzz.fuzz import WRatio
    score = WRatio(a, b)
    assert score >= 80


def test_address_confidence_same():
    from app.etl.normalizers.address import normalize_address, address_match_confidence
    a = normalize_address("1200 Peachtree Street NE", "Atlanta", "GA", "30309")
    b = normalize_address("1200 Peachtree St NE", "Atlanta", "GA", "30309")
    conf = address_match_confidence(a, b)
    assert conf >= 0.85


def test_address_confidence_different_cities():
    from app.etl.normalizers.address import normalize_address, address_match_confidence
    a = normalize_address("100 Main St", "Chicago", "IL", "60601")
    b = normalize_address("100 Main St", "Houston", "TX", "77001")
    conf = address_match_confidence(a, b)
    assert conf < 0.80
