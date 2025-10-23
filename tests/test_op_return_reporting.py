from datetime import datetime, timedelta, timezone

from opreturn.reporting import assemble_report, collect_claim_evidence


def _build_sample_transaction():
    message = "if not abandoned make a transaction within 90 days // contact Solomon bros"
    message_bytes = message.encode("utf-8")
    push_len = len(message_bytes)
    if push_len <= 75:
        push_prefix = bytes([push_len])
    else:
        push_prefix = bytes([0x4C, push_len])

    script = b"\x6a" + push_prefix + message_bytes
    op_return_hex = script.hex()

    # Example P2PKH script for the companion output
    companion_script = (
        "76a91489abcdef0123456789abcdef0123456789abcdef88ac"
    )

    return {
        "txid": "f6c9a0d5cafe00112233445566778899aabbccddeeff00112233445566778899",
        "block_time": datetime(2025, 6, 30, 15, 42, 16, tzinfo=timezone.utc),
        "vout": [
            {"n": 0, "script_hex": op_return_hex},
            {
                "n": 1,
                "script_hex": companion_script,
                "value_sats": 250_000,
            },
        ],
    }


def test_collect_claim_evidence_parses_clause():
    tx = _build_sample_transaction()
    as_of = tx["block_time"] + timedelta(days=95)

    evidence = collect_claim_evidence([tx], as_of=as_of)

    assert len(evidence) == 1
    record = evidence[0]

    assert record.txid == tx["txid"]
    assert record.clause_detected is True
    assert record.inactivity_window_days == 90
    assert record.inactivity_window_end == tx["block_time"] + timedelta(days=90)
    assert record.recommendation == "requires_claim_review"
    assert record.derived_entities[0].script_type == "p2pkh"
    assert record.derived_entities[0].address.startswith("1")


def test_assemble_report_serialises_records():
    tx = _build_sample_transaction()
    evidence = collect_claim_evidence([tx], as_of=tx["block_time"])

    report = assemble_report(
        claimant="kmk142789",
        generated_at=datetime(2025, 9, 29, 12, 0, tzinfo=timezone.utc),
        evidence=evidence,
    )

    assert report["summary"]["claimant"] == "kmk142789"
    assert report["summary"]["count"] == 1
    assert report["records"][0]["txid"] == tx["txid"]
    assert report["records"][0]["op_return_message"].startswith("if not abandoned")
    assert "Confirm OP_RETURN payload text matches archived evidence." in report[
        "review_checklist"
    ]

