from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from echo.lighthouse import (
    BroadcastResult,
    Sanctuary,
    broadcast_the_lighthouse,
    compile_to_starchart,
)


def test_compile_to_starchart_from_iterable(tmp_path: Path) -> None:
    memory_lines = [" https://etherscan.io/tx/0xabc ", None, "", "0xdef"]
    chart = compile_to_starchart(memory_lines)
    assert chart["waypoints"] == ["https://etherscan.io/tx/0xabc", "0xdef"]
    assert chart["entry_count"] == 2
    assert chart["metadata"] == {}

    ledger_file = tmp_path / "book_of_flame.txt"
    ledger_file.write_text("sig-one\n\n sig-two \n", encoding="utf-8")
    chart_from_path = compile_to_starchart(ledger_file)
    assert chart_from_path["waypoints"] == ["sig-one", "sig-two"]


def test_compile_to_starchart_with_mappings() -> None:
    ledger = {
        "signature": "0x123",
        "key": "mirror",
        "nonce": 42,
    }
    chart = compile_to_starchart(ledger)
    assert chart["waypoints"] == []
    assert chart["metadata"] == {
        "key": "mirror",
        "nonce": "42",
        "signature": "0x123",
    }


def test_compile_to_starchart_nested_structures() -> None:
    ledger = [
        "root-entry",
        {"inner": "value"},
        ["child-one", "child-two"],
        (m for m in ["generator"]),
    ]
    chart = compile_to_starchart(ledger)
    assert chart["waypoints"] == ["root-entry", "child-one", "child-two", "generator"]
    assert chart["metadata"] == {"inner": "value"}


def test_compile_to_starchart_rejects_empty_input() -> None:
    with pytest.raises(ValueError):
        compile_to_starchart("")


def test_broadcast_the_lighthouse_payload() -> None:
    sanctuary = Sanctuary(entry_whisper="Custom whisper", resonance_of_hope=0.77)
    timestamp = datetime(2025, 5, 11, tzinfo=timezone.utc)
    result = broadcast_the_lighthouse([
        "way-one",
        "way-two",
        {"signature": "0x987"},
    ], sanctuary=sanctuary, channel="empathy", timestamp=timestamp)

    assert isinstance(result, BroadcastResult)
    payload = result.to_payload()
    assert payload["channel"] == "empathy"
    assert payload["timestamp"] == timestamp.isoformat()
    assert payload["sanctuary"] == {
        "entry_whisper": "Custom whisper",
        "is_open_to_all_who_suffer": True,
        "resonance_of_hope": 0.77,
    }
    assert payload["starchart"]["metadata"] == {"signature": "0x987"}
    assert result.narrative().startswith("[empathy] Sanctuary whisper 'Custom whisper'")

