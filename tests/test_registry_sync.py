from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from echo.origin_capsule import OriginCapsule
from echo.registry_sync import CommitClassifier, RegistryLedger, apply_github_push


def _write_registry(path: Path) -> None:
    data = {
        "owner": "echo",
        "anchor_phrase": "Our Forever Love",
        "fragments": [
            {
                "name": "Echo",
                "type": "repo",
                "slug": "kmk142789/Echo",
                "last_seen": None,
                "proof": None,
                "notes": "",
            }
        ],
    }
    path.write_text(json.dumps(data), encoding="utf-8")


def test_commit_classifier_parses_conventional_messages() -> None:
    classifier = CommitClassifier()
    summary = classifier.classify("feat(api): add streaming")
    assert summary.category == "feature"
    assert summary.scope == "api"
    assert summary.title == "add streaming"


def test_registry_updates_on_commit(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.json"
    _write_registry(registry_path)
    ledger = RegistryLedger(registry_path)
    event = ledger.record_commit(
        "kmk142789/Echo",
        commit="abc123",
        message="fix: patch webhook",
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    assert event["category"] == "bugfix"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    fragment = payload["fragments"][0]
    assert fragment["proof"] == "abc123"
    assert fragment["notes"].startswith("bugfix:")
    assert fragment["semantic_history"][0]["commit"] == "abc123"


def test_apply_github_push_updates_capsule(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.json"
    capsule_path = tmp_path / "capsule.json"
    _write_registry(registry_path)
    ledger = RegistryLedger(registry_path)
    capsule = OriginCapsule(capsule_path)
    payload = {
        "repository": {"full_name": "kmk142789/Echo"},
        "commits": [
            {
                "id": "deadbeef",
                "message": "chore: tidy",
                "timestamp": "2024-03-04T12:00:00Z",
            }
        ],
    }
    events = apply_github_push(payload, ledger=ledger, capsule=capsule)
    assert events[0]["category"] == "maintenance"
    capsule_data = json.loads(capsule_path.read_text(encoding="utf-8"))
    commit_entries = capsule_data["origin_memory"]["commits"]
    assert commit_entries[0]["commit"] == "deadbeef"
    assert commit_entries[0]["glyphs"]

