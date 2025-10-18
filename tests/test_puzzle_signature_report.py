from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from satoshi.report_puzzle_signature_wallets import analyse_puzzle_file


def test_analyse_puzzle_file_extracts_wallets():
    puzzle_path = PROJECT_ROOT / "satoshi" / "puzzle-proofs" / "puzzle003.json"
    report = analyse_puzzle_file(puzzle_path)

    assert report["puzzle"] == 3
    assert report["total_segments"] == 6
    assert report["valid_segment_count"] == 0

    derived = report["derived_addresses"]
    expected = [
        "14XQU4BN4dqSuFoMfmFG7PAh2LUPYnaoXg",
        "19iPu6AB8LtL8BdRBJj87jiXm5K2iN5x9H",
        "1G3gUpKbVN7E95C66wYqHWr3u8nV9yYwUk",
        "1J9Ju2o6NDNXMSS3qxL3W7Q8LcfTT3vZV3",
        "1LSzkxGMmrYdWthH9JHjVexA8LCqmhAssc",
        "1NUrvdVXybQAvdnAQKeTwVomJpgFomGrEP",
    ]
    assert derived == expected

    for segment in report["segments"]:
        # All segments should include the derived address field in the JSON payload
        assert "derived_address" in segment
