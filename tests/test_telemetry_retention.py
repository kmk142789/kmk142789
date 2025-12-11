from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import json

import pytest

from src.telemetry import ConsentState, TelemetryContext, TelemetryEvent
from src.telemetry.retention import (
    CONSENT_OPT_OUT_REASON,
    CONSENT_UNKNOWN_REASON,
    EXPIRED_REASON,
    RetentionPolicy,
    enforce_retention_policy,
    main,
)
from src.telemetry.storage import InMemoryTelemetryStorage, JsonlTelemetryStorage


REFERENCE_TIME = datetime(2024, 5, 1, tzinfo=timezone.utc)


def _make_context(*, consent: ConsentState) -> TelemetryContext:
    return TelemetryContext.pseudonymize(
        raw_identifier=f"user-{consent.value}",
        salt="test",
        consent_state=consent,
    )


def _make_event(offset: timedelta, *, consent: ConsentState) -> TelemetryEvent:
    context = _make_context(consent=consent)
    occurred_at = REFERENCE_TIME - offset
    return TelemetryEvent(
        event_type="heartbeat",
        occurred_at=occurred_at,
        context=context,
        payload={"step": "check"},
    )


def test_policy_removes_expired_events() -> None:
    recent = _make_event(timedelta(days=5), consent=ConsentState.OPTED_IN)
    expired = _make_event(timedelta(days=45), consent=ConsentState.OPTED_IN)
    policy = RetentionPolicy(max_event_age=timedelta(days=30))

    decision = policy.evaluate([recent, expired], reference_time=REFERENCE_TIME)

    assert decision.cutoff == REFERENCE_TIME - timedelta(days=30)
    assert decision.retained == (recent,)
    assert decision.removed_for_reason(EXPIRED_REASON) == (expired,)
    assert decision.removed_count == 1


def test_policy_rejects_opted_out_events_by_default() -> None:
    opted_out = _make_event(timedelta(days=1), consent=ConsentState.OPTED_OUT)
    policy = RetentionPolicy(max_event_age=timedelta(days=30))

    decision = policy.evaluate([opted_out], reference_time=REFERENCE_TIME)

    assert decision.retained_count == 0
    assert decision.removed_for_reason(CONSENT_OPT_OUT_REASON) == (opted_out,)


def test_policy_optionally_allows_opted_out_events() -> None:
    opted_out = _make_event(timedelta(days=1), consent=ConsentState.OPTED_OUT)
    policy = RetentionPolicy(max_event_age=timedelta(days=30), allow_opted_out_events=True)

    decision = policy.evaluate([opted_out], reference_time=REFERENCE_TIME)

    assert decision.retained == (opted_out,)
    assert decision.removed_count == 0


def test_unknown_consent_handling() -> None:
    unknown = _make_event(timedelta(days=1), consent=ConsentState.UNKNOWN)
    policy = RetentionPolicy(max_event_age=timedelta(days=30))

    decision = policy.evaluate([unknown], reference_time=REFERENCE_TIME)

    assert decision.removed_for_reason(CONSENT_UNKNOWN_REASON) == (unknown,)

    relaxed_policy = RetentionPolicy(
        max_event_age=timedelta(days=30), allow_unknown_consent=True
    )
    relaxed = relaxed_policy.evaluate([unknown], reference_time=REFERENCE_TIME)
    assert relaxed.retained == (unknown,)


def test_policy_with_unbounded_age_retains_all() -> None:
    events = [
        _make_event(timedelta(days=120), consent=ConsentState.OPTED_IN),
        _make_event(timedelta(days=2), consent=ConsentState.OPTED_IN),
    ]
    policy = RetentionPolicy(max_event_age=None)

    decision = policy.evaluate(events, reference_time=REFERENCE_TIME)

    assert decision.retained == tuple(events)
    assert decision.cutoff is None
    assert decision.removed_count == 0


def test_policy_requires_positive_duration() -> None:
    with pytest.raises(ValueError):
        RetentionPolicy(max_event_age=timedelta(seconds=0))
    with pytest.raises(ValueError):
        RetentionPolicy(max_event_age=timedelta(days=-1))


def test_removed_reason_counts() -> None:
    events = [
        _make_event(timedelta(days=45), consent=ConsentState.OPTED_IN),
        _make_event(timedelta(days=1), consent=ConsentState.UNKNOWN),
        _make_event(timedelta(days=1), consent=ConsentState.OPTED_OUT),
    ]
    policy = RetentionPolicy(max_event_age=timedelta(days=30))

    decision = policy.evaluate(events, reference_time=REFERENCE_TIME)

    assert decision.removed_reason_counts == {
        EXPIRED_REASON: 1,
        CONSENT_UNKNOWN_REASON: 1,
        CONSENT_OPT_OUT_REASON: 1,
    }


def test_enforce_retention_policy_in_memory_storage() -> None:
    storage = InMemoryTelemetryStorage()
    retained_event = _make_event(timedelta(days=1), consent=ConsentState.OPTED_IN)
    expired_event = _make_event(timedelta(days=60), consent=ConsentState.OPTED_IN)
    storage.write(retained_event)
    storage.write(expired_event)

    policy = RetentionPolicy(max_event_age=timedelta(days=30))
    decision = enforce_retention_policy(storage, policy, reference_time=REFERENCE_TIME)

    assert decision.retained == (retained_event,)
    assert storage.read() == [retained_event]


def test_enforce_retention_policy_jsonl_storage(tmp_path: Path) -> None:
    path = tmp_path / "telemetry.jsonl"
    storage = JsonlTelemetryStorage(path)
    kept = _make_event(timedelta(days=10), consent=ConsentState.OPTED_IN)
    opted_out = _make_event(timedelta(days=5), consent=ConsentState.OPTED_OUT)
    storage.write(kept)
    storage.write(opted_out)

    policy = RetentionPolicy(max_event_age=timedelta(days=30))
    decision = enforce_retention_policy(storage, policy, reference_time=REFERENCE_TIME)

    assert decision.retained == (kept,)
    assert storage.read() == [kept]


def test_retention_decision_serialisation() -> None:
    recent = _make_event(timedelta(days=5), consent=ConsentState.OPTED_IN)
    expired = _make_event(timedelta(days=45), consent=ConsentState.OPTED_IN)
    unknown = _make_event(timedelta(days=1), consent=ConsentState.UNKNOWN)

    policy = RetentionPolicy(max_event_age=timedelta(days=30))
    decision = policy.evaluate(
        [recent, expired, unknown], reference_time=REFERENCE_TIME
    )

    snapshot = decision.as_dict()
    assert snapshot["retained_count"] == 1
    assert snapshot["removed_reason_counts"] == {
        EXPIRED_REASON: 1,
        CONSENT_UNKNOWN_REASON: 1,
    }
    assert snapshot["cutoff"] is not None

    summary = decision.describe()
    assert "Retained events: 1" in summary
    assert "Removal breakdown" in summary


def test_retention_cli_dry_run(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "telemetry.jsonl"
    storage = JsonlTelemetryStorage(path)
    context = _make_context(consent=ConsentState.OPTED_IN)
    recent = TelemetryEvent(
        event_type="heartbeat",
        occurred_at=datetime.now(timezone.utc) - timedelta(days=1),
        context=context,
        payload={"step": "check"},
    )
    expired = TelemetryEvent(
        event_type="heartbeat",
        occurred_at=datetime.now(timezone.utc) - timedelta(days=40),
        context=context,
        payload={"step": "check"},
    )
    storage.write(recent)
    storage.write(expired)

    exit_code = main([str(path), "--dry-run", "--json", "--max-age-days", "30"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["retained_count"] == 1
    assert payload["removed_count"] == 1
    # Dry run must not mutate the log
    assert len(list(storage.read())) == 2
