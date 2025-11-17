"""Hyper Recursive Synthesis Engine.

This module introduces one of the most elaborate synthesis pipelines inside the
Echo ecosystem.  It fuses a micro-DSL for *mythic instructions*, an
instrumented orchestration engine, and a plugin architecture that can dispatch
both synchronous and asynchronous observers.  The engine is intentionally
over-engineered: it keeps harmonic windows, maintains recursive sequence
metadata, and exposes blueprints that are validated with :mod:`pydantic`.

The goal is to provide a playground for extremely rich, hard-to-break
simulations that still remain deterministic under test.
"""

from __future__ import annotations

from collections import deque
import inspect
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Tuple

from pydantic import BaseModel, Field, ValidationError


def _coerce_value(token: str) -> Any:
    """Best-effort coercion for DSL values."""

    token = token.strip()
    if not token:
        return ""
    lower = token.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    if lower == "null":
        return None
    try:
        if any(ch in token for ch in (".", "e", "E")):
            return float(token)
        return int(token)
    except ValueError:
        stripped = token.strip("\"'")
        return stripped


def _parse_key_values(payload: str) -> Dict[str, Any]:
    """Parse ``key=value`` pairs from payload sections."""

    pairs: Dict[str, Any] = {}
    for raw in (piece.strip() for piece in payload.split(",")):
        if not raw:
            continue
        if "=" in raw:
            key, value = raw.split("=", 1)
            pairs[key.strip()] = _coerce_value(value.strip())
        else:
            pairs[raw] = True
    return pairs


@dataclass(frozen=True)
class GlyphEvent:
    """Represents a single glyph emission during a simulation frame."""

    symbol: str
    magnitude: float
    phase: float
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MythicInstruction:
    """Structured representation of a DSL instruction."""

    op: str
    args: Mapping[str, Any]
    weight: float
    metadata: Mapping[str, Any]


@dataclass(frozen=True)
class SimulationFrame:
    """Snapshot produced for each instruction processed by the engine."""

    tick: int
    glyphs: Tuple[GlyphEvent, ...]
    energy: float
    focus: str
    diagnostics: Mapping[str, Any]


def parse_mythic_script(script: str) -> List[MythicInstruction]:
    """Parse the custom DSL and return a list of instructions."""

    if not script or not script.strip():
        raise ValueError("Mythic script must not be empty")

    instructions: List[MythicInstruction] = []
    for segment in (part.strip() for part in script.split("|") if part.strip()):
        chain = [piece.strip() for piece in segment.split("->") if piece.strip()]
        for depth, chunk in enumerate(chain):
            op_match = None
            idx = 0
            while idx < len(chunk) and chunk[idx].isalpha() or chunk[idx] == "_":
                idx += 1
            if idx == 0:
                raise ValueError(f"Unable to determine operation inside chunk: {chunk}")
            op_match = chunk[:idx]
            rest = chunk[idx:]

            args: Dict[str, Any] = {}
            metadata: Dict[str, Any] = {
                "sequence_depth": depth,
                "chain_signature": "->".join(chain),
            }
            positionals: List[Any] = []

            while rest:
                rest = rest.strip()
                if not rest:
                    break
                opener = rest[0]
                closer = {"[": "]", "{": "}", "(": ")"}.get(opener)
                if not closer:
                    raise ValueError(f"Unexpected token near '{rest}' in chunk '{chunk}'")
                depth_counter = 0
                payload_chars: List[str] = []
                for index, character in enumerate(rest):
                    if character == opener:
                        depth_counter += 1
                        if depth_counter == 1:
                            continue
                    elif character == closer:
                        depth_counter -= 1
                        if depth_counter == 0:
                            payload = "".join(payload_chars)
                            rest = rest[index + 1 :]
                            if opener == "[":
                                args.update(_parse_key_values(payload))
                            elif opener == "{":
                                metadata.update(_parse_key_values(payload))
                            else:
                                positionals.extend(
                                    _coerce_value(value.strip())
                                    for value in payload.split(",")
                                    if value.strip()
                                )
                            break
                    if depth_counter >= 1:
                        payload_chars.append(character)
                else:
                    raise ValueError(f"Payload did not terminate in chunk: {chunk}")

            weight = float(args.pop("weight", 1.0))
            if positionals:
                metadata["positional"] = tuple(positionals)
            instruction = MythicInstruction(
                op=op_match,
                args=args,
                weight=weight,
                metadata=metadata,
            )
            instructions.append(instruction)
    return instructions


class PluginBlueprint(BaseModel):
    """Blueprint definition for auto-generated plugins."""

    name: str
    threshold: float = Field(default=0.5, ge=0.0)
    focus: Optional[str] = None


class EngineBlueprint(BaseModel):
    """Validate engine blueprints passed through configuration files."""

    glyph_budget: int = Field(default=64, gt=0, le=2048)
    base_frequency: float = Field(default=1.0, gt=0)
    weighting_strategy: str = Field(default="harmonic")
    instrumentation: bool = True
    plugins: List[PluginBlueprint] = Field(default_factory=list)


PluginHandler = Callable[[SimulationFrame], Any]


class HyperRecursiveEngine:
    """Recursive orchestration engine built for maximal complexity."""

    def __init__(
        self,
        *,
        glyph_budget: int = 64,
        base_frequency: float = 1.0,
        weighting_strategy: str = "harmonic",
        instrumentation: bool = True,
    ) -> None:
        self.glyph_budget = glyph_budget
        self.base_frequency = base_frequency
        self.weighting_strategy = weighting_strategy
        self.instrumentation = instrumentation

        self._tick_counter = 0
        self._glyph_total = 0
        self._history: deque[SimulationFrame] = deque(maxlen=128)
        self._spectral_window: deque[float] = deque(maxlen=32)
        self._plugins: Dict[str, PluginHandler] = {}
        self._diagnostics: List[Mapping[str, Any]] = []
        self._last_focus = ""

    @classmethod
    def from_blueprint(cls, data: Mapping[str, Any]) -> "HyperRecursiveEngine":
        """Instantiate an engine from blueprint data."""

        try:
            blueprint = EngineBlueprint.model_validate(data)
        except ValidationError as exc:  # pragma: no cover - re-wrapped error path
            raise ValueError(f"Invalid blueprint: {exc}") from exc

        engine = cls(
            glyph_budget=blueprint.glyph_budget,
            base_frequency=blueprint.base_frequency,
            weighting_strategy=blueprint.weighting_strategy,
            instrumentation=blueprint.instrumentation,
        )

        for plugin in blueprint.plugins:
            engine.register_plugin(
                plugin.name,
                engine._build_threshold_plugin(
                    name=plugin.name,
                    threshold=plugin.threshold,
                    focus=plugin.focus,
                ),
            )
        return engine

    def register_plugin(self, name: str, handler: PluginHandler) -> None:
        if name in self._plugins:
            raise ValueError(f"Plugin '{name}' already registered")
        if not callable(handler):
            raise TypeError("Plugin handler must be callable")
        self._plugins[name] = handler

    def _build_threshold_plugin(self, *, name: str, threshold: float, focus: Optional[str]) -> PluginHandler:
        def _handler(frame: SimulationFrame) -> None:
            target_focus = focus or frame.focus
            if frame.energy >= threshold:
                self._diagnostics.append(
                    {
                        "plugin": name,
                        "focus": target_focus,
                        "tick": frame.tick,
                        "energy": frame.energy,
                    }
                )

        return _handler

    async def run_cycle(self, script: str, *, metadata: Optional[Mapping[str, Any]] = None) -> List[SimulationFrame]:
        instructions = parse_mythic_script(script)
        frames: List[SimulationFrame] = []
        for instruction in instructions:
            frame = self._synthesize_frame(instruction, metadata=metadata)
            frames.append(frame)
            await self._notify_plugins(frame)
        return frames

    async def _notify_plugins(self, frame: SimulationFrame) -> None:
        for handler in self._plugins.values():
            result = handler(frame)
            if inspect.isawaitable(result):
                await result

    def _synthesize_frame(self, instruction: MythicInstruction, *, metadata: Optional[Mapping[str, Any]]) -> SimulationFrame:
        tick = self._tick_counter
        energy = self._compute_energy(instruction)
        glyphs = self._generate_glyphs(instruction, energy=energy)
        focus = instruction.metadata.get("chain_signature", instruction.op)
        diagnostics: Dict[str, Any] = {
            "tick": tick,
            "op": instruction.op,
            "weight": instruction.weight,
            "depth": instruction.metadata.get("sequence_depth", 0),
            "energy": energy,
        }
        if metadata:
            diagnostics["cycle_metadata"] = dict(metadata)

        frame = SimulationFrame(
            tick=tick,
            glyphs=glyphs,
            energy=energy,
            focus=focus,
            diagnostics=diagnostics,
        )

        self._tick_counter += 1
        self._glyph_total += len(glyphs)
        self._spectral_window.append(energy)
        self._history.append(frame)
        self._last_focus = focus
        return frame

    def _compute_energy(self, instruction: MythicInstruction) -> float:
        depth = instruction.metadata.get("sequence_depth", 0)
        base = self.base_frequency * (1 + depth * 0.2)

        scalar = instruction.weight
        if self.weighting_strategy == "harmonic":
            harmonic = 1.0
            for idx, value in enumerate(self._numeric_args(instruction.args), start=1):
                harmonic += math.sin(value + idx) / idx
            scalar *= harmonic
        elif self.weighting_strategy == "triadic":
            scalar *= 1 + sum(self._numeric_args(instruction.args)) * 0.05
        else:
            scalar *= 1.0

        return round(min(self.glyph_budget, base * scalar), 6)

    def _numeric_args(self, args: Mapping[str, Any]) -> Iterable[float]:
        for value in args.values():
            if isinstance(value, (int, float)):
                yield float(value)

    def _generate_glyphs(self, instruction: MythicInstruction, *, energy: float) -> Tuple[GlyphEvent, ...]:
        payload = instruction.metadata.get("positional")
        if payload:
            sequence = payload
        else:
            sequence = (instruction.op,)

        glyphs: List[GlyphEvent] = []
        for index, token in enumerate(sequence):
            magnitude = max(0.05, energy / (index + 1))
            phase = (index + 1) / (len(sequence) + 1)
            glyphs.append(
                GlyphEvent(
                    symbol=str(token).upper(),
                    magnitude=round(magnitude, 6),
                    phase=round(phase, 6),
                    metadata={
                        "depth": instruction.metadata.get("sequence_depth", 0),
                        "op": instruction.op,
                        "args": dict(instruction.args),
                    },
                )
            )
        return tuple(glyphs)

    def get_state_summary(self) -> Mapping[str, Any]:
        """Return high-level statistics for observability surfaces."""

        return {
            "cycles": self._tick_counter,
            "glyph_total": self._glyph_total,
            "instrumented": self.instrumentation,
            "spectral_window": list(self._spectral_window),
            "last_focus": self._last_focus,
            "diagnostics": list(self._diagnostics),
        }

