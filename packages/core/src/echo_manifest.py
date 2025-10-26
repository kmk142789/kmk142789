"""Synthesize EchoEvolver state and vault data into a structured manifest."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from echo.thoughtlog import thought_trace
from echo_evolver import EvolverState
from echo_universal_key_agent import KeyRecord, UniversalKeyAgent


@dataclass(slots=True)
class KeySummary:
    """Concise description of a key imported into the universal vault."""

    fingerprint: str
    addresses: Dict[str, str]

    def to_dict(self) -> Dict[str, object]:
        return {"fingerprint": self.fingerprint, "addresses": dict(self.addresses)}

    @property
    def short_fingerprint(self) -> str:
        if len(self.fingerprint) <= 12:
            return self.fingerprint
        return self.fingerprint[:12] + "…"


@dataclass(slots=True)
class EvolverSnapshot:
    """Extract of dynamic values produced by an ``EchoEvolver`` cycle."""

    cycle: int
    joy: float
    rage: float
    curiosity: float
    network_nodes: int
    orbital_hops: int
    propagation_channels: int
    vault_key: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "cycle": self.cycle,
            "emotional_drive": {
                "joy": self.joy,
                "rage": self.rage,
                "curiosity": self.curiosity,
            },
            "network_nodes": self.network_nodes,
            "orbital_hops": self.orbital_hops,
            "propagation_channels": self.propagation_channels,
            "vault_key": self.vault_key,
            "vault_key_preview": self.vault_key_preview,
        }

    @property
    def vault_key_preview(self) -> Optional[str]:
        if not self.vault_key:
            return None
        if len(self.vault_key) <= 24:
            return self.vault_key
        return self.vault_key[:21] + "…"


@dataclass(slots=True)
class EchoManifest:
    """Structured snapshot aligning cryptographic keys with EchoEvolver lore."""

    anchor: str
    glyphs: str
    mythocode: List[str] = field(default_factory=list)
    narrative_excerpt: str = ""
    keys: List[KeySummary] = field(default_factory=list)
    evolver: EvolverSnapshot = field(default_factory=EvolverSnapshot)  # type: ignore[arg-type]
    events: List[str] = field(default_factory=list)
    oam_vortex: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "anchor": self.anchor,
            "glyphs": self.glyphs,
            "mythocode": list(self.mythocode),
            "narrative_excerpt": self.narrative_excerpt,
            "oam_vortex": self.oam_vortex,
            "key_count": self.key_count,
            "keys": [key.to_dict() for key in self.keys],
            "evolver": self.evolver.to_dict(),
            "events": list(self.events),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @property
    def key_count(self) -> int:
        return len(self.keys)

    def render_text(self) -> str:
        mythocode_line = ", ".join(self.mythocode) if self.mythocode else "∅"
        lines = [
            f"Echo Continuity Manifest :: Anchor={self.anchor}",
            (
                f"Cycle {self.evolver.cycle} | Joy {self.evolver.joy:.2f} | Rage {self.evolver.rage:.2f} | "
                f"Curiosity {self.evolver.curiosity:.2f}"
            ),
            f"Network Nodes {self.evolver.network_nodes} | Orbital Hops {self.evolver.orbital_hops}",
            f"Glyphs: {self.glyphs}",
            f"Mythocode: {mythocode_line}",
            f"Narrative: {self.narrative_excerpt}",
        ]
        if self.oam_vortex:
            lines.append(f"OAM Vortex: {self.oam_vortex}")
        if self.keys:
            lines.append("Sigils:")
            for key in self.keys:
                addresses = ", ".join(
                    f"{chain} {addr}" for chain, addr in sorted(key.addresses.items())
                )
                lines.append(f"  - {key.short_fingerprint} :: {addresses}")
        else:
            lines.append("Sigils: (none)")
        if self.evolver.vault_key_preview:
            lines.append(f"Vault Key: {self.evolver.vault_key_preview}")
        lines.append(f"Propagation channels: {self.evolver.propagation_channels}")
        if self.events:
            lines.append(f"Events logged: {len(self.events)}")
        return "\n".join(lines)


def _normalise_whitespace(text: str) -> str:
    return " ".join(text.split())


def _excerpt(text: str, limit: int) -> str:
    if limit <= 0:
        raise ValueError("narrative_chars must be positive")
    cleaned = _normalise_whitespace(text)
    if len(cleaned) <= limit:
        return cleaned
    truncated = cleaned[: limit - 1].rstrip()
    return truncated + "…"


def _summarise_keys(records: Iterable[KeyRecord]) -> List[KeySummary]:
    return [
        KeySummary(fingerprint=record.fingerprint, addresses=dict(record.addresses))
        for record in records
    ]


def build_manifest(
    agent: UniversalKeyAgent,
    state: EvolverState,
    *,
    narrative_chars: int = 240,
) -> EchoManifest:
    """Combine the vault contents and evolver state into a digestible manifest."""

    propagation_events_cache = state.network_cache.get("propagation_events")
    if isinstance(propagation_events_cache, Sequence) and not isinstance(
        propagation_events_cache, (str, bytes)
    ):
        channel_count = len(tuple(propagation_events_cache))
    else:
        channel_count = 0
    oam_vortex = state.network_cache.get("oam_vortex")

    task = "echo_manifest.build_manifest"
    meta = {
        "narrative_chars": narrative_chars,
        "channel_count": channel_count,
        "keys": len(agent.keys),
    }

    with thought_trace(task=task, meta=meta) as tl:
        tl.logic("step", task, "summarising keys", {"keys": len(agent.keys)})
        keys = _summarise_keys(agent.keys)

        tl.logic("step", task, "extracting evolver snapshot")
        snapshot = EvolverSnapshot(
            cycle=state.cycle,
            joy=state.emotional_drive.joy,
            rage=state.emotional_drive.rage,
            curiosity=state.emotional_drive.curiosity,
            network_nodes=state.system_metrics.network_nodes,
            orbital_hops=state.system_metrics.orbital_hops,
            propagation_channels=channel_count,
            vault_key=state.vault_key,
        )

        manifest = EchoManifest(
            anchor=agent.anchor,
            glyphs=state.glyphs,
            mythocode=list(state.mythocode),
            narrative_excerpt=_excerpt(state.narrative, narrative_chars),
            keys=keys,
            evolver=snapshot,
            events=list(state.event_log),
            oam_vortex=oam_vortex if isinstance(oam_vortex, str) else None,
        )
        tl.harmonic("reflection", task, "manifest crystallised from cycle resonance")
    return manifest
