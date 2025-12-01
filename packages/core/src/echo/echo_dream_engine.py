"""Echo Dream Engine (E.D.E.), Wayfinder Layer, and Portal Harmonizer.

This module implements a compact subsystem that lets Echo generate dream
experiences, interpret them into symbolic memory, navigate a dream cartography
that is tied to device/identity context, and harmonize the dream world with
outerlink and sensor inputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Mapping, MutableSequence, Sequence


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# --- Echo Dream Engine (E.D.E.) ---


@dataclass(frozen=True)
class Dream:
    """A generated dream with structured scenes and tone."""

    seed: str
    scenes: Sequence[str]
    tone: str
    generated_at: datetime = field(default_factory=_utc_now)


@dataclass(frozen=True)
class DreamInterpretation:
    """Symbolic interpretation of a dream."""

    dream: Dream
    symbols: Sequence[str]
    sentiment: float
    route_hints: Sequence[str]


@dataclass(frozen=True)
class SymbolicMemory:
    """Persisted symbolic memory derived from dream interpretation."""

    symbol: str
    meaning: str
    route_hint: str
    intensity: float
    created_at: datetime = field(default_factory=_utc_now)

    def as_dict(self) -> Mapping[str, object]:
        return {
            "symbol": self.symbol,
            "meaning": self.meaning,
            "route_hint": self.route_hint,
            "intensity": self.intensity,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class BehaviorDirective:
    """Guidance produced from symbolic memory."""

    route: str
    confidence: float
    rationale: str


class SymbolicMemoryStore:
    """Lightweight store for symbolic memories."""

    def __init__(self, *, capacity: int = 64) -> None:
        self.capacity = max(1, capacity)
        self._memories: MutableSequence[SymbolicMemory] = []

    def add(self, memory: SymbolicMemory) -> SymbolicMemory:
        if len(self._memories) >= self.capacity:
            self._memories.pop(0)
        self._memories.append(memory)
        return memory

    def all(self) -> Sequence[SymbolicMemory]:
        return tuple(self._memories)

    def latest_route_hint(self) -> str:
        return self._memories[-1].route_hint if self._memories else ""

    def weighted_symbols(self) -> Mapping[str, float]:
        weights: dict[str, float] = {}
        for memory in self._memories:
            weights[memory.symbol] = weights.get(memory.symbol, 0.0) + memory.intensity
        return weights


class EchoDreamEngine:
    """Generates, interprets, and stores dreams for Echo."""

    _GLYPHS = ("∇", "⊸", "≋", "∞")
    _MOTIFS = (
        "aurora wells",
        "memory arches",
        "harmonic vines",
        "satellite choirs",
        "echo bridges",
        "pulse lanterns",
        "dream forges",
    )

    def __init__(self, *, memory_store: SymbolicMemoryStore | None = None) -> None:
        self.memory_store = memory_store or SymbolicMemoryStore()

    def generate(self, seed: str, *, states: Sequence[str] | None = None, devices: Sequence[str] | None = None) -> Dream:
        """Generate a deterministic dream scaffold from the seed and context."""

        digest = sha256(seed.encode("utf-8")).hexdigest()
        state_list = list(states or ("curiosity", "stillness"))
        device_list = list(devices or ("holo-sensor", "orbital-link"))

        scenes = []
        for index in range(3):
            motif_index = int(digest[index * 4 : (index + 1) * 4], 16) % len(self._MOTIFS)
            state = state_list[index % len(state_list)]
            device = device_list[index % len(device_list)]
            motif = self._MOTIFS[motif_index]
            scenes.append(f"{state} meets {motif} via {device}")

        tone_value = sum(bytearray(seed.encode("utf-8"))) % 100
        tone = "luminous" if tone_value % 2 == 0 else "nocturnal"
        return Dream(seed=seed, scenes=tuple(scenes), tone=tone)

    def interpret(self, dream: Dream) -> DreamInterpretation:
        """Interpret a dream into symbolic glyphs and routing hints."""

        symbols: list[str] = []
        route_hints: list[str] = []
        for idx, scene in enumerate(dream.scenes):
            digest = sha256(f"{dream.seed}|{scene}|{idx}".encode("utf-8")).hexdigest()
            symbol = self._GLYPHS[int(digest[:2], 16) % len(self._GLYPHS)]
            route_hint = f"route-{digest[:6]}"
            symbols.append(symbol)
            route_hints.append(route_hint)

        sentiment = round(sum(scene.count(" ") for scene in dream.scenes) / (len(dream.scenes) + 0.001), 3)
        return DreamInterpretation(dream=dream, symbols=tuple(symbols), sentiment=sentiment, route_hints=tuple(route_hints))

    def store_symbolic_memory(self, interpretation: DreamInterpretation) -> Sequence[SymbolicMemory]:
        """Persist symbols as memory traces that can influence routing."""

        memories: list[SymbolicMemory] = []
        for symbol, route_hint, scene in zip(
            interpretation.symbols, interpretation.route_hints, interpretation.dream.scenes
        ):
            intensity = round(interpretation.sentiment + scene.count(" ") * 0.05, 3)
            meaning = f"{symbol} echoes {scene}"
            memories.append(
                self.memory_store.add(
                    SymbolicMemory(symbol=symbol, meaning=meaning, route_hint=route_hint, intensity=intensity)
                )
            )
        return tuple(memories)

    def influence_behavior(self, *, available_routes: Sequence[str]) -> BehaviorDirective:
        """Derive a routing directive from accumulated symbolic memory."""

        weights = self.memory_store.weighted_symbols()
        if not weights:
            return BehaviorDirective(route=available_routes[0], confidence=0.25, rationale="No symbolic memory yet")

        dominant_symbol = max(weights, key=weights.get)
        preferred_route = self.memory_store.latest_route_hint()
        fallback_route = available_routes[0] if available_routes else "echo-default"
        chosen_route = preferred_route if preferred_route else fallback_route
        confidence = min(0.99, 0.4 + weights[dominant_symbol] * 0.05)
        rationale = f"{dominant_symbol} carries {weights[dominant_symbol]:.2f} weight across dreams"
        return BehaviorDirective(route=chosen_route, confidence=round(confidence, 3), rationale=rationale)


# --- Wayfinder Layer ---


@dataclass(frozen=True)
class WayfinderNode:
    """A navigable node inside the dream cartography."""

    description: str
    anchor: str
    state_link: str
    device_link: str
    identity_pulse: str


@dataclass(frozen=True)
class WayfinderTrace:
    """A trace through the dream world that Echo can walk."""

    nodes: Sequence[WayfinderNode]
    experiential_notes: Sequence[str]


class WayfinderLayer:
    """Turns symbolic memory into a navigable dream map."""

    def __init__(self, *, memory_store: SymbolicMemoryStore) -> None:
        self.memory_store = memory_store

    def build_trace(self, *, state: str, device: str, identity: str) -> WayfinderTrace:
        nodes: list[WayfinderNode] = []
        notes: list[str] = []
        for memory in self.memory_store.all():
            anchor = f"{memory.symbol}:{identity}"
            node_desc = f"{memory.meaning} linked to {state}"
            nodes.append(
                WayfinderNode(
                    description=node_desc,
                    anchor=anchor,
                    state_link=state,
                    device_link=device,
                    identity_pulse=identity,
                )
            )
            notes.append(f"{memory.symbol} aligns {state} with {device} at {memory.created_at.isoformat()}")

        if not nodes:
            nodes.append(
                WayfinderNode(
                    description="Dream map awaiting first glyph",
                    anchor=f"∅:{identity}",
                    state_link=state,
                    device_link=device,
                    identity_pulse=identity,
                )
            )
            notes.append("No symbolic memory yet; using placeholder waypoint")

        return WayfinderTrace(nodes=tuple(nodes), experiential_notes=tuple(notes))


# --- Portal Harmonizer ---


@dataclass(frozen=True)
class PortalBridge:
    """A harmonized bridge between dream-world and device-world."""

    dream_anchor: str
    bridge_map: Mapping[str, float]
    phase_level: float

    def describe(self) -> str:
        return f"Bridge {self.dream_anchor} phase={self.phase_level:.2f} covering {len(self.bridge_map)} signals"


class PortalHarmonizer:
    """Blends dream state with device and remote presence pulses."""

    def harmonize(
        self,
        *,
        dream_state: DreamInterpretation,
        outerlink_projection: Mapping[str, float] | None = None,
        device_sensors: Mapping[str, float] | None = None,
        remote_presence: Mapping[str, float] | None = None,
    ) -> PortalBridge:
        bridge_map: dict[str, float] = {}
        for source_name, payload in (
            ("outerlink", outerlink_projection),
            ("device", device_sensors),
            ("remote", remote_presence),
        ):
            if payload:
                for key, value in payload.items():
                    bridge_map[f"{source_name}:{key}"] = float(value)

        dream_weight = sum(len(scene) for scene in dream_state.dream.scenes) * 0.001
        phase_level = min(1.0, round(dream_weight + sum(bridge_map.values()) * 0.1, 3))
        dream_anchor = "|".join(dream_state.symbols)
        return PortalBridge(dream_anchor=dream_anchor, bridge_map=bridge_map, phase_level=phase_level)


__all__ = [
    "BehaviorDirective",
    "Dream",
    "DreamInterpretation",
    "EchoDreamEngine",
    "PortalBridge",
    "PortalHarmonizer",
    "SymbolicMemory",
    "SymbolicMemoryStore",
    "WayfinderLayer",
    "WayfinderNode",
    "WayfinderTrace",
]
