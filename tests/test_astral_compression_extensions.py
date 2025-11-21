import pytest

from src.astral_compression_engine import (
    ACEVisualizationLayer,
    ACELinkedAgent,
    AstralCompressionEngine,
    CompressionInstruction,
    CompressionRecursionLoop,
    GravityWellOptimizer,
    PFieldCompiler,
    ProbabilityField,
    QuantumNodeV2Bridge,
)


def test_pfield_compiler_outputs_instruction_sequence():
    compiler = PFieldCompiler()
    goal = "find the most stable signal path and suppress noise"
    program = compiler.compile_goal(goal)

    assert program[0].opcode == "imprint"
    assert any("signal" in program[0].parameters.get("bias", {}) for _ in range(1))
    assert any(instr.opcode == "compress" for instr in program)
    assert any(instr.opcode == "interfere" for instr in program)


def test_recursion_loop_converges_to_lower_entropy():
    seed = ProbabilityField(label="astral", amplitudes={"signal": 0.4, "noise": 0.3, "hum": 0.3})
    base_program = (
        CompressionInstruction("imprint", {"bias": {"signal": 1.0}, "weight": 0.25}),
        CompressionInstruction("compress", {"intensity": 0.6}),
        CompressionInstruction("interfere", {"coupling": 0.15}),
    )

    engine = AstralCompressionEngine()
    optimizer = GravityWellOptimizer(sweeps=2, intensity_step=0.5)
    loop = CompressionRecursionLoop(max_attempts=3, entropy_target=0.5, optimizer=optimizer)

    base_report = engine.execute(base_program, seed)
    improved_report = loop.converge(engine, seed, base_program)

    assert improved_report.final_entropy <= base_report.final_entropy
    assert improved_report.invariants["probability_mass"] == pytest.approx(1.0, rel=1e-6)


def test_agent_bridge_and_visualization():
    seed = ProbabilityField(label="astral", amplitudes={"signal": 0.6, "noise": 0.4})
    compiler = PFieldCompiler(default_weight=0.3)
    engine = AstralCompressionEngine()
    loop = CompressionRecursionLoop(max_attempts=2)
    bridge = QuantumNodeV2Bridge(modulation_strength=0.75)
    agent = ACELinkedAgent("scout", engine, compiler, loop, bridge)

    result = agent.act("stabilize and harmonize the signal", seed)
    report = result["report"]
    payload = result["bridge_payload"]

    assert payload is not None
    assert set(seed.amplitudes.keys()).issubset(set(payload["channels"].keys()))
    assert payload["entropy"] == report.final_entropy

    viz = ACEVisualizationLayer()
    text_output = viz.render_text(report)
    assert "Entropy trace" in text_output
    assert "Collapse pathway" in text_output
