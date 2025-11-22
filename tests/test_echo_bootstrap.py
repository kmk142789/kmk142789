import pytest

from system_architecture.bootstrap.echo_bootstrap import (
    EchoBootstrap,
    StageResult,
)


def test_add_stage_rejects_duplicates() -> None:
    boot = EchoBootstrap()
    boot.add_stage("alpha", lambda: None)

    with pytest.raises(ValueError):
        boot.add_stage("alpha", lambda: None)


def test_run_collects_results_and_skips_disabled() -> None:
    boot = EchoBootstrap()

    observed: list[str] = []

    boot.add_stage("active", lambda: observed.append("active"))
    boot.add_stage("disabled", lambda: observed.append("disabled"), enabled=False)

    results = boot.run(halt_on_failure=False)

    assert observed == ["active"]
    assert len(results) == 2

    active = next(result for result in results if result.name == "active")
    disabled = next(result for result in results if result.name == "disabled")

    assert active.status == "ok"
    assert isinstance(active, StageResult)
    assert disabled.status == "skipped"
    assert disabled.duration_s == 0.0


def test_run_surfaces_failures_for_critical_stages() -> None:
    boot = EchoBootstrap()
    boot.add_stage("fail", lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    with pytest.raises(RuntimeError):
        boot.run()
