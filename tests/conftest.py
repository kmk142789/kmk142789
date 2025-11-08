from __future__ import annotations

import itertools
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, Tuple

import pytest

from echo.negotiation import NegotiationSession


@pytest.fixture
def negotiation_parties() -> Tuple[str, str]:
    return ("EchoBank", "MirrorGov")


@pytest.fixture
def fake_clock() -> Callable[[], datetime]:
    base = datetime(2025, 1, 1, tzinfo=timezone.utc)
    counter = itertools.count()

    def _tick() -> datetime:
        return base + timedelta(seconds=next(counter))

    return _tick


@pytest.fixture
def negotiation_session(
    negotiation_parties: Tuple[str, str], fake_clock: Callable[[], datetime]
) -> NegotiationSession:
    return NegotiationSession("session-test", negotiation_parties, clock=fake_clock)


@pytest.fixture
def negotiation_payloads() -> Dict[str, Dict[str, object]]:
    return {
        "initial": {"terms": "Initial offer", "amount": 42, "currency": "USD"},
        "counter": {"terms": "Counter proposal", "amount": 45, "currency": "USD"},
        "recovery": {"terms": "Recovered proposal", "amount": 44, "currency": "USD"},
    }
