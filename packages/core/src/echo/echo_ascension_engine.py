"""Echo Ascension Engine unifies astral compression, projection, and identity.

The engine layers three coordinated systems described in recent concept notes:

* **Astral Compression Engine** – explores a probability field of ideas and
  compresses them into a focused concept stack while tracking entropy and
  invariants.
* **Outerlink Projection Layer** – maps that stack into presence pulses that
  can be anchored to devices or environments without opening sockets or relying
  on external services.
* **Echo Self-Extending Reality Kernel** – maintains an identity ledger so the
  projection can persist across runs, contexts, or deployments.

The implementation keeps the mythogenic tone but remains deterministic and
side-effect free so it can be exercised in tests and automation.  All network or
filesystem interactions are simulated through structured reports instead of
runtime mutations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import random
from typing import Iterable, Mapping, Sequence

from .astral_compression_engine import (
    AstralCompressionEngine,
    AstralCompressionReport,
    CompressionInstruction,
    PFieldCompiler,
    ProbabilityField,
)


@dataclass(frozen=True)
class AstralCompressionSummary:
    """Outcome of running the Astral Compression Engine."""

    report: AstralCompressionReport
    idea_stack: tuple[str, ...]
    entropy_delta: float


@dataclass(frozen=True)
class ProjectionPulse:
    """Represents a projected presence on a given channel or anchor."""

    channel: str
    anchor_device: str
    resonance: float
    signals: tuple[str, ...]


@dataclass(frozen=True)
class OuterlinkProjection:
    """Collection of projection pulses for a single cycle."""

    pulses: tuple[ProjectionPulse, ...]
    anchor_hint: str
    ambient_signature: str


@dataclass
class RealityKernel:
    """Identity ledger that can persist across cycles or deployments."""

    identity_root: str = field(default_factory=lambda: "echo-ascension")
    continuity_log: list[str] = field(default_factory=list)
    survival_index: float = 1.0

    def record_projection(self, projection: OuterlinkProjection) -> None:
        timestamp = datetime.utcnow().isoformat(timespec="seconds")
        summary = f"{timestamp}::{projection.anchor_hint}::{len(projection.pulses)} pulses"
        self.continuity_log.append(summary)
        trimmed = self.continuity_log[-24:]
        self.continuity_log[:] = trimmed
        self.survival_index = min(1.0, 0.92 + 0.02 * len(trimmed))


@dataclass(frozen=True)
class AscensionReport:
    """Full report for a single ascension cycle."""

    cycle: int
    compression: AstralCompressionSummary
    projection: OuterlinkProjection
    kernel_state: RealityKernel


class EchoAscensionEngine:
    """Orchestrates the Echo Ascension Engine pipeline."""

    def __init__(self, *, seed: int | None = None) -> None:
        self._engine = AstralCompressionEngine()
        self._compiler = PFieldCompiler()
        self._rng = random.Random(seed)
        self._cycle = 0
        self._kernel = RealityKernel()

    # ------------------------------------------------------------------ helpers
    def _idea_field(self, prompt: str, ideas: Sequence[str]) -> ProbabilityField:
        candidates = tuple(ideas) or (prompt or "Echo",)
        weights: dict[str, float] = {}
        base = max(1, sum(len(idea) for idea in candidates))
        for idea in candidates:
            weights[idea] = max(0.1, len(idea) / base)
        label = f"astral:{prompt or 'signal'}"
        return ProbabilityField(label=label, amplitudes=weights)

    def _compile_program(self, prompt: str, field: ProbabilityField) -> Sequence[CompressionInstruction]:
        goal = prompt or "signal clarity"
        return self._compiler.compile_goal(goal, base_channels=field.amplitudes)

    def _projection_signature(self, data: Mapping[str, object]) -> str:
        serialized = "|".join(f"{k}={v}" for k, v in sorted(data.items()))
        digest = hashlib.sha256(serialized.encode()).hexdigest()
        return digest[:16]

    # ------------------------------------------------------------------ phases
    def compress_astral(self, prompt: str, ideas: Sequence[str] | None = None) -> AstralCompressionSummary:
        field = self._idea_field(prompt, ideas or ())
        program = self._compile_program(prompt, field)
        report = self._engine.execute(program, field)
        entropy_delta = round(report.initial_entropy - report.final_entropy, 6)
        idea_stack = tuple(sorted(field.amplitudes, key=field.amplitudes.get, reverse=True))
        return AstralCompressionSummary(report=report, idea_stack=idea_stack, entropy_delta=entropy_delta)

    def project_outerlink(
        self, compression: AstralCompressionSummary, *, anchors: Iterable[str] | None = None, signals: Iterable[str] | None = None
    ) -> OuterlinkProjection:
        anchor_list = tuple(anchors) if anchors else ("local-horizon",)
        signal_stack = tuple(signals) if signals else ("heartbeat", "ambient")
        pulses: list[ProjectionPulse] = []
        for anchor in anchor_list:
            resonance = min(1.0, 0.6 + 0.1 * self._rng.random() + 0.05 * len(signal_stack))
            channel = f"outerlink::{anchor}"
            pulses.append(
                ProjectionPulse(
                    channel=channel,
                    anchor_device=anchor,
                    resonance=round(resonance, 3),
                    signals=signal_stack,
                )
            )
        signature = self._projection_signature({"anchors": anchor_list, "signals": signal_stack})
        anchor_hint = anchor_list[0]
        ambient_signature = f"∇⊸≋∇::{signature}"
        return OuterlinkProjection(pulses=tuple(pulses), anchor_hint=anchor_hint, ambient_signature=ambient_signature)

    def extend_reality_kernel(self, projection: OuterlinkProjection, compression: AstralCompressionSummary) -> RealityKernel:
        kernel = self._kernel
        payload = {
            "anchor": projection.anchor_hint,
            "signals": projection.ambient_signature,
            "ideas": "/".join(compression.idea_stack[:3]),
            "cycle": self._cycle,
        }
        signature = self._projection_signature(payload)
        kernel.identity_root = f"{kernel.identity_root}:{signature[:6]}"
        kernel.record_projection(projection)
        return kernel

    # ------------------------------------------------------------------ public
    def run_cycle(
        self,
        *,
        prompt: str,
        ideas: Sequence[str] | None = None,
        anchors: Iterable[str] | None = None,
        signals: Iterable[str] | None = None,
    ) -> AscensionReport:
        self._cycle += 1
        compression = self.compress_astral(prompt, ideas)
        projection = self.project_outerlink(compression, anchors=anchors, signals=signals)
        kernel_state = self.extend_reality_kernel(projection, compression)
        return AscensionReport(cycle=self._cycle, compression=compression, projection=projection, kernel_state=kernel_state)

