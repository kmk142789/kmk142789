from __future__ import annotations

import argparse
import json

import pytest

from tools.verify_satoshi_34k_dataset import (
    DatasetEntry,
    export_importmulti,
    parse_timestamp_option,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("now", "now"),
        ("NOW", "now"),
        ("  now  ", "now"),
        ("0", 0),
        ("1234567890", 1234567890),
    ],
)
def test_parse_timestamp_option_accepts_expected_values(value: str, expected):
    assert parse_timestamp_option(value) == expected


@pytest.mark.parametrize("value", ["", "yesterday", "-1", "1.5"])
def test_parse_timestamp_option_rejects_invalid(value: str):
    with pytest.raises(argparse.ArgumentTypeError):
        parse_timestamp_option(value)  # type: ignore[arg-type]


def test_export_importmulti_structure(tmp_path):
    entries = [
        DatasetEntry(
            "04" + "11" * 64,
            "1BoatSLRHtKNngkdXEeobR76b53LETtpyT",
        ),
        DatasetEntry(
            "04" + "22" * 64,
            "1QLbz7JHiBTspS962RLKV8GndWFwi5j6Qr",
        ),
    ]
    output = tmp_path / "import.json"

    export_importmulti(entries, output, label_prefix="demo", timestamp=1700000000)

    data = json.loads(output.read_text())
    assert len(data) == 2
    assert data[0]["scriptPubKey"]["address"] == entries[0].address
    assert data[0]["pubkeys"] == [entries[0].public_key_hex]
    assert data[0]["label"] == "demo-0001"
    assert data[0]["timestamp"] == 1700000000
    assert data[0]["watchonly"] is True
    assert data[1]["label"] == "demo-0002"
