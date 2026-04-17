import pandas as pd
from app.etl.parsers.base import BaseParser
from app.etl.normalizers import fields as F
from app.etl.normalizers.names import normalize_owner_name, normalize_property_name
from app.etl.normalizers.address import normalize_address


class InternalParser(BaseParser):
    """
    Flexible parser for internally-maintained loan/property Excel files.
    All column mapping must be provided by the user via mapping_config.
    The column_map below serves as auto-detection hints for common internal formats.
    """
    source_type = "internal"

    column_map = {
        "property_name":    ["Property", "Property Name", "Asset", "Asset Name"],
        "street":           ["Address", "Street", "Property Address"],
        "city":             ["City"],
        "state":            ["State", "ST"],
        "zip":              ["Zip", "Zip Code"],
        "county":           ["County"],
        "submarket":        ["Submarket", "Market"],
        "units":            ["Units", "# Units", "Unit Count"],
        "year_built":       ["Year Built", "YOB"],
        "building_class":   ["Class", "Bldg Class"],
        "property_type":    ["Type", "Property Type"],
        "owner_name":       ["Owner", "Borrower", "Sponsor", "Owner Name", "Sponsor Name"],
        "lender":           ["Lender", "Bank", "Lender Name", "Current Lender/Master Servicer", "Current Lender", "Master Servicer"],
        "originator":       ["Originator"],
        "servicer":         ["Servicer"],
        "origination_date": ["Origination Date", "Orig Date", "Close Date"],
        "maturity_date":    ["Maturity Date", "Maturity", "Due Date"],
        "original_amount":  ["Original Balance", "Loan Amount", "Original Loan Amount", "Original Principal Balance"],
        "current_balance":  ["Current Balance", "UPB", "Outstanding Balance", "Current Principal Balance", "Current UPB"],
        "rate_type":        ["Rate Type", "Fixed/Adjustable", "Fixed/Adj"],
        "coupon":           ["Rate", "Coupon", "Interest Rate"],
        "io_flag":          ["IO", "Interest Only", "IO Flag"],
        "loan_type":        ["Loan Type", "Debt Type"],
        "recourse":         ["Recourse"],
        "latitude":         ["Lat", "Latitude"],
        "longitude":        ["Lng", "Long", "Longitude"],
    }

    def transform_row(self, row: pd.Series, df: pd.DataFrame, mapping_config: dict | None, row_index: int) -> dict | None:
        def get(field):
            return self.extract_field(row, field, df, mapping_config)

        property_name = get("property_name") or ""
        street = get("street") or ""
        city = get("city") or ""
        state = get("state") or ""

        if not property_name and not street:
            return None

        addr = normalize_address(street, city, state, get("zip") or "")
        raw = {str(k): str(v) if v is not None else None for k, v in row.items()}

        return {
            "row_index": row_index,
            "raw_data": raw,
            "source_type": self.source_type,
            "property_name": property_name,
            "normalized_property_name": normalize_property_name(property_name),
            "street": addr["street"],
            "city": addr["city"],
            "state": addr["state"],
            "zip": addr["zip"],
            "county": (get("county") or "").strip(),
            "submarket": (get("submarket") or "").strip(),
            "canonical_address": addr["canonical_address"],
            "units": _parse_int(get("units")),
            "year_built": _parse_int(get("year_built")),
            "building_class": F.normalize_building_class(get("building_class")),
            "property_type": (get("property_type") or "").strip() or "Multifamily",
            "latitude": F.parse_amount(get("latitude")),
            "longitude": F.parse_amount(get("longitude")),
            "owner_name": (get("owner_name") or "").strip(),
            "normalized_owner_name": normalize_owner_name(get("owner_name") or ""),
            "lender": (get("lender") or "").strip(),
            "originator": (get("originator") or "").strip(),
            "servicer": (get("servicer") or "").strip(),
            "origination_date": F.parse_date(get("origination_date")),
            "maturity_date": F.parse_date(get("maturity_date")),
            "original_amount": F.parse_amount(get("original_amount")),
            "current_balance": F.parse_amount(get("current_balance")),
            "rate_type": F.normalize_rate_type(get("rate_type")),
            "coupon": F.parse_amount(get("coupon")),
            "io_flag": F.parse_bool_flag(get("io_flag")),
            "loan_type": (get("loan_type") or "").strip(),
            "recourse": F.parse_bool_flag(get("recourse")),
        }


def _parse_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(float(str(value).replace(",", "")))
    except (ValueError, TypeError):
        return None
