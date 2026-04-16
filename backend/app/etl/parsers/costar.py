import pandas as pd
from app.etl.parsers.base import BaseParser
from app.etl.normalizers import fields as F
from app.etl.normalizers.names import normalize_owner_name, normalize_property_name
from app.etl.normalizers.address import normalize_address


class CoStarParser(BaseParser):
    source_type = "costar"

    column_map = {
        "property_name":    ["Property Name", "Building Name", "Name"],
        "street":           ["Address", "Street Address", "Property Address"],
        "city":             ["City"],
        "state":            ["State", "State/Province"],
        "zip":              ["Zip", "Zip Code", "Postal Code"],
        "county":           ["County"],
        "submarket":        ["Submarket", "Submarket Name"],
        "units":            ["Units", "Number of Units", "Total Units", "# Units"],
        "year_built":       ["Year Built", "Yr Built"],
        "building_class":   ["Class", "Building Class", "Property Class"],
        "property_type":    ["Property Type", "Type"],
        "owner_name":       ["Owner", "Owner Name", "Current Owner"],
        "lender":           ["Lender", "Current Lender"],
        "originator":       ["Originator", "Loan Originator"],
        "servicer":         ["Servicer", "Loan Servicer"],
        "origination_date": ["Origination Date", "Loan Origination Date", "Start Date"],
        "maturity_date":    ["Maturity Date", "Loan Maturity Date"],
        "original_amount":  ["Loan Amount", "Original Loan Amount", "Original Balance"],
        "current_balance":  ["Current Balance", "Current Loan Balance", "Unpaid Balance"],
        "rate_type":        ["Rate Type", "Interest Rate Type"],
        "coupon":           ["Coupon", "Interest Rate", "Rate"],
        "io_flag":          ["IO", "Interest Only", "IO Flag", "Interest Only Flag"],
        "loan_type":        ["Loan Type", "Debt Type"],
        "recourse":         ["Recourse", "Recourse Flag"],
        "latitude":         ["Latitude", "Lat"],
        "longitude":        ["Longitude", "Long", "Lon"],
        "occupancy":        ["Occupancy", "Occupancy %", "Occ %"],
        "vacancy":          ["Vacancy", "Vacancy %"],
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
            "occupancy": F.parse_amount(get("occupancy")),
            "vacancy": F.parse_amount(get("vacancy")),
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
