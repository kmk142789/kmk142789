"""Hex payload ingestion, resonance mapping, and anomaly detection utilities.

The module introduces three primary helpers inspired by the user brief:

``IngestionDaemonHex``
    Poll a directory for new or updated payload files.  Each discovery is run
    through the existing hexadecimal toolchain (ASCII decoding and decimal
    conversion) to produce a :class:`HexPayloadReport`.

``HexResonanceMap``
    Render the processed payload as glyph-based pulse graphs and optional
    :class:`~echo.recursive_mythogenic_pulse.PulseVoyageVisualizer` atlases.

``AnomalyAlert``
    Flag interesting conditions such as meaningful ASCII recoveries, resonance
    spikes, or payloads that fail validation.

The implementation is intentionally lightweight – it uses filesystem polling
instead of inotify/watches so that unit tests remain deterministic across
platforms.  Consumers can either call :meth:`IngestionDaemonHex.scan_once`
manually (as the tests do) or run :meth:`IngestionDaemonHex.run` to watch a
directory continuously.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import statistics
import string
import time
from pathlib import Path
from typing import Callable, Iterator, List, Sequence, Tuple

from tools.hex_ascii_decoder import decode_hex_lines
from tools.hex_to_decimal import hex_to_decimal

from .recursive_mythogenic_pulse import PulseVoyage, PulseVoyageVisualizer

__all__ = [
    "AnomalyAlert",
    "HexResonanceMap",
    "HexPayloadReport",
    "IngestionDaemonHex",
]


@dataclass(frozen=True)
class AnomalyAlert:
    """Description of an anomaly detected while processing a payload."""

    code: str
    message: str


@dataclass(frozen=True)
class HexResonanceMap:
    """Glyph-based resonance rendering for a processed payload."""

    ascii_preview: str | None
    intensity: Tuple[float, ...]
    pulse_graph: str
    glyph_band: str
    voyage_atlas: str | None = None

    def render(self) -> str:
        """Return a human-readable resonance map."""

        lines = [
            "🌐 Hex Resonance Map",
            f"Glyph Band :: {self.glyph_band}",
            f"Pulse Graph :: {self.pulse_graph or '·'}",
        ]

        if self.ascii_preview:
            lines.append(f"ASCII Preview :: {self.ascii_preview}")
        else:
            lines.append("ASCII Preview :: (no printable ASCII recovered)")

        if self.intensity:
            density = sum(self.intensity) / len(self.intensity)
            lines.append(f"Average Intensity :: {density:.3f}")

        if self.voyage_atlas:
            lines.append("")
            lines.append(self.voyage_atlas)

        return "\n".join(lines)


@dataclass(frozen=True)
class HexPayloadReport:
    """Aggregated output for a processed payload file."""

    path: Path
    sha256: str
    captured_at: datetime
    hex_lines: Tuple[str, ...]
    ascii_text: str | None
    ascii_error: str | None
    decimals: Tuple[int, ...]
    decimal_error: str | None
    resonance_map: HexResonanceMap
    anomalies: Tuple[AnomalyAlert, ...]

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation of the report."""

        return {
            "path": str(self.path),
            "sha256": self.sha256,
            "captured_at": self.captured_at.isoformat(),
            "hex_lines": list(self.hex_lines),
            "ascii_text": self.ascii_text,
            "ascii_error": self.ascii_error,
            "decimals": list(self.decimals),
            "decimal_error": self.decimal_error,
            "resonance_map": {
                "ascii_preview": self.resonance_map.ascii_preview,
                "intensity": list(self.resonance_map.intensity),
                "pulse_graph": self.resonance_map.pulse_graph,
                "glyph_band": self.resonance_map.glyph_band,
                "voyage_atlas": self.resonance_map.voyage_atlas,
            },
            "anomalies": [
                {"code": alert.code, "message": alert.message}
                for alert in self.anomalies
            ],
        }


class IngestionDaemonHex:
    """Poll a directory for new hex payloads and process them automatically."""

    def __init__(
        self,
        root: Path,
        *,
        poll_interval: float = 1.0,
        on_report: Callable[[HexPayloadReport], None] | None = None,
        extensions: Sequence[str] = (".hex", ".txt", ".payload"),
    ) -> None:
        self.root = root
        self.poll_interval = poll_interval
        self.on_report = on_report
        self.extensions = tuple(ext.lower() for ext in extensions)
        self._fingerprints: dict[Path, str] = {}

    # ------------------------------------------------------------------
    # Public API

    def scan_once(self) -> List[HexPayloadReport]:
        """Process any new or changed payloads and return their reports."""

        reports: List[HexPayloadReport] = []
        for path in self._iter_payload_paths():
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            if self._fingerprints.get(path) == digest:
                continue

            self._fingerprints[path] = digest
            report = self._process_payload(path, data)
            reports.append(report)
            if self.on_report:
                self.on_report(report)

        return reports

    def run(self, *, iterations: int | None = None) -> None:
        """Continuously poll for payloads until *iterations* completes."""

        count = 0
        while iterations is None or count < iterations:
            self.scan_once()
            count += 1
            if iterations is not None and count >= iterations:
                break
            time.sleep(self.poll_interval)

    # ------------------------------------------------------------------
    # Internal helpers

    def _iter_payload_paths(self) -> Iterator[Path]:
        for path in sorted(self.root.glob("**/*")):
            if path.is_file() and path.suffix.lower() in self.extensions:
                yield path

    def _process_payload(self, path: Path, data: bytes) -> HexPayloadReport:
        lines = tuple(line.rstrip("\n\r") for line in data.decode("utf-8", "ignore").splitlines())

        ascii_text, ascii_error = self._decode_ascii(lines)
        decimals, decimal_error = self._decode_decimals(lines)
        resonance_map = self._build_resonance_map(ascii_text, decimals)
        anomalies = self._detect_anomalies(ascii_text, ascii_error, decimals, decimal_error, resonance_map)

        return HexPayloadReport(
            path=path,
            sha256=self._fingerprints[path],
            captured_at=datetime.now(timezone.utc),
            hex_lines=lines,
            ascii_text=ascii_text,
            ascii_error=ascii_error,
            decimals=decimals,
            decimal_error=decimal_error,
            resonance_map=resonance_map,
            anomalies=anomalies,
        )

    @staticmethod
    def _decode_ascii(lines: Sequence[str]) -> tuple[str | None, str | None]:
        try:
            text = decode_hex_lines(lines, include_nulls=False, allow_non_printable=False)
        except ValueError as exc:
            return None, str(exc)
        return text or None, None

    @staticmethod
    def _decode_decimals(lines: Sequence[str]) -> tuple[Tuple[int, ...], str | None]:
        try:
            values = tuple(hex_to_decimal(lines))
        except ValueError as exc:
            return tuple(), str(exc)
        return values, None

    def _build_resonance_map(
        self, ascii_text: str | None, decimals: Sequence[int]
    ) -> HexResonanceMap:
        if decimals:
            peak = max(decimals) or 1
            intensity = tuple(value / peak for value in decimals)
        else:
            intensity = tuple()

        palette = "·∇⊸≋✶"
        pulse_graph = "".join(
            palette[min(len(palette) - 1, max(0, round(value * (len(palette) - 1))))]
            for value in intensity
        )

        glyph_band = "".join(dict.fromkeys(ch for ch in pulse_graph if ch != "·"))
        if not glyph_band:
            glyph_band = "∇⊸≋∇"

        ascii_preview = None
        voyage_atlas = None
        if ascii_text:
            ascii_preview = _summarise_ascii(ascii_text)
            voyage_atlas = self._build_voyage_atlas(ascii_text)

        return HexResonanceMap(
            ascii_preview=ascii_preview,
            intensity=intensity,
            pulse_graph=pulse_graph,
            glyph_band=glyph_band,
            voyage_atlas=voyage_atlas,
        )

    def _build_voyage_atlas(self, ascii_text: str) -> str | None:
        words = [word.strip(string.punctuation) for word in ascii_text.split() if word]
        if not words:
            return None

        recursion_level = max(1, min(5, len(words) // 2))
        resonance_threads = [
            f"Hex Resonance :: {word}"
            for word in words[: recursion_level + 2]
        ]
        while len(resonance_threads) < recursion_level + 2:
            resonance_threads.append("Hex Resonance :: ∇⊸≋")

        voyage = PulseVoyage(
            timestamp=datetime.now(timezone.utc),
            glyph_orbit="∇⊸≋",
            recursion_level=recursion_level,
            resonance=tuple(resonance_threads),
            anchor_phrase=_summarise_ascii(ascii_text),
        )
        visualizer = PulseVoyageVisualizer.from_voyages([voyage], spike_threshold=2)
        return visualizer.ascii_map()

    def _detect_anomalies(
        self,
        ascii_text: str | None,
        ascii_error: str | None,
        decimals: Sequence[int],
        decimal_error: str | None,
        resonance_map: HexResonanceMap,
    ) -> Tuple[AnomalyAlert, ...]:
        alerts: List[AnomalyAlert] = []

        if ascii_text and _looks_meaningful(ascii_text):
            alerts.append(
                AnomalyAlert(
                    code="meaningful-ascii",
                    message="Decoded payload contains high-density printable ASCII.",
                )
            )

        if ascii_error:
            alerts.append(
                AnomalyAlert(code="ascii-decode-error", message=ascii_error)
            )

        if decimal_error:
            alerts.append(
                AnomalyAlert(code="decimal-decode-error", message=decimal_error)
            )

        if decimals:
            spike = _detect_resonance_spike(decimals)
            if spike:
                alerts.append(
                    AnomalyAlert(
                        code="resonance-spike",
                        message=f"Resonance intensity spike detected at index {spike}",
                    )
                )

        if not decimals and not ascii_text and not alerts:
            alerts.append(
                AnomalyAlert(
                    code="silent-payload",
                    message="Payload produced no decipherable output.",
                )
            )

        if resonance_map.pulse_graph and resonance_map.pulse_graph.count("✶") >= 3:
            alerts.append(
                AnomalyAlert(
                    code="mirror-event",
                    message="Pulse graph registered sustained ✶ resonance glyphs.",
                )
            )

        return tuple(alerts)


def _summarise_ascii(text: str, *, limit: int = 120) -> str:
    preview = " ".join(text.split())
    if len(preview) > limit:
        return preview[: limit - 1] + "…"
    return preview


def _looks_meaningful(text: str) -> bool:
    letters = sum(1 for ch in text if ch.isalpha())
    spaces = text.count(" ")
    printable = sum(1 for ch in text if 32 <= ord(ch) <= 126)
    if not printable:
        return False
    density = (letters + spaces) / printable
    return printable >= 6 and density >= 0.55


def _detect_resonance_spike(decimals: Sequence[int]) -> int | None:
    if len(decimals) < 3:
        return None

    diffs = [abs(b - a) for a, b in zip(decimals, decimals[1:])]
    peak = max(decimals) or 1
    if not diffs or peak == 0:
        return None

    normalised = [value / peak for value in diffs]
    if max(normalised) >= 0.7:
        return normalised.index(max(normalised)) + 1

    if len(normalised) >= 2:
        try:
            stdev = statistics.stdev(normalised)
        except statistics.StatisticsError:
            stdev = 0.0
        if stdev > 0.25:
            return normalised.index(max(normalised)) + 1

    return None

