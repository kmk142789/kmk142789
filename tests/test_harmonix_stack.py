"""Tests for the cognitive harmonix stack implementation."""

from cognitive_harmonics.harmonix_stack import (
    HarmonixOrchestrator,
    NetAddr,
    NoiseXX,
    PolicyActionType,
    PolicyInput,
    PolicyVM,
)


def test_policy_vm_numeric_and_route_actions() -> None:
    program = """
    when pairs < 4 then scale_out +2;
    when rtt_ms > 20 then route "alt";
    """
    vm = PolicyVM()
    ok, err = vm.load_text(program)
    assert ok, err

    inputs = PolicyInput(num={"pairs": 2, "rtt_ms": 30})
    actions = vm.eval(inputs)
    assert {action.type for action in actions} == {
        PolicyActionType.SCALE_OUT,
        PolicyActionType.ROUTE,
    }


def test_noise_xx_handshake_is_deterministic() -> None:
    handshake_a = NoiseXX("demo")
    msg1 = handshake_a.stage1()
    handshake_a.stage2(msg1)
    handshake_a.stage3()
    keys_a = handshake_a.keys()

    handshake_b = NoiseXX("demo")
    msg1b = handshake_b.stage1()
    handshake_b.stage2(msg1b)
    handshake_b.stage3()
    keys_b = handshake_b.keys()

    assert keys_a.rx == keys_b.rx
    assert keys_a.tx == keys_b.tx


def test_harmonix_orchestrator_payload_shape() -> None:
    orchestrator = HarmonixOrchestrator(
        mesh_bind=NetAddr("127.0.0.1", 7946),
        seeds=[NetAddr("127.0.0.1", 7947)],
        policy_text="when pairs < 3 then scale_out +1;",
    )
    orchestrator.ensure_route("primary", "10.0.0.5:9000", min_pairs=1)
    state, payload = orchestrator.run_cycle()

    assert payload["waveform"] == "complex_harmonic"
    metadata = payload["metadata"]
    assert metadata["cycle"] == state.cycle
    assert metadata["mesh_members"], "Mesh members should be listed"
    assert metadata["telemetry"]["pairs"] >= 1
    assert state.telemetry.bytes_up > 0
