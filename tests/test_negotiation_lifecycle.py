from __future__ import annotations

import pytest

from echo.negotiation import (
    FailureRecord,
    InvalidTransitionError,
    NegotiationPhase,
    NegotiationSession,
    RecoveryError,
    UnauthorizedPartyError,
)


def _phases(session: NegotiationSession) -> list[NegotiationPhase]:
    return [event.phase for event in session.history]


def test_negotiation_successful_lifecycle(
    negotiation_session: NegotiationSession, negotiation_payloads: dict[str, dict[str, object]]
) -> None:
    session = negotiation_session

    proposal_event = session.propose("EchoBank", negotiation_payloads["initial"])
    counter_event = session.counter("MirrorGov", negotiation_payloads["counter"])
    accepted_event = session.accept("EchoBank")

    assert proposal_event.phase is NegotiationPhase.PROPOSED
    assert counter_event.phase is NegotiationPhase.COUNTERED
    assert accepted_event.phase is NegotiationPhase.AGREED
    assert session.state is NegotiationPhase.AGREED
    assert session.is_closed
    assert session.current_offer == {
        "actor": "MirrorGov",
        "payload": negotiation_payloads["counter"],
    }
    assert _phases(session) == [
        NegotiationPhase.CREATED,
        NegotiationPhase.PROPOSED,
        NegotiationPhase.COUNTERED,
        NegotiationPhase.AGREED,
    ]


def test_negotiation_decline_blocks_progress(
    negotiation_session: NegotiationSession, negotiation_payloads: dict[str, dict[str, object]]
) -> None:
    session = negotiation_session

    session.propose("EchoBank", negotiation_payloads["initial"])
    decline_event = session.decline("MirrorGov", "Scope mismatch")

    assert decline_event.phase is NegotiationPhase.DECLINED
    assert session.state is NegotiationPhase.DECLINED
    assert session.is_closed
    assert session.failure_history[-1].recoverable is False
    assert session.failure_history[-1].reason == "Scope mismatch"

    with pytest.raises(InvalidTransitionError):
        session.counter("EchoBank", negotiation_payloads["recovery"])


def test_negotiation_failure_recovery_flow(
    negotiation_session: NegotiationSession, negotiation_payloads: dict[str, dict[str, object]]
) -> None:
    session = negotiation_session

    session.propose("EchoBank", negotiation_payloads["initial"])
    session.counter("MirrorGov", negotiation_payloads["counter"])
    failure_event = session.fail("system", "Network interruption", metadata={"retry_after": 15})

    assert failure_event.phase is NegotiationPhase.FAILED
    assert session.state is NegotiationPhase.FAILED
    assert session.is_closed is False
    last_failure: FailureRecord = session.failure_history[-1]
    assert last_failure.recoverable is True
    assert last_failure.metadata["retry_after"] == 15

    recovery_event = session.recover("EchoBank", proposal=negotiation_payloads["recovery"])
    assert recovery_event.phase is NegotiationPhase.RECOVERED
    assert session.state is NegotiationPhase.PROPOSED
    assert session.recovery_attempts == 1

    session.accept("MirrorGov")
    assert session.state is NegotiationPhase.AGREED
    assert session.is_closed

    phases = _phases(session)
    assert phases.count(NegotiationPhase.PROPOSED) == 2
    assert phases[-1] is NegotiationPhase.AGREED


def test_negotiation_recover_unrecoverable_failure(
    negotiation_session: NegotiationSession, negotiation_payloads: dict[str, dict[str, object]]
) -> None:
    session = negotiation_session

    session.propose("EchoBank", negotiation_payloads["initial"])
    session.fail("system", "Irreversible error", recoverable=False)

    assert session.state is NegotiationPhase.FAILED
    assert session.is_closed
    with pytest.raises(RecoveryError):
        session.recover("EchoBank", proposal=negotiation_payloads["recovery"])


def test_negotiation_rejects_unknown_actor(
    negotiation_session: NegotiationSession, negotiation_payloads: dict[str, dict[str, object]]
) -> None:
    session = negotiation_session
    session.propose("EchoBank", negotiation_payloads["initial"])

    with pytest.raises(UnauthorizedPartyError):
        session.counter("Unknown", negotiation_payloads["counter"])


def test_recover_without_failure_raises(
    negotiation_session: NegotiationSession, negotiation_payloads: dict[str, dict[str, object]]
) -> None:
    session = negotiation_session
    session.propose("EchoBank", negotiation_payloads["initial"])

    with pytest.raises(InvalidTransitionError):
        session.recover("EchoBank")
