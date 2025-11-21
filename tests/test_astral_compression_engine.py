import math

import pytest

from echo.astral_compression_engine import (
    AstralCompressionEngine,
    CompressionInstruction,
    ProbabilityField,
    compile_program,
)


def test_astral_engine_compresses_entropy():
    seed = ProbabilityField(
        label="astral",
        amplitudes={"signal": 0.25, "noise": 0.25, "hum": 0.25, "static": 0.25},
    )

    program = (
        CompressionInstruction("imprint", {"bias": {"signal": 1.0}, "weight": 0.35}),
        CompressionInstruction("compress", {"intensity": 1.5}),
        CompressionInstruction("interfere", {"coupling": 0.4}),
    )

    engine = AstralCompressionEngine()
    report = engine.execute(program, seed)

    assert pytest.approx(1.0, rel=1e-6) == sum(report.field.amplitudes.values())
    assert report.final_entropy < report.initial_entropy
    assert report.compression_ratio > 0
    assert len(report.trace) == len(program)


def test_compile_program_and_invariants():
    seed = ProbabilityField(label="astral", amplitudes={"a": 0.8, "b": 0.2})
    instructions = compile_program(
        [
            {"opcode": "imprint", "bias": {"a": 1.0, "b": 0.5}, "weight": 0.25},
            {"opcode": "compress", "intensity": 2.0},
            {"opcode": "renormalize"},
        ]
    )

    engine = AstralCompressionEngine()
    report = engine.execute(instructions, seed)

    assert math.isclose(report.invariants["probability_mass"], 1.0, rel_tol=1e-6)
    assert report.invariants["support"] == 2
    assert report.final_entropy <= report.initial_entropy
    assert report.trace[0].opcode == "imprint"
