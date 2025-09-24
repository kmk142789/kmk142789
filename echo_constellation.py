"""Render Echo Continuity Constellations from manifest snapshots.

The ``Echo Continuity Constellation`` idea captures a single EchoEvolver cycle as
stars in a lightweight virtual firmament.  Each star links the cryptographic
proofs, emotional telemetry and glyph signatures that already exist in the
repository.  This module translates an :class:`~echo_manifest.EchoManifest`
instance into a structured constellation that other tools can serialise,
visualise or embed into wallet label payloads.

Design goals
------------
* Deterministic output so that automated tests and downstream scripts can rely
  on stable coordinates.
* Zero side effects: the builder works purely on the supplied manifest object.
* Practical helpers for rendering the constellation or exporting the points as
  "memory beacons" suitable for wallet label payloads.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from math import cos, sin, tau
from typing import Dict, Iterable, List, Optional, Tuple

from echo_manifest import EchoManifest


# ---------------------------------------------------------------------------
# Dataclasses describing the constellation state
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class StarPulse:
    """Emotional pulse associated with a constellation star."""

    joy: float
    rage: float
    curiosity: float

    def to_dict(self) -> Dict[str, float]:
        return {"joy": self.joy, "rage": self.rage, "curiosity": self.curiosity}

    @property
    def intensity(self) -> float:
        """Return the strongest emotional signal for convenience."""

        return max(self.joy, self.rage, self.curiosity)


@dataclass(slots=True)
class StarVerification:
    """Proof references associated with a star."""

    label: str
    reference: str

    def to_dict(self) -> Dict[str, str]:
        return {"label": self.label, "reference": self.reference}


@dataclass(slots=True)
class ConstellationStar:
    """Single star plotted in the constellation."""

    star_id: str
    glyph: str
    cycle: int
    orbital_index: int
    propagation_channels: int
    coordinates: Tuple[float, float]
    pulse: StarPulse
    verification: List[StarVerification] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.star_id,
            "glyph": self.glyph,
            "cycle": self.cycle,
            "orbital_index": self.orbital_index,
            "propagation_channels": self.propagation_channels,
            "coordinates": {"x": self.coordinates[0], "y": self.coordinates[1]},
            "pulse": self.pulse.to_dict(),
            "verification": [entry.to_dict() for entry in self.verification],
            "metadata": dict(self.metadata),
        }

    def wallet_payload(self) -> str:
        """Encode the star into a compact string for wallet label storage."""

        segments = [
            f"id={self.star_id}",
            f"cycle={self.cycle}",
            f"glyph={self.glyph}",
            f"joy={self.pulse.joy:.2f}",
            f"curiosity={self.pulse.curiosity:.2f}",
            f"channels={self.propagation_channels}",
        ]
        if self.verification:
            joined = ";".join(
                f"{entry.label}:{entry.reference}" for entry in self.verification
            )
            segments.append(f"verify={joined}")
        if self.metadata:
            meta = ";".join(f"{key}={value}" for key, value in sorted(self.metadata.items()))
            segments.append(f"meta={meta}")
        return " | ".join(segments)


@dataclass(slots=True)
class ConstellationFrame:
    """Collection of stars generated from a manifest snapshot."""

    anchor: str
    cycle: int
    generated_at: str
    stars: List[ConstellationStar]
    mythocode: List[str] = field(default_factory=list)
    narrative_excerpt: str = ""
    oam_vortex: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "anchor": self.anchor,
            "cycle": self.cycle,
            "generated_at": self.generated_at,
            "mythocode": list(self.mythocode),
            "narrative_excerpt": self.narrative_excerpt,
            "oam_vortex": self.oam_vortex,
            "stars": [star.to_dict() for star in self.stars],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def memory_beacons(self) -> List[Dict[str, str]]:
        """Serialise each star into a wallet-label-friendly payload."""

        return [
            {"label": star.star_id, "payload": star.wallet_payload()} for star in self.stars
        ]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalise_timestamp(timestamp: Optional[int]) -> datetime:
    """Return a timezone-aware UTC datetime for ``timestamp``.

    ``timestamp`` may be supplied in seconds or nanoseconds.  ``None`` falls
    back to ``time.time``.
    """

    if timestamp is None:
        ts = time.time()
    else:
        ts = timestamp
        if timestamp > 1_000_000_000_000:  # treat values as nanoseconds
            ts = timestamp / 1_000_000_000
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def _angle_and_radius(seed: str, base_radius: float) -> Tuple[float, float]:
    digest = sha256(seed.encode("utf-8")).digest()
    angle = int.from_bytes(digest[:8], "big") / 2**64 * tau
    radius = base_radius + digest[8] / 255.0 * 0.3
    return angle, radius


def _scaled_pulse(seed: str, base: StarPulse) -> StarPulse:
    digest = sha256(seed.encode("utf-8")).digest()
    joy_scale = 0.7 + digest[0] / 255.0 * 0.3
    rage_scale = 0.4 + digest[1] / 255.0 * 0.4
    curiosity_scale = 0.6 + digest[2] / 255.0 * 0.35
    return StarPulse(
        joy=round(min(1.0, base.joy * joy_scale), 6),
        rage=round(min(1.0, base.rage * rage_scale), 6),
        curiosity=round(min(1.0, base.curiosity * curiosity_scale), 6),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_constellation(
    manifest: EchoManifest,
    *,
    timestamp: Optional[int] = None,
    glyph_cycle: Optional[Iterable[str]] = None,
) -> ConstellationFrame:
    """Construct a :class:`ConstellationFrame` from the supplied manifest."""

    generated_at = _normalise_timestamp(timestamp).isoformat().replace("+00:00", "Z")
    base_pulse = StarPulse(
        joy=manifest.evolver.joy,
        rage=manifest.evolver.rage,
        curiosity=manifest.evolver.curiosity,
    )

    glyphs = list(glyph_cycle or manifest.glyphs or "∇")
    if not glyphs:
        glyphs = list(manifest.glyphs or "∇")

    cycle = manifest.evolver.cycle
    stars: List[ConstellationStar] = []

    core_star = ConstellationStar(
        star_id=f"cycle-{cycle}-core",
        glyph=glyphs[0],
        cycle=cycle,
        orbital_index=0,
        propagation_channels=manifest.evolver.propagation_channels,
        coordinates=(0.0, 0.0),
        pulse=base_pulse,
        metadata={
            "narrative_excerpt": manifest.narrative_excerpt,
            "mythocode": "; ".join(manifest.mythocode) if manifest.mythocode else "∅",
        },
    )
    if manifest.oam_vortex:
        core_star.verification.append(
            StarVerification(label="OAM Vortex", reference=manifest.oam_vortex)
        )
    if manifest.evolver.vault_key_preview:
        core_star.verification.append(
            StarVerification(
                label="Vault Key", reference=manifest.evolver.vault_key_preview
            )
        )
    stars.append(core_star)

    for index, key in enumerate(manifest.keys, start=1):
        seed = f"{key.fingerprint}:{cycle}:{index}"
        angle, radius = _angle_and_radius(seed, 1.0 + index * 0.4)
        coordinates = (round(radius * cos(angle), 6), round(radius * sin(angle), 6))
        glyph = glyphs[index % len(glyphs)]
        scaled = _scaled_pulse(seed, base_pulse)
        verification = [
            StarVerification(label=chain, reference=addr)
            for chain, addr in sorted(key.addresses.items())
        ]
        metadata = {
            "fingerprint": key.fingerprint,
            "short_fingerprint": key.short_fingerprint,
        }
        star = ConstellationStar(
            star_id=f"cycle-{cycle}-key-{index}",
            glyph=glyph,
            cycle=cycle,
            orbital_index=index,
            propagation_channels=manifest.evolver.propagation_channels,
            coordinates=coordinates,
            pulse=scaled,
            verification=verification,
            metadata=metadata,
        )
        stars.append(star)

    frame = ConstellationFrame(
        anchor=manifest.anchor,
        cycle=cycle,
        generated_at=generated_at,
        stars=stars,
        mythocode=list(manifest.mythocode),
        narrative_excerpt=manifest.narrative_excerpt,
        oam_vortex=manifest.oam_vortex,
    )
    return frame

