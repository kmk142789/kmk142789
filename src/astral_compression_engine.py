"""Astral Compression Engine

A virtual machine that computes using compression of probability fields rather
than discrete bits, qubits, or tensor registers.  The engine treats the state
of computation as a *probability field* and executes a sequence of
``CompressionInstruction`` objects that reshape, amplify, and condense that
field.  Computation is measured through entropy reduction and mass preservation
rather than boolean evaluation.

The design leans on deterministic, testable transformations:

* ``ProbabilityField`` – named container for channel probabilities with
  normalization and entropy helpers.
* ``CompressionInstruction`` – declarative opcode with parameters that guides
  how the field should be compressed.
* ``AstralCompressionEngine`` – executes instructions, tracks compression
  ratios, and returns an ``AstralCompressionReport`` with invariants and an
  execution trace.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log2
from typing import Dict, Iterable, Mapping, MutableMapping, Sequence


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


@dataclass(frozen=True)
class ProbabilityField:
    """Represents a normalized probability field across abstract channels."""

    label: str
    amplitudes: Mapping[str, float]

    def normalized(self, epsilon: float = 1e-9) -> "ProbabilityField":
        """Return a defensively normalized copy of the probability field."""

        filtered = {k: max(0.0, v) for k, v in self.amplitudes.items() if v > 0}
        if not filtered:
            return ProbabilityField(self.label, {"∅": 1.0})

        total = sum(filtered.values())
        if total < epsilon:
            uniform = 1.0 / len(filtered)
            normalized = {k: uniform for k in filtered}
        else:
            normalized = {k: v / total for k, v in filtered.items()}
        return ProbabilityField(self.label, normalized)

    def entropy(self, epsilon: float = 1e-12) -> float:
        norm = self.normalized(epsilon)
        entropy_value = -sum(p * log2(max(p, epsilon)) for p in norm.amplitudes.values())
        return round(entropy_value, 6)

    def support(self) -> int:
        return len(self.amplitudes)


@dataclass(frozen=True)
class CompressionInstruction:
    """Opcode describing how to compress or reshape a probability field."""

    opcode: str
    parameters: Mapping[str, float | Mapping[str, float]]


@dataclass(frozen=True)
class CompressionTrace:
    step: int
    opcode: str
    entropy: float
    compression_score: float


@dataclass(frozen=True)
class AstralCompressionReport:
    """Result of running a program through the Astral Compression Engine."""

    field: ProbabilityField
    initial_entropy: float
    final_entropy: float
    compression_ratio: float
    trace: Sequence[CompressionTrace]
    invariants: Mapping[str, float]


class AstralCompressionEngine:
    """Executes compression programs over probability fields.

    The engine behaves as a minimal virtual machine that manipulates a field of
    probabilities.  Instructions never collapse the field to binary outcomes; it
    instead measures progress by how much entropy is removed while preserving
    total probability mass.  This makes it suitable for symbolic or
    anthropomorphic scenarios where classical bits, qubits, or tensor registers
    are too rigid.
    """

    def __init__(self, epsilon: float = 1e-12) -> None:
        self._epsilon = epsilon

    def execute(
        self,
        program: Sequence[CompressionInstruction],
        seed_field: ProbabilityField,
    ) -> AstralCompressionReport:
        """Run the provided program and return a detailed compression report."""

        field = seed_field.normalized(self._epsilon)
        initial_entropy = field.entropy(self._epsilon)
        trace: list[CompressionTrace] = []

        for step, instruction in enumerate(program):
            field = self._apply_instruction(field, instruction)
            entropy = field.entropy(self._epsilon)
            trace.append(
                CompressionTrace(
                    step=step,
                    opcode=instruction.opcode,
                    entropy=entropy,
                    compression_score=self._compression_score(initial_entropy, entropy),
                )
            )

        final_entropy = field.entropy(self._epsilon)
        report = AstralCompressionReport(
            field=field,
            initial_entropy=initial_entropy,
            final_entropy=final_entropy,
            compression_ratio=self._compression_score(initial_entropy, final_entropy),
            trace=tuple(trace),
            invariants={
                "probability_mass": round(sum(field.amplitudes.values()), 6),
                "support": field.support(),
                "entropy_delta": round(initial_entropy - final_entropy, 6),
            },
        )
        return report

    def _apply_instruction(
        self, field: ProbabilityField, instruction: CompressionInstruction
    ) -> ProbabilityField:
        opcode = instruction.opcode.lower()
        params = instruction.parameters

        if opcode == "imprint":
            return self._op_imprint(field, params)
        if opcode == "compress":
            return self._op_compress(field, params)
        if opcode == "interfere":
            return self._op_interfere(field, params)
        if opcode == "attenuate":
            return self._op_attenuate(field, params)
        if opcode == "renormalize":
            return field.normalized(self._epsilon)

        # Unknown opcode: return the field unchanged but normalized for safety.
        return field.normalized(self._epsilon)

    def _op_imprint(
        self, field: ProbabilityField, params: Mapping[str, float | Mapping[str, float]]
    ) -> ProbabilityField:
        bias = params.get("bias", {})
        weight = _clamp(float(params.get("weight", 0.5)), 0.0, 1.0)

        if not isinstance(bias, Mapping):
            return field

        merged: MutableMapping[str, float] = dict(field.amplitudes)
        for channel, strength in bias.items():
            strength = max(0.0, float(strength))
            merged[channel] = merged.get(channel, 0.0) * (1 - weight) + strength * weight

        return ProbabilityField(field.label, merged).normalized(self._epsilon)

    def _op_compress(
        self, field: ProbabilityField, params: Mapping[str, float | Mapping[str, float]]
    ) -> ProbabilityField:
        intensity = _clamp(float(params.get("intensity", 1.0)), 0.0, 4.0)
        power = 1.0 + intensity * 0.5
        scaled = {k: v**power for k, v in field.normalized(self._epsilon).amplitudes.items()}
        return ProbabilityField(field.label, scaled).normalized(self._epsilon)

    def _op_interfere(
        self, field: ProbabilityField, params: Mapping[str, float | Mapping[str, float]]
    ) -> ProbabilityField:
        coupling = _clamp(float(params.get("coupling", 0.25)), 0.0, 1.0)
        baseline = field.normalized(self._epsilon)
        mean_intensity = sum(baseline.amplitudes.values()) / max(1, baseline.support())

        interfered: Dict[str, float] = {}
        for channel, amplitude in baseline.amplitudes.items():
            deviation = amplitude - mean_intensity
            interfered[channel] = amplitude + coupling * deviation * amplitude

        return ProbabilityField(field.label, interfered).normalized(self._epsilon)

    def _op_attenuate(
        self, field: ProbabilityField, params: Mapping[str, float | Mapping[str, float]]
    ) -> ProbabilityField:
        damping = _clamp(float(params.get("damping", 0.1)), 0.0, 1.0)
        attenuated = {k: v * (1 - damping) for k, v in field.amplitudes.items()}
        return ProbabilityField(field.label, attenuated).normalized(self._epsilon)

    def _compression_score(self, initial: float, current: float) -> float:
        if initial <= self._epsilon:
            return 0.0
        return round((initial - current) / initial, 6)


def compile_program(instructions: Iterable[Mapping[str, object]]) -> Sequence[CompressionInstruction]:
    """Helper to compile dict-like opcodes into ``CompressionInstruction`` objects."""

    compiled = []
    for spec in instructions:
        opcode = str(spec.get("opcode", "")).lower()
        params = {
            k: v
            for k, v in spec.items()
            if k != "opcode"
        }
        compiled.append(CompressionInstruction(opcode=opcode, parameters=params))
    return tuple(compiled)
