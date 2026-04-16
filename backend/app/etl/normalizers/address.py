import re
import unicodedata

# Common street type abbreviation expansions
_STREET_ABBR = {
    "st": "street", "ave": "avenue", "blvd": "boulevard", "dr": "drive",
    "rd": "road", "ct": "court", "pl": "place", "ln": "lane",
    "way": "way", "hwy": "highway", "pkwy": "parkway", "cir": "circle",
    "ter": "terrace", "trl": "trail",
}
# Direction abbreviations
_DIR_ABBR = {"n": "north", "s": "south", "e": "east", "w": "west",
             "ne": "northeast", "nw": "northwest", "se": "southeast", "sw": "southwest"}

_WHITESPACE = re.compile(r"\s+")


def _ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def normalize_address(street: str, city: str = "", state: str = "", zip_code: str = "") -> dict:
    """
    Returns a dict of normalized address components plus a canonical_address string.
    Used for property deduplication.
    """
    result = {
        "street": _normalize_street(street or ""),
        "city": (city or "").strip().lower(),
        "state": (state or "").strip().upper()[:2],
        "zip": _normalize_zip(zip_code or ""),
    }
    parts = [p for p in [result["street"], result["city"], result["state"], result["zip"]] if p]
    result["canonical_address"] = ", ".join(parts)
    return result


def _normalize_street(street: str) -> str:
    if not street:
        return ""
    s = _ascii(street).lower()
    s = re.sub(r"[^\w\s]", " ", s)
    tokens = _WHITESPACE.sub(" ", s).strip().split()
    expanded = []
    for t in tokens:
        t_lower = t.lower()
        if t_lower in _STREET_ABBR:
            expanded.append(_STREET_ABBR[t_lower])
        elif t_lower in _DIR_ABBR:
            expanded.append(_DIR_ABBR[t_lower])
        else:
            expanded.append(t_lower)
    return " ".join(expanded)


def _normalize_zip(zip_code: str) -> str:
    digits = re.sub(r"\D", "", zip_code)
    return digits[:5] if digits else ""


def address_match_confidence(a: dict, b: dict) -> float:
    """
    Score two normalized address dicts for similarity.
    Returns 0.0-1.0.
    """
    if not a.get("street") or not b.get("street"):
        return 0.0

    # Exact full canonical address
    if a["canonical_address"] and a["canonical_address"] == b["canonical_address"]:
        return 1.0

    score = 0.0
    weights = 0.0

    # Street similarity
    from rapidfuzz.fuzz import ratio
    street_sim = ratio(a["street"], b["street"]) / 100.0
    score += street_sim * 0.6
    weights += 0.6

    # City match
    if a["city"] and b["city"]:
        city_match = 1.0 if a["city"] == b["city"] else 0.0
        score += city_match * 0.25
        weights += 0.25

    # State match
    if a["state"] and b["state"]:
        state_match = 1.0 if a["state"] == b["state"] else 0.0
        score += state_match * 0.1
        weights += 0.1

    # Zip match
    if a["zip"] and b["zip"]:
        zip_match = 1.0 if a["zip"] == b["zip"] else 0.0
        score += zip_match * 0.05
        weights += 0.05

    return score / weights if weights > 0 else 0.0
