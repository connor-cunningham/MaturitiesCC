import pytest
from datetime import date
from app.scoring.engine import (
    score_months_to_maturity,
    score_loan_amount,
    score_rate_type,
    score_io_flag,
    score_portfolio_concentration,
    score_building_class,
    score_outreach_status,
    compute_loan_score,
)
from types import SimpleNamespace
from app.models.scoring import DEFAULT_FACTOR_WEIGHTS


def make_loan(**kwargs):
    """Create a lightweight mock loan — avoids SQLAlchemy mapper initialization."""
    loan = SimpleNamespace(
        id=None, property=None, owner=None,
        maturity_date=None, original_amount=None, current_balance=None,
        rate_type=None, io_flag=None,
    )
    for k, v in kwargs.items():
        setattr(loan, k, v)
    return loan


def test_months_to_maturity_immediate():
    d = date.today()
    assert score_months_to_maturity(d) == 100.0


def test_months_to_maturity_far():
    from datetime import timedelta
    d = date(date.today().year + 5, 1, 1)
    assert score_months_to_maturity(d) == 10.0


def test_months_to_maturity_none():
    assert score_months_to_maturity(None) == 0.0


def test_loan_amount_tiers():
    assert score_loan_amount(60_000_000) == 100.0
    assert score_loan_amount(25_000_000) == 80.0
    assert score_loan_amount(4_000_000) == 20.0
    assert score_loan_amount(None) == 0.0


def test_rate_type():
    assert score_rate_type("floating") == 100.0
    assert score_rate_type("SOFR + 100") == 100.0
    assert score_rate_type("fixed") == 20.0
    assert score_rate_type(None) == 20.0


def test_io_flag():
    assert score_io_flag(True) == 100.0
    assert score_io_flag(False) == 20.0
    assert score_io_flag(None) == 20.0


def test_portfolio_concentration():
    assert score_portfolio_concentration(3) == 100.0
    assert score_portfolio_concentration(2) == 60.0
    assert score_portfolio_concentration(1) == 20.0


def test_building_class():
    assert score_building_class("C") == 80.0
    assert score_building_class("B") == 50.0
    assert score_building_class("A") == 30.0


def test_outreach_status():
    assert score_outreach_status("cold") == 80.0
    assert score_outreach_status("warm") == 100.0
    assert score_outreach_status("do_not_contact") == 0.0


def test_compute_loan_score_high_priority():
    """A floating IO loan maturing soon with large balance should score high."""
    from datetime import timedelta
    loan = make_loan(
        maturity_date=date.today(),
        original_amount=50_000_000,
        rate_type="floating",
        io_flag=True,
    )
    total, factors = compute_loan_score(
        loan, owner_maturity_count=3, weights=DEFAULT_FACTOR_WEIGHTS,
        outreach_stage="cold", state="TX", city="houston"
    )
    assert total > 70.0
    assert "months_to_maturity" in factors


def test_compute_loan_score_low_priority():
    """A fixed, fully amortizing, far-future loan should score low."""
    loan = make_loan(
        maturity_date=date(date.today().year + 10, 1, 1),
        original_amount=2_000_000,
        rate_type="fixed",
        io_flag=False,
    )
    total, factors = compute_loan_score(
        loan, owner_maturity_count=1, weights=DEFAULT_FACTOR_WEIGHTS,
        outreach_stage="contacted", state="WY", city="cheyenne"
    )
    assert total < 40.0
