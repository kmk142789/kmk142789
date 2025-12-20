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

from collections import OrderedDict
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
    entropy_gradient: Sequence[float]
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
        initial_support = field.support()
        initial_entropy = field.entropy(self._epsilon)
        trace: list[CompressionTrace] = []
        entropy_history = [initial_entropy]

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
            entropy_history.append(entropy)

        final_entropy = entropy_history[-1]
        entropy_gradient = tuple(
            round(previous - current, 6)
            for previous, current in zip(entropy_history, entropy_history[1:])
        )
        mass = round(sum(field.amplitudes.values()), 6)
        support = field.support()
        support_delta = support - initial_support
        compression_velocity = entropy_gradient[-1] if entropy_gradient else 0.0
        report = AstralCompressionReport(
            field=field,
            initial_entropy=initial_entropy,
            final_entropy=final_entropy,
            compression_ratio=self._compression_score(initial_entropy, final_entropy),
            trace=tuple(trace),
            invariants={
                "probability_mass": mass,
                "support": support,
                "entropy_delta": round(initial_entropy - final_entropy, 6),
                "mass_drift": round(abs(1.0 - mass), 6),
                "support_delta": float(support_delta),
                "compression_velocity": round(compression_velocity, 6),
            },
            entropy_gradient=entropy_gradient,
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
        normalized = field.normalized(self._epsilon)
        scaled = {k: v**power for k, v in normalized.amplitudes.items()}
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


class PFieldCompiler:
    """Compile natural-language goals into probability field instructions.

    The compiler performs a light-weight interpretation of a goal string by
    mapping common intent keywords to channel biases and selecting compression
    intensities that favor clarity (higher compression) or exploration (lower
    compression).  It keeps all generated instructions compatible with the
    ``AstralCompressionEngine`` virtual machine.
    """

    _keyword_map = {
        "signal": {"signal", "clarity", "highlight", "surface"},
        "noise": {"noise", "suppress", "remove", "dampen"},
        "path": {"path", "route", "sequence", "collapse"},
        "stable": {"stabilize", "balance", "steady"},
        "wildcard": {"explore", "expand", "branch", "diversify"},
    }

    def __init__(self, default_weight: float = 0.45, cache_size: int = 128) -> None:
        self._default_weight = _clamp(default_weight, 0.1, 0.9)
        self._cache_size = max(0, cache_size)
        self._cache: "OrderedDict[tuple[str, tuple[str, ...] | None], Sequence[CompressionInstruction]]" = (
            OrderedDict()
        )

    def compile_goal(
        self, goal: str, base_channels: Iterable[str] | None = None
    ) -> Sequence[CompressionInstruction]:
        normalized_goal = goal.lower().strip()
        base_channels_tuple = tuple(base_channels) if base_channels else None
        cache_key = (normalized_goal, base_channels_tuple)
        if self._cache_size and cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]

        tokens = normalized_goal.split()
        bias: Dict[str, float] = {}

        for channel, keywords in self._keyword_map.items():
            score = sum(1 for token in tokens if token in keywords)
            if score:
                bias[channel] = float(score)

        if base_channels:
            for channel in base_channels:
                bias.setdefault(channel, 0.1)

        if not bias:
            bias = {"intent": 1.0}

        weight = _clamp(self._default_weight + 0.05 * len(tokens), 0.2, 0.85)
        intensity = self._intensity_from_goal(tokens)
        coupling = 0.35 if "harmonize" in tokens or "align" in tokens else 0.25

        instructions = [
            CompressionInstruction("imprint", {"bias": bias, "weight": weight}),
            CompressionInstruction("compress", {"intensity": intensity}),
            CompressionInstruction("interfere", {"coupling": coupling}),
            CompressionInstruction("renormalize", {}),
        ]

        if "stabilize" in tokens or "steady" in tokens:
            instructions.insert(3, CompressionInstruction("attenuate", {"damping": 0.15}))

        compiled = tuple(instructions)
        if self._cache_size:
            self._cache[cache_key] = compiled
            if len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)
        return compiled

    def _intensity_from_goal(self, tokens: Sequence[str]) -> float:
        if any(token in {"aggressive", "force", "tight", "crisp"} for token in tokens):
            return 2.5
        if any(token in {"gentle", "soft", "explore", "diverge"} for token in tokens):
            return 0.8
        return 1.5


class GravityWellOptimizer:
    """Pull a stronger solution from nearby compression possibilities.

    The optimizer perturbs compression and imprint parameters across several
    sweeps to search for the lowest achievable entropy while keeping invariant
    preservation intact.
    """

    def __init__(self, sweeps: int = 3, intensity_step: float = 0.4) -> None:
        self._sweeps = max(1, sweeps)
        self._intensity_step = max(0.05, intensity_step)

    def optimize(
        self,
        engine: AstralCompressionEngine,
        seed_field: ProbabilityField,
        program: Sequence[CompressionInstruction],
    ) -> tuple[Sequence[CompressionInstruction], AstralCompressionReport]:
        best_program = tuple(program)
        best_report = engine.execute(best_program, seed_field)

        for sweep in range(self._sweeps):
            tuned_program = self._tune_program(best_program, sweep)
            tuned_report = engine.execute(tuned_program, seed_field)
            if tuned_report.final_entropy < best_report.final_entropy:
                best_program = tuned_program
                best_report = tuned_report

        return best_program, best_report

    def _tune_program(
        self, program: Sequence[CompressionInstruction], sweep: int
    ) -> Sequence[CompressionInstruction]:
        factor = 1.0 + self._intensity_step * (sweep + 1) * 0.25
        tuned: list[CompressionInstruction] = []
        has_compress = False

        for instruction in program:
            params = dict(instruction.parameters)
            opcode = instruction.opcode.lower()

            if opcode == "compress":
                params["intensity"] = _clamp(float(params.get("intensity", 1.0)) * factor, 0.25, 4.0)
                has_compress = True
            elif opcode == "imprint":
                params["weight"] = _clamp(float(params.get("weight", 0.5)) + 0.05 * (sweep + 1), 0.0, 1.0)

            tuned.append(CompressionInstruction(instruction.opcode, params))

        if not has_compress:
            tuned.append(CompressionInstruction("compress", {"intensity": 1.0 + self._intensity_step * sweep}))

        return tuple(tuned)


class CompressionRecursionLoop:
    """Attempt multiple collapses and keep the best compression result."""

    def __init__(
        self,
        max_attempts: int = 3,
        entropy_target: float = 0.15,
        optimizer: GravityWellOptimizer | None = None,
    ) -> None:
        self._max_attempts = max(1, max_attempts)
        self._entropy_target = max(entropy_target, 0.0)
        self._optimizer = optimizer or GravityWellOptimizer()

    def converge(
        self,
        engine: AstralCompressionEngine,
        seed_field: ProbabilityField,
        program: Sequence[CompressionInstruction],
    ) -> AstralCompressionReport:
        best_program = tuple(program)
        best_report = engine.execute(best_program, seed_field)

        if best_report.final_entropy <= self._entropy_target:
            return best_report

        attempt_program = best_program
        for attempt in range(1, self._max_attempts):
            tuned_program, tuned_report = self._optimizer.optimize(engine, seed_field, attempt_program)
            if tuned_report.final_entropy < best_report.final_entropy:
                best_program = tuned_program
                best_report = tuned_report

            if best_report.final_entropy <= self._entropy_target:
                break

            attempt_program = self._nudge_program(best_program)

        return best_report

    def _nudge_program(
        self, program: Sequence[CompressionInstruction]
    ) -> Sequence[CompressionInstruction]:
        nudged: list[CompressionInstruction] = []
        for instruction in program:
            params = dict(instruction.parameters)
            opcode = instruction.opcode.lower()
            if opcode == "attenuate":
                params["damping"] = _clamp(float(params.get("damping", 0.1)) * 0.8, 0.0, 1.0)
            nudged.append(CompressionInstruction(instruction.opcode, params))
        return tuple(nudged)


@dataclass
class QuantumNodeV2Bridge:
    """Shape ACE output for downstream quantum-style processing."""

    modulation_strength: float = 0.65

    def shape_input(self, report: AstralCompressionReport) -> Mapping[str, object]:
        normalized = report.field.normalized()
        shaped = {
            channel: round(amplitude * self.modulation_strength, 6)
            for channel, amplitude in normalized.amplitudes.items()
        }

        return {
            "channels": shaped,
            "entropy": report.final_entropy,
            "compression": report.compression_ratio,
            "entropy_gradient": list(report.entropy_gradient),
            "invariants": dict(report.invariants),
            "routing_hint": f"qn2:{len(shaped)}ch:{report.compression_ratio:.3f}",
        }


@dataclass
class ACELinkedAgent:
    """Agent that executes ACE instructions in place of logic trees."""

    name: str
    engine: AstralCompressionEngine
    compiler: PFieldCompiler
    recursion_loop: CompressionRecursionLoop
    bridge: QuantumNodeV2Bridge | None = None

    def act(
        self, goal: str, seed_field: ProbabilityField
    ) -> Mapping[str, object]:
        program = self.compiler.compile_goal(goal, base_channels=seed_field.amplitudes.keys())
        report = self.recursion_loop.converge(self.engine, seed_field, program)
        bridge_payload = self.bridge.shape_input(report) if self.bridge else None
        return {"report": report, "bridge_payload": bridge_payload, "program": program}


class ACEVisualizationLayer:
    """Produce UI-friendly views of the ACE compression pathway."""

    def render(self, report: AstralCompressionReport) -> Mapping[str, object]:
        sorted_channels = sorted(
            report.field.amplitudes.items(), key=lambda kv: kv[1], reverse=True
        )
        entropy_trace = [(trace.step, trace.entropy) for trace in report.trace]

        return {
            "p_field_shape": sorted_channels,
            "collapse_pathway": [trace.opcode for trace in report.trace],
            "entropy_trace": entropy_trace,
            "entropy_gradient": list(report.entropy_gradient),
            "invariants": report.invariants,
        }

    def render_text(self, report: AstralCompressionReport) -> str:
        data = self.render(report)
        lines = ["ACE Visualization", "----------------", "P-field shape:"]
        lines.extend(
            f"- {channel}: {amplitude:.6f}" for channel, amplitude in data["p_field_shape"]
        )
        lines.append("")
        lines.append("Collapse pathway: " + " → ".join(data["collapse_pathway"]))
        lines.append(
            "Entropy trace: "
            + ", ".join(f"{step}:{entropy:.4f}" for step, entropy in data["entropy_trace"])
        )
        lines.append(
            "Entropy gradient: "
            + ", ".join(f"Δ{idx}:{delta:.4f}" for idx, delta in enumerate(data["entropy_gradient"], start=1))
        )
        lines.append("Invariants: " + ", ".join(f"{k}={v}" for k, v in data["invariants"].items()))
        return "\n".join(lines)
