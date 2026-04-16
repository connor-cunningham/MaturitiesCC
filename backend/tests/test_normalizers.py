import pytest
from app.etl.normalizers.names import normalize_owner_name, normalize_property_name
from app.etl.normalizers.address import normalize_address, address_match_confidence
from app.etl.normalizers.fields import parse_amount, parse_date, normalize_rate_type, parse_bool_flag


def test_normalize_owner_name_strips_suffixes():
    assert normalize_owner_name("ABC Properties LLC") == normalize_owner_name("ABC Properties")
    assert normalize_owner_name("ABC Capital Group Inc.") == normalize_owner_name("ABC Capital Group")


def test_normalize_owner_name_case_insensitive():
    assert normalize_owner_name("Greystar Real Estate") == normalize_owner_name("GREYSTAR REAL ESTATE")


def test_normalize_owner_name_handles_empty():
    assert normalize_owner_name("") == ""
    assert normalize_owner_name(None) == ""


def test_normalize_address_standardizes():
    result = normalize_address("1200 Peachtree St NE", "Atlanta", "GA", "30309")
    assert result["state"] == "GA"
    assert result["zip"] == "30309"
    assert "peachtree" in result["street"]


def test_address_match_exact():
    a = normalize_address("1200 Peachtree St NE", "Atlanta", "GA", "30309")
    b = normalize_address("1200 Peachtree St NE", "Atlanta", "GA", "30309")
    assert address_match_confidence(a, b) == 1.0


def test_address_match_different_addresses():
    a = normalize_address("100 Main St", "Denver", "CO", "80201")
    b = normalize_address("200 Oak Ave", "Dallas", "TX", "75201")
    conf = address_match_confidence(a, b)
    assert conf < 0.5


def test_parse_amount_currency():
    assert parse_amount("$1,500,000") == 1_500_000.0
    assert parse_amount("25.5M") == 25_500_000.0
    assert parse_amount(5_000_000) == 5_000_000.0


def test_parse_amount_none():
    assert parse_amount(None) is None
    assert parse_amount("") is None


def test_parse_date():
    from datetime import date
    assert parse_date("2026-07-01") == date(2026, 7, 1)
    assert parse_date("7/1/2026") == date(2026, 7, 1)
    assert parse_date(None) is None


def test_normalize_rate_type():
    assert normalize_rate_type("Floating Rate") == "floating"
    assert normalize_rate_type("SOFR + 200bps") == "floating"
    assert normalize_rate_type("Fixed") == "fixed"
    assert normalize_rate_type(None) is None


def test_parse_bool_flag():
    assert parse_bool_flag("Yes") is True
    assert parse_bool_flag("Y") is True
    assert parse_bool_flag("No") is False
    assert parse_bool_flag("") is False
    assert parse_bool_flag(None) is None
