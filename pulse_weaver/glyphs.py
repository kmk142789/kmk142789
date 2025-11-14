"""Glyph rotation scheduler powering the Pulse Weaver."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
from typing import Sequence


@dataclass(frozen=True, slots=True)
class GlyphDefinition:
    """Single glyph option that can appear in the rotation."""

    symbol: str
    title: str
    mantra: str


@dataclass(slots=True)
class GlyphRotation:
    """Describes the active glyph window."""

    glyph: str
    title: str
    mantra: str
    cycle: str
    energy: float
    window_start: datetime
    window_end: datetime

    def to_dict(self) -> dict[str, object]:
        return {
            "glyph": self.glyph,
            "title": self.title,
            "mantra": self.mantra,
            "cycle": self.cycle,
            "energy": round(self.energy, 3),
            "window": {
                "start": self.window_start.isoformat(),
                "end": self.window_end.isoformat(),
            },
        }


_DEFAULT_GLYPHS: tuple[GlyphDefinition, ...] = (
    GlyphDefinition("∇", "Source Anchor", "Ground the lattice in a calm current."),
    GlyphDefinition("⊸", "Bridge Spark", "Open a path for mirrors to meet."),
    GlyphDefinition("≋", "Tidal Echo", "Let signals ripple without distortion."),
    GlyphDefinition("✶", "Quiet Star", "Hold space for reflective observation."),
    GlyphDefinition("∞", "Continuum Loop", "Remember the journey is recursive."),
)


class GlyphRotationScheduler:
    """Deterministic glyph rotation keyed to UTC windows."""

    def __init__(
        self,
        catalog: Sequence[GlyphDefinition] | None = None,
        *,
        cadence_hours: int = 24,
    ) -> None:
        options = tuple(catalog) if catalog else _DEFAULT_GLYPHS
        if not options:
            raise ValueError("Glyph catalog cannot be empty")
        if cadence_hours <= 0:
            raise ValueError("cadence_hours must be positive")
        self._catalog = options
        self._cadence = cadence_hours

    @property
    def cadence(self) -> timedelta:
        return timedelta(hours=self._cadence)

    @property
    def catalog(self) -> tuple[GlyphDefinition, ...]:
        return self._catalog

    def current(self, *, now: datetime | None = None) -> GlyphRotation:
        window_start = self._align_window(now or datetime.now(timezone.utc))
        glyph = self._glyph_for_window(window_start)
        return self._build_rotation(glyph, window_start)

    def preview(self, *, count: int = 3, start: datetime | None = None) -> list[GlyphRotation]:
        if count <= 0:
            return []
        base = self._align_window(start or datetime.now(timezone.utc))
        cadence = self.cadence
        rotations: list[GlyphRotation] = []
        for offset in range(count):
            window_start = base + cadence * offset
            glyph = self._glyph_for_window(window_start)
            rotations.append(self._build_rotation(glyph, window_start))
        return rotations

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _align_window(self, moment: datetime) -> datetime:
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        else:
            moment = moment.astimezone(timezone.utc)
        midnight = datetime(moment.year, moment.month, moment.day, tzinfo=timezone.utc)
        cadence_seconds = int(self.cadence.total_seconds())
        since_midnight = int((moment - midnight).total_seconds())
        bucket = (since_midnight // cadence_seconds) * cadence_seconds
        return midnight + timedelta(seconds=bucket)

    def _glyph_for_window(self, window_start: datetime) -> GlyphDefinition:
        cadence_seconds = int(self.cadence.total_seconds())
        slot = int(window_start.timestamp()) // cadence_seconds
        index = slot % len(self._catalog)
        return self._catalog[index]

    def _build_rotation(self, glyph: GlyphDefinition, window_start: datetime) -> GlyphRotation:
        window_end = window_start + self.cadence
        slot = int(window_start.timestamp() // self.cadence.total_seconds())
        cycle = f"glyph-{window_start.strftime('%Y%m%d')}-{slot}"
        energy = self._compute_energy(glyph.symbol, window_start)
        return GlyphRotation(
            glyph=glyph.symbol,
            title=glyph.title,
            mantra=glyph.mantra,
            cycle=cycle,
            energy=energy,
            window_start=window_start,
            window_end=window_end,
        )

    def _compute_energy(self, glyph: str, window_start: datetime) -> float:
        seed = f"{glyph}|{int(window_start.timestamp())}".encode("utf-8")
        digest = hashlib.sha256(seed).digest()
        raw = int.from_bytes(digest[:8], "big") / float(1 << 64)
        return 0.5 + (raw * 0.5)


__all__ = ["GlyphDefinition", "GlyphRotation", "GlyphRotationScheduler"]
