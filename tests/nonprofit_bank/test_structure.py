from decimal import Decimal
from datetime import datetime

import pytest

from src.nonprofit_bank.structure import (
    NonprofitBankStructure,
    create_default_structure,
)


@pytest.fixture()
def structure():
    return create_default_structure()


def test_record_flow_and_snapshot(structure):
    entry = structure.record_flow(
        category="donation",
        amount="125.50",
        source="donor:alice",
        destination="Little Footsteps operations",
        label="general fund",
    )

    snapshot = structure.transparency_snapshot()

    assert snapshot == (entry,)
    assert entry.amount == Decimal("125.50")
    assert entry.destination.lower().startswith("little footsteps")
    assert isinstance(entry.timestamp, datetime)


def test_validate_reinvestment_flags_non_compliant_entries(structure):
    structure.record_flow(
        category="yield",
        amount=50,
        source="treasury",
        destination="Little Footsteps classroom fund",
        label="quarterly yield",
    )
    structure.record_flow(
        category="investment_return",
        amount=25,
        source="treasury",
        destination="Community partner grant",
        label="partner yield",
    )

    assert structure.validate_reinvestment() is False


def test_create_impact_token_generates_trace(structure):
    token = structure.create_impact_token(
        donor="alice",
        amount=10,
        deployment="snacks",
        investment_vehicle="Treasuries",
    )

    assert token.token_id.startswith("IMPACT-")
    assert token.amount == Decimal("10.00")
    assert list(token.path) == [
        "donor:alice",
        "investment:Treasuries",
        "destination:snacks",
    ]
    assert isinstance(token.issued_at, datetime)


def test_quarterly_report_calculates_cash_flow_and_roi(structure):
    report = structure.generate_quarterly_report(
        quarter="2024Q4",
        total_inflows=Decimal("1000"),
        investment_returns=Decimal("150"),
        operating_costs=Decimal("400"),
        kids_supported=42,
        meals_served=200,
        stands_operated=3,
    )

    assert report.roi == Decimal("0.1500")
    assert report.net_cash_flow == Decimal("750.00")
    assert report.financials["cash_on_hand"] == Decimal("750.00")
    assert "Little Footsteps" in report.narrative


def test_as_dict_serialises_key_sections(structure):
    payload = structure.as_dict()

    assert payload["core_design"]["nonprofit_inflows"]
    assert "public_ledger_dashboard" in payload["transparency"]
    assert "guaranteed_reinvestment" in payload["growth_model"]
    assert "impact_nfts" in payload["overkill_features"]
    assert "dashboard" in payload["core_design"]["transparency_layer"].lower()
