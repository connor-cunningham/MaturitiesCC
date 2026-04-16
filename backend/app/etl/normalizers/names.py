import re
import unicodedata

# Legal entity suffixes to strip when creating comparison keys
_STRIP_SUFFIXES = re.compile(
    r"\b(llc|lp|ltd|inc|corp|co|company|group|management|capital|realty|"
    r"properties|property|investments|investment|holdings|fund|partners|"
    r"partner|associates|associate|advisors|advisor|enterprises|enterprise|"
    r"real estate|realestate)\b",
    re.IGNORECASE,
)
_WHITESPACE = re.compile(r"\s+")
_NON_ALNUM = re.compile(r"[^a-z0-9\s]")


def normalize_owner_name(name: str) -> str:
    """Return a stable comparison key for owner/company name matching."""
    if not name:
        return ""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = s.lower()
    s = _NON_ALNUM.sub(" ", s)
    s = _STRIP_SUFFIXES.sub(" ", s)
    s = _WHITESPACE.sub(" ", s).strip()
    return s


def normalize_property_name(name: str) -> str:
    """Lightweight normalization for property name matching."""
    if not name:
        return ""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = _WHITESPACE.sub(" ", s).strip()
    return s
