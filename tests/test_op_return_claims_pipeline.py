import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from opreturn.claims import (
    ParsedClaim,
    parse_claim_records,
    validate_claim_windows,
    write_actionable_report,
)


@pytest.fixture(scope="module")
def sample_transactions_path() -> Path:
    return Path("tests/data/opreturn/sample_transactions.json")


@pytest.fixture(scope="module")
def expected_parsed_records() -> list[dict]:
    path = Path("tests/data/opreturn/expected_parsed_records.json")
    return json.loads(path.read_text(encoding="utf-8"))


def test_parse_claim_records_matches_fixture(sample_transactions_path, expected_parsed_records):
    with sample_transactions_path.open("r", encoding="utf-8") as handle:
        transactions = json.load(handle)

    parsed = parse_claim_records(transactions)
    assert len(parsed) >= 1_000
    assert [record.as_dict() for record in parsed] == expected_parsed_records


def test_validate_claim_windows_boundary_cases():
    block_time = datetime(2025, 5, 1, tzinfo=timezone.utc)
    base_record = ParsedClaim(
        txid="ff" * 32,
        vout=0,
        block_time=block_time,
        op_return_hex="6a0b536f6c6f6d6f6e2062726f73",
        op_return_text="Solomon bros",
    )

    as_of_valid = block_time + timedelta(days=90)
    as_of_pre = block_time + timedelta(days=89, hours=23)
    as_of_post = block_time + timedelta(days=91)

    valid_record = validate_claim_windows([base_record], as_of=as_of_pre)[0]
    assert valid_record.claim_status == "valid"
    assert "remaining" in valid_record.reason.lower()
    assert valid_record.next_step_suggestion in {"evidence verified", "action (not expired)"}

    boundary_record = validate_claim_windows([base_record], as_of=as_of_valid)[0]
    assert boundary_record.claim_status == "valid"

    expired_record = validate_claim_windows([base_record], as_of=as_of_post)[0]
    assert expired_record.claim_status == "expired"
    assert "expired" in expired_record.reason.lower()
    assert expired_record.next_step_suggestion == "escalate for allocation"


def test_classifier_assigns_fallback_when_no_marker():
    record = ParsedClaim(
        txid="00" * 32,
        vout=1,
        block_time=datetime(2025, 5, 1, tzinfo=timezone.utc),
        op_return_hex="6a044e4f5445",
        op_return_text="NOTE",
    )

    validated = validate_claim_windows([record], as_of=datetime(2025, 5, 2, tzinfo=timezone.utc))[0]
    assert validated.issuer_tag == "kmk142789"
    assert pytest.approx(validated.confidence, rel=0, abs=1e-6) == 0.4


def test_write_actionable_report_generates_json_and_csv(tmp_path: Path, sample_transactions_path):
    transactions = json.loads(sample_transactions_path.read_text(encoding="utf-8"))
    validated = validate_claim_windows(parse_claim_records(transactions), as_of=datetime(2025, 3, 20, tzinfo=timezone.utc))

    json_path = tmp_path / "claims.json"
    csv_path = tmp_path / "claims.csv"

    result = write_actionable_report(validated, json_path=json_path, csv_path=csv_path)

    assert json_path.exists() and csv_path.exists()
    assert result == {"json": str(json_path), "csv": str(csv_path)}

    json_payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert json_payload[0]["txid"].startswith("1111")
    assert json_payload[0]["claim_status"] in {"valid", "expired"}

    csv_lines = csv_path.read_text(encoding="utf-8").strip().splitlines()
    assert csv_lines[0].split(",") == [
        "txid",
        "block_time",
        "op_return_text",
        "claim_status",
        "issuer_tag",
        "next_step_suggestion",
    ]


def test_regression_fixture_remains_stable(tmp_path: Path):
    transactions = json.loads(Path("tests/data/opreturn/regression_transactions.json").read_text(encoding="utf-8"))
    expected = json.loads(Path("tests/data/opreturn/expected_regression_validated.json").read_text(encoding="utf-8"))

    validated = validate_claim_windows(
        parse_claim_records(transactions),
        as_of=datetime(2025, 6, 1, tzinfo=timezone.utc),
    )

    payload = [record.as_dict() for record in validated]
    assert payload == expected

    json_path = tmp_path / "regression.json"
    csv_path = tmp_path / "regression.csv"
    write_actionable_report(validated, json_path=json_path, csv_path=csv_path)

    assert json.loads(json_path.read_text(encoding="utf-8")) == expected
