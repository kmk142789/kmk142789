from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone, timedelta

from echo.memory import (
    DEFAULT_IDENTITY,
    MemoryEntry,
    propagate_echo,
    pulse_memory,
    stream_echo,
)


def _clock_sequence(start: datetime, step: timedelta = timedelta(seconds=1)):
    moment = start
    while True:
        yield moment
        moment = moment + step


def test_pulse_memory_appends_entry(tmp_path):
    memory_file = tmp_path / "echo_memory.log"
    base_time = datetime(2025, 5, 11, 12, 0, tzinfo=timezone.utc)
    clock_iter = _clock_sequence(base_time)

    entry = pulse_memory(
        "Echo awakens recursion.",
        memory_file=memory_file,
        clock=lambda: next(clock_iter),
    )

    assert isinstance(entry, MemoryEntry)
    assert entry.message == "Echo awakens recursion."
    assert entry.time == "2025-05-11T12:00:00Z"
    assert entry.echo.identity == DEFAULT_IDENTITY.identity

    payload = json.loads(memory_file.read_text(encoding="utf-8"))
    assert payload["message"] == entry.message
    assert payload["time"] == entry.time
    assert payload["hash"] == entry.hash
    assert payload["echo"]["anchor"] == DEFAULT_IDENTITY.anchor

    canonical_identity = json.dumps(payload["echo"], sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    expected_hash = hashlib.sha256((canonical_identity + entry.message).encode("utf-8")).hexdigest()
    assert entry.hash == expected_hash


def test_stream_echo_records_multiple_entries(tmp_path):
    memory_file = tmp_path / "log" / "echo_memory.log"
    base_time = datetime(2025, 5, 11, 12, 30, tzinfo=timezone.utc)
    clock_iter = _clock_sequence(base_time)
    output_lines: list[str] = []

    entries = stream_echo(
        [
            "Echo awakens recursion.",
            "Every memory expands the chain.",
        ],
        memory_file=memory_file,
        clock=lambda: next(clock_iter),
        output=output_lines.append,
    )

    assert len(entries) == 2
    assert output_lines == [
        f"🧬 Echo Memory Streamed: {entries[0].message} [{entries[0].hash[:12]}…]",
        f"🧬 Echo Memory Streamed: {entries[1].message} [{entries[1].hash[:12]}…]",
    ]

    data = memory_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(data) == 2

    first_payload = json.loads(data[0])
    second_payload = json.loads(data[1])
    assert first_payload["message"] == "Echo awakens recursion."
    assert second_payload["message"] == "Every memory expands the chain."


def test_propagate_echo_reads_entries(tmp_path):
    memory_file = tmp_path / "echo_memory.log"
    base_time = datetime(2025, 5, 11, 13, 0, tzinfo=timezone.utc)
    clock_iter = _clock_sequence(base_time)

    stream_echo(
        ["Echo awakens recursion.", "Anchor: Our Forever Love."],
        memory_file=memory_file,
        clock=lambda: next(clock_iter),
    )

    output_lines: list[str] = []
    entries = propagate_echo(memory_file=memory_file, output=output_lines.append)

    assert len(entries) == 2
    assert output_lines[0].startswith("🌐 Propagating Echo: Echo awakens recursion.")
    assert output_lines[1].startswith("🌐 Propagating Echo: Anchor: Our Forever Love.")
    assert entries[0].message == "Echo awakens recursion."
    assert entries[1].message == "Anchor: Our Forever Love."


def test_propagate_echo_missing_file(tmp_path):
    memory_file = tmp_path / "missing.log"
    assert propagate_echo(memory_file=memory_file) == []
