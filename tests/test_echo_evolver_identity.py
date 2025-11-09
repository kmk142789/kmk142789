import random

from echo.evolver import EchoEvolver


def test_identity_badge_defaults_recorded():
    evolver = EchoEvolver(rng=random.Random(0))

    badge = evolver.identity_badge()

    assert badge["entity"] == "SATOSHI_NAKAMOTO_515X"
    assert badge["anchor"] == "1105 Glenwood Ave, Port Huron, MI 48060"
    assert badge["parcel"] == "APN-88-MJ-418-22"
    assert "core_directive" in badge
    assert evolver.state.network_cache["identity_badge"] == badge
    assert evolver.state.event_log[-1].startswith(
        "Identity badge prepared for SATOSHI_NAKAMOTO_515X"
    )


def test_identity_badge_optional_directive():
    evolver = EchoEvolver(rng=random.Random(1))

    badge = evolver.identity_badge(include_directive=False)

    assert "core_directive" not in badge
    assert badge["entity"] == "SATOSHI_NAKAMOTO_515X"
    assert "identity_badge_compact" in evolver.state.network_cache
