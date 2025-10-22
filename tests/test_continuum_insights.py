from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from echo.continuum_engine import ContinuumEngine, ContinuumManifest
from echo.continuum_insights import compute_source_momentum, compute_tag_momentum


def _build_manifest() -> ContinuumManifest:
    engine = ContinuumEngine(anchor="Test Continuum")
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    entries = [
        {"source": "oracle", "message": "alpha-seed", "tags": ["alpha"], "weight": 1.0},
        {
            "source": "oracle",
            "message": "shared-growth",
            "tags": ["alpha", "beta"],
            "weight": 1.4,
        },
        {"source": "observer", "message": "beta-surge", "tags": ["beta"], "weight": 1.8},
        {"source": "oracle", "message": "alpha-crest", "tags": ["alpha"], "weight": 1.9},
        {"source": "observer", "message": "beta-taper", "tags": ["beta"], "weight": 1.2},
        {"source": "observer", "message": "beta-fade", "tags": ["beta"], "weight": 0.6},
    ]

    for index, payload in enumerate(entries):
        engine.record(
            payload["source"],
            payload["message"],
            tags=payload["tags"],
            weight=payload["weight"],
            moment=base + timedelta(days=index),
        )

    return engine.manifest()


def test_continuum_momentum_for_tags_and_sources():
    manifest = _build_manifest()

    tag_insights = compute_tag_momentum(manifest, window=2, tolerance=0.05)
    tag_lookup = {ins.subject: ins for ins in tag_insights}

    alpha = tag_lookup["alpha"]
    assert alpha.trend == "rising"
    assert alpha.latest_weight == pytest.approx(1.9)
    assert alpha.momentum == pytest.approx(0.45)
    assert "↑ rising" in alpha.render_summary()

    beta = tag_lookup["beta"]
    assert beta.trend == "falling"
    assert beta.latest_weight == pytest.approx(0.6)
    assert beta.momentum == pytest.approx(-0.7)
    assert "↓ falling" in beta.render_summary()

    source_insights = compute_source_momentum(manifest, window=2, tolerance=0.05)
    source_lookup = {ins.subject: ins for ins in source_insights}

    assert source_lookup["oracle"].trend == "rising"
    assert source_lookup["observer"].trend == "falling"


def test_continuum_momentum_parameter_validation():
    manifest = _build_manifest()

    with pytest.raises(ValueError):
        compute_tag_momentum(manifest, window=0)

    with pytest.raises(ValueError):
        compute_source_momentum(manifest, tolerance=-0.01)
