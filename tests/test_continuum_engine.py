from datetime import datetime, timedelta, timezone

import pytest

from echo.continuum_engine import ContinuumEngine


@pytest.fixture()
def continuum_times():
    base = datetime(2045, 1, 1, 12, 0, tzinfo=timezone.utc)

    def _next() -> datetime:
        nonlocal base
        current = base
        base = base + timedelta(seconds=1)
        return current

    return _next


def test_manifest_is_deterministic_across_order(continuum_times):
    engine = ContinuumEngine(time_source=continuum_times)
    engine.record(
        "Eden88",
        "ignite the continuum",
        tags=["eden88", "bridge", "eden88"],
        weight=1.5,
        meta={"phase": 1},
    )
    engine.record(
        "MirrorJosh",
        "anchor the broadcast",
        tags=["bridge", "anchor"],
        weight=1.0,
        meta={"priority": "high"},
    )

    manifest = engine.manifest()
    duplicate = engine.manifest()

    assert manifest is duplicate  # cache reused
    assert manifest.entry_count == 2
    assert manifest.cumulative_weight == pytest.approx(2.5)
    assert manifest.tag_index["anchor"]["count"] == 1
    assert manifest.tag_index["anchor"]["weight"] == pytest.approx(1.0)
    assert manifest.tag_index["bridge"]["count"] == 2
    assert manifest.tag_index["bridge"]["weight"] == pytest.approx(2.5)
    assert manifest.tag_index["eden88"]["count"] == 1
    assert manifest.tag_index["eden88"]["weight"] == pytest.approx(1.5)
    assert manifest.source_index["Eden88"]["count"] == 1
    assert manifest.source_index["Eden88"]["weight"] == pytest.approx(1.5)
    assert manifest.source_index["MirrorJosh"]["count"] == 1
    assert manifest.source_index["MirrorJosh"]["weight"] == pytest.approx(1.0)

    first_entry, second_entry = manifest.entries
    assert first_entry["tags"] == ["bridge", "eden88"]
    assert second_entry["tags"] == ["anchor", "bridge"]
    assert first_entry["meta"] == {"phase": 1}
    assert second_entry["meta"] == {"priority": "high"}


def test_manifest_digest_matches_when_entry_order_differs():
    anchor = "Our Forever Love"
    baseline = datetime(2046, 7, 4, 11, 0, tzinfo=timezone.utc)
    moments = [baseline + timedelta(minutes=index) for index in range(3)]

    entries = [
        {
            "source": "Eden88",
            "message": "ignite",
            "tags": ["bridge", "eden88"],
            "weight": 1.25,
        },
        {
            "source": "EchoWildfire",
            "message": "fan the flames",
            "tags": ["wildfire", "bridge"],
            "weight": 0.75,
        },
        {
            "source": "MirrorJosh",
            "message": "hold the anchor",
            "tags": ["anchor", "bridge"],
            "weight": 1.0,
        },
    ]

    engine_a = ContinuumEngine(anchor=anchor)
    for payload, moment in zip(entries, moments):
        engine_a.record(moment=moment, **payload)

    engine_b = ContinuumEngine(anchor=anchor)
    for payload, moment in zip(reversed(entries), reversed(moments)):
        shuffled_tags = list(reversed(payload["tags"]))
        engine_b.record(moment=moment, **{**payload, "tags": shuffled_tags})

    manifest_a = engine_a.manifest()
    manifest_b = engine_b.manifest()

    assert manifest_a.digest == manifest_b.digest
    assert manifest_a.to_dict() == manifest_b.to_dict()
    assert manifest_a.entries == manifest_b.entries


def test_playback_filters_entries_by_tag_and_source(continuum_times):
    engine = ContinuumEngine(time_source=continuum_times)
    engine.record("Eden88", "ignite", tags=["eden88", "bridge"], weight=1.0)
    engine.record("EchoWildfire", "pulse", tags=["wildfire", "bridge"], weight=0.5)
    engine.record("MirrorJosh", "anchor", tags=["anchor"], weight=0.75)

    playback = engine.replay()
    bridge_entries = playback.filter(tag="bridge")
    assert len(bridge_entries) == 2
    assert {entry["source"] for entry in bridge_entries} == {"Eden88", "EchoWildfire"}

    mirror_entries = playback.filter(source="MirrorJosh")
    assert len(mirror_entries) == 1
    assert mirror_entries[0]["message"] == "anchor"

    summary = playback.summary()
    assert summary["anchor"] == "Our Forever Love"
    assert summary["entry_count"] == 3
    assert summary["tags"]["bridge"] == 2
    assert summary["sources"]["Eden88"] == 1
    assert summary["digest"] == engine.manifest_signature()
