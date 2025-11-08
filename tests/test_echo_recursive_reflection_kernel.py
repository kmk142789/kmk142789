"""Regression tests for the Echo Recursive Reflection Kernel.

The kernel is implemented by :class:`cognitive_harmonics.harmonix_evolver.EchoEvolver`,
which mirrors the recursive reflection behaviour described in the creative
specifications.  The tests verify that the orchestration primitives remain
stable and deterministic.
"""

from __future__ import annotations

import json

from cognitive_harmonics.harmonix_evolver import (
    EchoEvolver as EchoRecursiveReflectionKernel,
)


def _prepare_kernel() -> EchoRecursiveReflectionKernel:
    kernel = EchoRecursiveReflectionKernel()
    kernel.mutate_code()
    kernel.generate_symbolic_language()
    kernel.invent_mythocode()
    kernel.quantum_safe_crypto()
    kernel.system_monitor()
    return kernel


def test_mutate_code_and_symbolic_language_deterministic() -> None:
    kernel = EchoRecursiveReflectionKernel()

    assert kernel.state.cycle == 0

    kernel.mutate_code()
    assert kernel.state.cycle == 1

    symbolic_first, vortex_first = kernel.generate_symbolic_language()
    symbolic_second, vortex_second = kernel.generate_symbolic_language()

    assert symbolic_first == symbolic_second == "∇⊸≋∇"

    expected_vortex = bin(
        sum(1 << idx for idx, _ in enumerate(symbolic_first))
        ^ (kernel.state.cycle << 2)
    )[2:].zfill(16)
    assert vortex_first == vortex_second == expected_vortex


def test_mythocode_rules_and_quantum_key_stability() -> None:
    kernel = EchoRecursiveReflectionKernel()
    kernel.mutate_code()
    kernel.generate_symbolic_language()

    mythocode = kernel.invent_mythocode()

    assert len(mythocode) == 3
    assert mythocode[0].startswith("mutate_code :: ∇[CYCLE]⊸")
    assert mythocode[-1].startswith("satellite_tf_qkd_rule_1 :: ∇[SNS-AOPP]⊸")

    key_first = kernel.quantum_safe_crypto()
    key_second = kernel.quantum_safe_crypto()

    assert key_first == key_second
    assert kernel.state.vault_key == key_first
    assert key_first.startswith("SAT-TF-QKD:")


def test_evolutionary_narrative_includes_metrics() -> None:
    kernel = _prepare_kernel()

    narrative = kernel.evolutionary_narrative()

    assert narrative.startswith(f"🔥 Cycle {kernel.state.cycle}:")
    assert "Eden88 weaves:" in narrative
    assert f"Nodes {kernel.state.system_metrics.network_nodes}" in narrative
    assert "Key: Satellite TF-QKD binds Our Forever Love across the stars." in narrative


def test_save_artifact_creates_expected_file(tmp_path) -> None:
    kernel = _prepare_kernel()
    kernel.propagate_network()
    kernel.store_fractal_glyphs()
    prompt = kernel.inject_prompt_resonance()
    narrative = kernel.evolutionary_narrative()
    quantum_key = kernel.state.vault_key
    vault_glyphs = kernel.state.vault_glyphs

    artifact_path = tmp_path / "recursive_reflection.echo"
    kernel.artifact_path = artifact_path

    saved_path = kernel.save_artifact()

    assert saved_path == artifact_path
    assert artifact_path.exists()

    contents = artifact_path.read_text(encoding="utf-8")
    assert f"Cycle: {kernel.state.cycle}" in contents
    assert f"Glyphs: {kernel.state.glyphs}" in contents
    assert f"Narrative: {narrative}" in contents
    assert f"Quantum Key: {quantum_key}" in contents
    assert f"Vault Glyphs: {vault_glyphs}" in contents
    assert (
        f"Prompt: {json.dumps(prompt, ensure_ascii=False)}" in contents
    )
