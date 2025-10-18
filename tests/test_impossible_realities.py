from decimal import Decimal
from fractions import Fraction

import pytest

from echo.impossible_realities import ImpossibleRealityEngine


def test_conjure_event_feels_impossible_but_is_real():
    engine = ImpossibleRealityEngine([Fraction(1, 3), 3.1415926535, Decimal("2.718281828")])
    event = engine.conjure("quantum love is archived in gold")

    assert "quantum love" in event.description
    assert event.evidence
    assert 0.0 < float(event.probability) < 1.0
    assert event.timestamp.tzinfo is not None

    report = event.evidence_report()
    assert report.startswith("p=")
    assert "Phenomenon: quantum love is archived in gold" in report


def test_manifest_batches_multiple_phenomena():
    engine = ImpossibleRealityEngine([Fraction(5, 7), 1.6180339887, Decimal("0.57721")])
    events = engine.manifest(["echo spiral", "mirror sunrise"])

    assert len(events) == 2
    assert events[0].description != events[1].description


def test_engine_requires_anchor_values():
    with pytest.raises(ValueError):
        ImpossibleRealityEngine([])


def test_invoke_allows_named_contextual_events():
    engine = ImpossibleRealityEngine([Fraction(2, 5), 0.5, Decimal("1.41421")])

    event = engine.invoke(
        "mirror sunrise",
        name="Impossible Invocation",
        context=["orbital mesh", "quantum braid"],
        seed="satellite-phase",
    )

    assert "Impossible Invocation" in event.description
    assert "mirror sunrise" in event.description
    assert 0.0 < float(event.probability) < 1.0

    report = event.evidence_report()
    assert "Context[1]: orbital mesh" in report
    assert "Context[2]: quantum braid" in report
