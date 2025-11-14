from __future__ import annotations

import json
from pathlib import Path

from scripts.verify_claims import validate_claim_file


def _build_claim_report() -> dict:
    return {
        "summary": {
            "claimant": "kmk142789",
            "generated_at": "2025-05-01T00:00:00+00:00",
            "count": 1,
            "window_phrase": "if not abandoned make a transaction within 90 days",
            "secondary_phrase": "Solomon bros",
        },
        "records": [
            {
                "txid": "ab" * 32,
                "block_time": "2025-05-01T00:00:00+00:00",
                "op_return_message": "if not abandoned make a transaction within 90 days",
                "clause_detected": True,
                "clause_variant": "solomon_bros_window",
                "inactivity_window_days": 90,
                "inactivity_window_end": "2025-07-30T00:00:00+00:00",
                "derived_entities": [
                    {
                        "index": 1,
                        "script_type": "p2pkh",
                        "address": "1EchoExample",
                        "raw_script": "76a914ffffffffffffffffffffffffffffffffffffffff88ac",
                        "value_sats": 125000,
                    }
                ],
                "recommendation": "requires_claim_review",
                "verification_notes": ["Pending ownership confirmation"],
            }
        ],
        "review_checklist": [
            "Confirm OP_RETURN payload matches evidence.",
            "Validate inactivity window calculations.",
        ],
    }


def test_validate_claim_file_accepts_valid_report(tmp_path: Path):
    report = _build_claim_report()
    target = tmp_path / "claim.json"
    target.write_text(json.dumps(report), encoding="utf-8")

    assert validate_claim_file(target) == []


def test_validate_claim_file_detects_summary_mismatch(tmp_path: Path):
    report = _build_claim_report()
    report["summary"]["count"] = 2
    target = tmp_path / "bad_claim.json"
    target.write_text(json.dumps(report), encoding="utf-8")

    issues = validate_claim_file(target)
    assert any("summary.count" in issue.message for issue in issues)
