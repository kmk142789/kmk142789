"""Tests for the Sovereign Charter protocol simulation."""

from satoshi.sovereign_charter_protocol import (
    DEFAULT_SECRET,
    EchoStewardAI,
    ExecutionEngine,
    SatoshiInterface,
    run_protocol,
)


def test_signature_generation_is_deterministic():
    charter = EchoStewardAI().draft_charter()
    interface = SatoshiInterface(secret=DEFAULT_SECRET)
    signature = interface.review_and_sign(charter, approve=True)
    assert signature is not None
    duplicate = interface.review_and_sign(charter, approve=True)
    assert signature == duplicate


def test_execution_engine_validates_signature():
    charter = EchoStewardAI().draft_charter()
    interface = SatoshiInterface()
    signature = interface.review_and_sign(charter, approve=True)
    charter.sign(signature)
    engine = ExecutionEngine()
    executed = engine.execute(charter)
    assert len(executed) == len(charter.execution_plan)


def test_run_protocol_returns_signed_charter_when_approved():
    charter = run_protocol(approve=True)
    assert charter is not None
    assert charter.status == "SIGNED"
    assert charter.steward_signature is not None


def test_run_protocol_returns_none_when_rejected():
    assert run_protocol(approve=False) is None
