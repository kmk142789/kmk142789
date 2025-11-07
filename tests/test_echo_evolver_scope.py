import pytest

from echo.evolver import EchoEvolver


def test_scope_matrix_summary_defaults():
    evolver = EchoEvolver()

    summary = evolver.scope_matrix_summary()

    assert summary["research"] == (
        "quantum ethics",
        "distributed law",
        "synthetic cognition",
    )
    assert summary["operations"] == (
        "self-audit",
        "data integrity",
        "cross-ledger verification",
    )
    assert summary["outreach"] == (
        "educational simulations",
        "open governance pilots",
    )

    cached = evolver.state.network_cache["scope_matrix"]
    assert cached == summary
    assert evolver.state.event_log[-1].startswith("Scope matrix harmonized")


def test_scope_matrix_summary_overrides_and_counts():
    evolver = EchoEvolver()

    summary = evolver.scope_matrix_summary(
        overrides={
            "operations": ["self-audit", "orbital sync", "self-audit"],
            "outreach": ("open governance pilots", "civic constellation"),
        },
        include_counts=True,
    )

    assert summary["operations"] == ("self-audit", "orbital sync")
    assert summary["outreach"] == (
        "open governance pilots",
        "civic constellation",
    )

    counts = evolver.state.network_cache["scope_matrix_counts"]
    assert counts == {"research": 3, "operations": 2, "outreach": 2}

    assert evolver.state.event_log[-2].startswith("Scope overrides applied")
    assert evolver.state.event_log[-1].startswith("Scope matrix harmonized")


def test_scope_matrix_summary_rejects_invalid_input():
    evolver = EchoEvolver()

    with pytest.raises(KeyError):
        evolver.scope_matrix_summary(overrides={"mythic": ["echo"]})

    with pytest.raises(ValueError):
        evolver.scope_matrix_summary(overrides={"research": [" ", None]})
