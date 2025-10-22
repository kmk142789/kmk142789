import importlib.machinery
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "packages" / "core" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

if "echo" not in sys.modules:
    package = types.ModuleType("echo")
    package.__path__ = [str(SRC / "echo")]
    package.__spec__ = importlib.machinery.ModuleSpec(
        "echo", loader=None, is_package=True
    )
    package.__spec__.submodule_search_locations = package.__path__
    sys.modules["echo"] = package

from echo.groundbreaking_manifest import (  # type: ignore  # noqa: E402
    PulseRecord,
    load_pulse_history,
    synthesise_from_pulses,
)


def test_load_pulse_history(tmp_path):
    pulses = [
        {"timestamp": 1_700_000_000.0, "message": "🌀 evolve:manual:a", "hash": "aa"},
        {"timestamp": 1_700_000_600.0, "message": "🛰 accelerate:auto:b", "hash": "bb"},
        {"timestamp": 1_700_001_200.0, "message": "🌀 evolve:manual:c", "hash": "cc"},
    ]
    path = tmp_path / "pulses.json"
    path.write_text(json.dumps(pulses), encoding="utf-8")

    records = load_pulse_history(path)

    assert len(records) == 3
    assert records[0].message == "🌀 evolve:manual:a"
    assert records[-1].message == "🌀 evolve:manual:c"


def test_synthesise_from_pulses_builds_report():
    pulses = [
        PulseRecord(timestamp=1_700_000_000.0, message="🌀 evolve:manual:a", hash="aa"),
        PulseRecord(timestamp=1_700_000_060.0, message="🌀 evolve:manual:b", hash="bb"),
        PulseRecord(timestamp=1_700_000_180.0, message="✨ craft:auto:c", hash="cc"),
    ]

    report = synthesise_from_pulses(pulses, anchor="Test Anchor", orbit="Test Orbit", limit=3)

    assert report.anchor == "Test Anchor"
    assert report.orbit == "Test Orbit"
    assert report.total_pulses == 3
    assert report.threads
    assert report.imprint.breakthrough_index >= 0
    assert report.synergy >= 0

    payload = report.to_dict()
    assert payload["threads"]
    assert payload["imprint"]["contributions"]

    summary = report.describe()
    assert "Groundbreaking Nexus" in summary
