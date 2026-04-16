import re
from datetime import date
from dateutil import parser as dateutil_parser


def parse_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    try:
        return dateutil_parser.parse(str(value)).date()
    except Exception:
        return None


def parse_amount(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = re.sub(r"[$,\s]", "", str(value))
    # Handle millions shorthand: "12.5M" or "12.5m"
    m = re.match(r"^([\d.]+)[Mm]$", s)
    if m:
        return float(m.group(1)) * 1_000_000
    try:
        return float(s)
    except ValueError:
        return None


def normalize_rate_type(value: str | None) -> str | None:
    if not value:
        return None
    v = value.strip().lower()
    if any(x in v for x in ["float", "libor", "sofr", "variable", "arm", "adjustable"]):
        return "floating"
    if "fixed" in v:
        return "fixed"
    return value.strip()


def parse_bool_flag(value) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ("yes", "y", "true", "1", "x"):
        return True
    if s in ("no", "n", "false", "0", ""):
        return False
    return None


def normalize_building_class(value: str | None) -> str | None:
    if not value:
        return None
    v = value.strip().upper()
    if v in ("A", "A+", "AA"):
        return "A"
    if v in ("B", "B+", "B-"):
        return "B"
    if v in ("C", "C+", "C-"):
        return "C"
    if v in ("D",):
        return "D"
    return v[:5]


SOURCE_PRECEDENCE = {"internal": 3, "msci": 2, "costar": 1, "other": 0}


def higher_precedence(a: str | None, b: str | None) -> str | None:
    """Return the source type with higher precedence."""
    pa = SOURCE_PRECEDENCE.get(a or "", -1)
    pb = SOURCE_PRECEDENCE.get(b or "", -1)
    return a if pa >= pb else b
