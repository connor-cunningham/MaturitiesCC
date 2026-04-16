import pytest
import pandas as pd
from io import StringIO
from unittest.mock import patch, MagicMock
from app.etl.parsers.costar import CoStarParser
from app.etl.parsers.internal import InternalParser


def make_costar_df():
    data = {
        "Property Name": ["The Grand Apartments"],
        "Address": ["1200 Main St"],
        "City": ["Austin"],
        "State": ["TX"],
        "Zip": ["78701"],
        "Units": ["250"],
        "Year Built": ["2018"],
        "Class": ["A"],
        "Owner": ["ABC Capital LLC"],
        "Lender": ["Goldman Sachs"],
        "Loan Amount": ["35000000"],
        "Maturity Date": ["2027-06-01"],
        "Rate Type": ["Floating"],
        "Coupon": ["5.75"],
        "IO": ["Yes"],
        "Origination Date": ["2022-06-01"],
    }
    return pd.DataFrame(data)


def test_costar_parser_transform_row():
    parser = CoStarParser()
    df = make_costar_df()
    record = parser.transform_row(df.iloc[0], df, None, 0)

    assert record is not None
    assert record["property_name"] == "The Grand Apartments"
    assert record["city"] == "austin"
    assert record["state"] == "TX"
    assert record["units"] == 250
    assert record["original_amount"] == 35_000_000.0
    assert record["rate_type"] == "floating"
    assert record["io_flag"] is True
    assert record["lender"] == "Goldman Sachs"
    assert record["normalized_owner_name"] != ""


def test_costar_parser_skips_empty_rows():
    parser = CoStarParser()
    df = pd.DataFrame({"Property Name": [None], "Address": [None]})
    record = parser.transform_row(df.iloc[0], df, None, 0)
    assert record is None


def test_internal_parser_transform_row():
    parser = InternalParser()
    data = {
        "Property": ["Harbor View"],
        "Address": ["500 Harbor Blvd"],
        "City": ["San Diego"],
        "State": ["CA"],
        "Zip": ["92101"],
        "Units": ["180"],
        "Borrower": ["Harbor Capital Group"],
        "Lender": ["Freddie Mac"],
        "Original Balance": ["22000000"],
        "Maturity Date": ["2028-03-01"],
        "Rate Type": ["Fixed"],
    }
    df = pd.DataFrame(data)
    record = parser.transform_row(df.iloc[0], df, None, 0)

    assert record is not None
    assert record["property_name"] == "Harbor View"
    assert record["original_amount"] == 22_000_000.0
    assert record["rate_type"] == "fixed"


def test_costar_parser_with_custom_mapping():
    parser = CoStarParser()
    df = pd.DataFrame({
        "Prop Name": ["Test Property"],
        "Addr": ["100 Test St"],
        "Cty": ["Denver"],
        "St": ["CO"],
        "ZipCode": ["80201"],
    })
    mapping = {
        "property_name": "Prop Name",
        "street": "Addr",
        "city": "Cty",
        "state": "St",
        "zip": "ZipCode",
    }
    record = parser.transform_row(df.iloc[0], df, mapping, 0)
    assert record is not None
    assert record["property_name"] == "Test Property"
    assert record["city"] == "denver"
