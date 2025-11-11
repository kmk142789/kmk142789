"""High-level helper for consuming Pulse Dashboard datasets."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


def _coerce_sequence(value: object) -> Sequence[Mapping[str, object]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [item for item in value if isinstance(item, Mapping)]  # type: ignore[return-value]
    return []


@dataclass(slots=True)
class PulseDashboardClient:
    """Convenience façade around the aggregated dashboard payload."""

    payload: Mapping[str, object]
    source_path: Path | None = None

    @classmethod
    def from_file(cls, path: Path | str) -> "PulseDashboardClient":
        candidate = Path(path)
        payload = json.loads(candidate.read_text(encoding="utf-8"))
        return cls(payload=payload, source_path=candidate)

    # ------------------------------------------------------------------
    # Pulse helpers

    def total_pulses(self) -> int:
        pulses = _coerce_sequence(self.payload.get("pulses"))
        return len(pulses)

    def pulse_categories(self, *, limit: int = 5) -> list[tuple[str, int]]:
        summary = self.payload.get("pulse_summary")
        if isinstance(summary, Mapping):
            categories = summary.get("categories")
            if isinstance(categories, Sequence):
                results: list[tuple[str, int]] = []
                for item in categories[:limit]:
                    if not isinstance(item, Mapping):
                        continue
                    name = str(item.get("name", ""))
                    try:
                        count = int(item.get("count", 0))
                    except (TypeError, ValueError):
                        continue
                    results.append((name, count))
                if results:
                    return results

        pulses = _coerce_sequence(self.payload.get("pulses"))
        counts: dict[str, int] = {}
        for entry in pulses:
            category = str(entry.get("category", "pulse"))
            counts[category] = counts.get(category, 0) + 1
        return sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]

    def latest_pulse_message(self) -> str | None:
        pulses = _coerce_sequence(self.payload.get("pulses"))
        if not pulses:
            return None
        first = pulses[0]
        message = first.get("message")
        return str(message) if isinstance(message, str) else None

    def average_pulse_wave(self) -> float:
        summary = self.payload.get("pulse_summary")
        if isinstance(summary, Mapping):
            value = summary.get("average_wave")
            try:
                return round(float(value), 2)
            except (TypeError, ValueError):
                pass
        pulses = _coerce_sequence(self.payload.get("pulses"))
        if not pulses:
            return 0.0
        total = 0.0
        for entry in pulses:
            try:
                total += float(entry.get("wave", 0.0))
            except (TypeError, ValueError):
                continue
        return round(total / len(pulses), 2) if pulses else 0.0

    # ------------------------------------------------------------------
    # Amplify helpers

    def amplify_momentum(self) -> float | None:
        amplify = self.payload.get("amplify")
        if not isinstance(amplify, Mapping):
            return None
        summary = amplify.get("summary", {})
        if isinstance(summary, Mapping):
            value = summary.get("momentum")
            if value is None:
                return None
            try:
                return round(float(value), 2)
            except (TypeError, ValueError):
                return None
        return None

    def amplify_history(self, *, limit: int = 3) -> list[Mapping[str, object]]:
        amplify = self.payload.get("amplify")
        if not isinstance(amplify, Mapping):
            return []
        history = amplify.get("history")
        if isinstance(history, Sequence):
            return [entry for entry in history[:limit] if isinstance(entry, Mapping)]
        latest = amplify.get("latest")
        return [latest] if isinstance(latest, Mapping) else []

    # ------------------------------------------------------------------
    # Worker hive helpers

    def recent_worker_events(self, *, limit: int = 5) -> list[Mapping[str, object]]:
        hive = self.payload.get("worker_hive")
        if not isinstance(hive, Mapping):
            return []
        events = hive.get("events")
        if isinstance(events, Sequence):
            return [entry for entry in events[:limit] if isinstance(entry, Mapping)]
        return []

    # ------------------------------------------------------------------

    def glyph_energy(self) -> float:
        glyph_cycle = self.payload.get("glyph_cycle")
        if isinstance(glyph_cycle, Mapping):
            try:
                return round(float(glyph_cycle.get("energy", 0.0)), 2)
            except (TypeError, ValueError):
                return 0.0
        return 0.0

    def attestation_ids(self) -> list[str]:
        attestations = _coerce_sequence(self.payload.get("attestations"))
        ids: list[str] = []
        for entry in attestations:
            value = entry.get("id")
            if isinstance(value, str):
                ids.append(value)
        return ids

    def proof_count(self) -> int:
        proof = self.payload.get("proof_of_computation")
        if not isinstance(proof, Mapping):
            return 0
        try:
            return int(proof.get("total", 0))
        except (TypeError, ValueError):
            return 0

    def describe(self) -> str:
        """Return a multi-line textual summary for quick inspection."""

        parts = [
            f"Pulse Dashboard :: pulses={self.total_pulses()} attestations={len(self.attestation_ids())}",
            f"Glyph energy: {self.glyph_energy():.2f} :: Amplify momentum: {self.amplify_momentum()}",
            "Categories: "
            + ", ".join(f"{name}({count})" for name, count in self.pulse_categories(limit=3)),
        ]
        latest = self.latest_pulse_message()
        if latest:
            parts.append(f"Latest pulse: {latest}")
        return "\n".join(parts)


__all__ = ["PulseDashboardClient"]
