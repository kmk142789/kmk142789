"""Aggregate Echo signals into the Pulse Dashboard dataset."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

from echo.proof_of_computation import load_proof_ledger

from .impact_explorer import ImpactExplorerBuilder
from .loop_health import LoopHealthCollector


@dataclass(slots=True)
class PulseDashboardPaths:
    """Convenience container for dashboard-related filesystem paths."""

    root: Path

    @property
    def pulse_history(self) -> Path:
        return self.root / "pulse_history.json"

    @property
    def attestation_dir(self) -> Path:
        return self.root / "attestations"

    @property
    def dns_tokens(self) -> Path:
        return self.root / "dns_tokens.txt"

    @property
    def worker_state_dir(self) -> Path:
        return self.root / "state" / "pulse_dashboard"

    @property
    def worker_log(self) -> Path:
        return self.worker_state_dir / "worker_events.jsonl"

    @property
    def amplify_log(self) -> Path:
        return self.root / "state" / "amplify_log.jsonl"

    @property
    def output_dir(self) -> Path:
        return self.root / "pulse_dashboard" / "data"

    @property
    def output_path(self) -> Path:
        return self.output_dir / "dashboard.json"


class PulseDashboardBuilder:
    """Construct a synthesised dashboard view of the Echo ecosystem."""

    def __init__(self, project_root: Path | str | None = None) -> None:
        root = Path(project_root or Path.cwd()).resolve()
        self._paths = PulseDashboardPaths(root=root)
        self._paths.output_dir.mkdir(parents=True, exist_ok=True)
        self._paths.worker_state_dir.mkdir(parents=True, exist_ok=True)

    def build(self) -> dict[str, object]:
        """Collect the latest pulse, attestation, DNS, and worker signals."""

        payload: dict[str, object] = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "pulses": self._load_pulses(),
            "attestations": self._load_attestations(),
            "dns_snapshots": self._load_dns_snapshots(),
            "worker_hive": self._load_worker_events(),
        }
        payload["amplify"] = self._load_amplify_snapshots()
        payload["impact_explorer"] = ImpactExplorerBuilder(self._paths.root).build()
        payload["loop_health"] = LoopHealthCollector(self._paths.root).collect()
        payload["glyph_cycle"] = self._build_glyph_cycle(payload)
        payload["pulse_summary"] = self._summarize_pulses(payload["pulses"])
        payload["signal_health"] = self._assess_signal_health(payload)
        payload["proof_of_computation"] = self._load_proof_of_computation()
        return payload

    def write(self, data: Mapping[str, object] | None = None, *, path: Path | str | None = None) -> Path:
        """Serialise *data* to disk and return the output path."""

        target = Path(path or self._paths.output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = data or self.build()
        target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return target

    # ------------------------------------------------------------------
    # Pulse aggregation helpers

    _pulse_category_pattern = re.compile(r"^[^A-Za-z0-9]*([A-Za-z0-9_-]+)")

    def _load_pulses(self) -> list[dict[str, object]]:
        path = self._paths.pulse_history
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        pulses: list[dict[str, object]] = []
        for entry in data:
            try:
                ts = datetime.fromtimestamp(float(entry["timestamp"]), tz=timezone.utc)
            except (KeyError, TypeError, ValueError):
                continue
            message = str(entry.get("message", ""))
            digest = str(entry.get("hash", ""))
            category = self._classify_pulse(message)
            glyph = self._derive_glyph(message, digest)
            pulses.append(
                {
                    "timestamp": ts.isoformat(),
                    "message": message,
                    "hash": digest,
                    "category": category,
                    "wave": self._calculate_wave(message, digest),
                    "glyph": glyph,
                }
            )
        pulses.sort(key=lambda item: item["timestamp"], reverse=True)
        return pulses

    def _summarize_pulses(self, pulses: list[dict[str, object]]) -> dict[str, object]:
        if not pulses:
            return {"total": 0, "categories": [], "average_wave": 0.0}

        category_counts: dict[str, int] = {}
        wave_total = 0.0
        valid_entries = 0
        for entry in pulses:
            category = str(entry.get("category", "pulse"))
            category_counts[category] = category_counts.get(category, 0) + 1
            try:
                wave_total += float(entry.get("wave", 0.0))
                valid_entries += 1
            except (TypeError, ValueError):
                continue

        average_wave = round(wave_total / valid_entries, 2) if valid_entries else 0.0
        categories = [
            {"name": name, "count": count, "share": round(count / len(pulses), 3)}
            for name, count in sorted(category_counts.items(), key=lambda item: item[1], reverse=True)
        ]

        latest = pulses[0]
        summary = {
            "total": len(pulses),
            "categories": categories[:10],
            "average_wave": average_wave,
            "latest": {
                "message": latest.get("message"),
                "timestamp": latest.get("timestamp"),
                "glyph": latest.get("glyph"),
            },
        }
        return summary

    def _classify_pulse(self, message: str) -> str:
        match = self._pulse_category_pattern.search(message.strip())
        if not match:
            return "pulse"
        return match.group(1).lower()

    def _derive_glyph(self, message: str, digest: str) -> str:
        seed = f"{message}:{digest}".encode("utf-8")
        anchors = ["∇", "⊸", "≋", "∞", "⚡"]
        glyphs = []
        for index, byte in enumerate(seed[:8]):
            glyphs.append(anchors[(byte + index) % len(anchors)])
        return "".join(glyphs)

    def _calculate_wave(self, message: str, digest: str) -> float:
        combined = sum(ord(ch) for ch in message) + sum(ord(ch) for ch in digest)
        return float(combined % 360)

    # ------------------------------------------------------------------
    # Attestation aggregation helpers

    def _load_attestations(self) -> list[dict[str, object]]:
        directory = self._paths.attestation_dir
        if not directory.exists():
            return []
        attestations: list[dict[str, object]] = []
        for candidate in sorted(directory.glob("*.json")):
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            metadata: dict[str, object] = {}
            for key, value in data.items():
                if key in {"message", "created_at", "hash_sha256", "sha256"}:
                    continue
                if isinstance(value, str) and len(value) > 160:
                    continue
                metadata[key] = value
            entry = {
                "id": candidate.stem,
                "path": str(candidate.relative_to(self._paths.root)),
                "message": data.get("message", ""),
                "created_at": data.get("created_at"),
                "hash": data.get("hash_sha256") or data.get("sha256") or "",
                "metadata": metadata,
            }
            attestations.append(entry)
        attestations.sort(key=lambda item: item.get("created_at") or item["id"], reverse=True)
        return attestations[:100]

    # ------------------------------------------------------------------
    # DNS snapshot helpers

    def _load_dns_snapshots(self) -> list[dict[str, str]]:
        path = self._paths.dns_tokens
        if not path.exists():
            return []
        snapshots: list[dict[str, str]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            cleaned = line.strip()
            if not cleaned or "=" not in cleaned:
                continue
            domain, token = cleaned.split("=", 1)
            snapshots.append({"domain": domain.strip(), "token": token.strip()})
        return snapshots

    # ------------------------------------------------------------------
    # Worker hive helpers

    def _load_worker_events(self) -> dict[str, object]:
        path = self._paths.worker_log
        if not path.exists():
            return {"events": [], "total": 0}
        events: list[dict[str, object]] = []
        for raw in path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            events.append(data)
        events.sort(key=lambda item: item.get("timestamp", ""), reverse=True)
        return {"events": events, "total": len(events)}

    # ------------------------------------------------------------------
    # Proof-of-Computation bridge

    def _load_proof_of_computation(self) -> dict[str, object]:
        path = self._paths.output_dir / "proof_of_computation.json"
        records = load_proof_ledger(path)
        latest = records[0] if records else None
        return {
            "total": len(records),
            "latest": latest,
            "records": records[:50],
        }

    # ------------------------------------------------------------------

    def _load_amplify_snapshots(self) -> dict[str, object]:
        path = self._paths.amplify_log
        if not path.exists():
            return {"history": [], "latest": None, "summary": {"cycles_tracked": 0}}

        raw_entries = path.read_text(encoding="utf-8").splitlines()
        snapshots: list[dict[str, object]] = []
        for raw in raw_entries:
            raw = raw.strip()
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            try:
                cycle = int(data.get("cycle", 0))
            except (TypeError, ValueError):
                continue

            try:
                index_value = float(data.get("index", 0.0))
            except (TypeError, ValueError):
                index_value = 0.0

            timestamp_raw = data.get("timestamp")
            timestamp_iso = None
            sort_dt = None
            if isinstance(timestamp_raw, str):
                iso_source = timestamp_raw.replace("Z", "+00:00")
                try:
                    sort_dt = datetime.fromisoformat(iso_source)
                    timestamp_iso = sort_dt.isoformat()
                except ValueError:
                    timestamp_iso = timestamp_raw
            if sort_dt is None:
                sort_dt = datetime.fromtimestamp(0, tz=timezone.utc)

            metrics_payload: dict[str, float | object] = {}
            metrics = data.get("metrics", {})
            if isinstance(metrics, Mapping):
                for key, value in metrics.items():
                    try:
                        metrics_payload[str(key)] = round(float(value), 2)
                    except (TypeError, ValueError):
                        metrics_payload[str(key)] = value

            entry: dict[str, object] = {
                "cycle": cycle,
                "index": round(index_value, 2),
                "commit_sha": str(data.get("commit_sha", "")),
                "timestamp": timestamp_iso or timestamp_raw,
                "metrics": metrics_payload,
                "_sort_key": (sort_dt, cycle),
            }
            snapshots.append(entry)

        if not snapshots:
            return {"history": [], "latest": None, "summary": {"cycles_tracked": 0}}

        snapshots.sort(key=lambda item: item["_sort_key"], reverse=True)
        for entry in snapshots:
            entry.pop("_sort_key", None)

        history = snapshots[:50]
        latest = history[0]

        indices: list[float] = []
        for entry in history:
            value = entry.get("index")
            if isinstance(value, (int, float)):
                indices.append(float(value))
        summary: dict[str, object] = {"cycles_tracked": len(snapshots)}
        if indices:
            avg_index = sum(indices) / len(indices)
            summary["average_index"] = round(avg_index, 2)
            summary["peak_index"] = round(max(indices), 2)
            if len(indices) >= 2:
                deltas = [round(indices[i] - indices[i + 1], 4) for i in range(len(indices) - 1)]
                summary["momentum"] = round(deltas[0], 2)
                direction, streak, stability = self._diagnose_amplify_trend(indices[0], deltas)
                summary["trend"] = direction
                summary["streak_length"] = streak
                summary["stability"] = stability
                summary["volatility"] = self._amplify_volatility(indices)
                summary["presence_score"] = self._presence_score(indices[0], deltas[0], streak, stability)
            else:
                summary["trend"] = "steady"
                summary["streak_length"] = 0
                summary["stability"] = 1.0
                summary["volatility"] = 0.0
                summary["presence_score"] = round(indices[0], 2)
        summary.setdefault("trend", "steady")
        summary.setdefault("streak_length", 0)
        summary.setdefault("stability", 1.0)
        summary.setdefault("volatility", 0.0)
        summary.setdefault("presence_score", 0.0)
        summary["latest_commit"] = latest.get("commit_sha")
        summary["presence"] = self._format_presence_message(latest, summary)

        return {"history": history, "latest": latest, "summary": summary}

    # ------------------------------------------------------------------

    def _build_glyph_cycle(self, payload: Mapping[str, object]) -> dict[str, object]:
        pulses = payload.get("pulses", [])
        attestations = payload.get("attestations", [])
        if not isinstance(pulses, Iterable) or not isinstance(attestations, Iterable):
            return {"energy": 0.0, "cycles": []}
        wave_total = sum(float(item.get("wave", 0.0)) for item in pulses if isinstance(item, Mapping))
        attn_total = len(attestations)
        energy = (wave_total / 360.0) + attn_total * 0.5
        cycles = [
            {
                "label": "pulse-wave",
                "value": round(wave_total % 360, 2),
            },
            {
                "label": "attestation-glyph",
                "value": attn_total,
            },
        ]
        return {"energy": round(energy, 2), "cycles": cycles}

    def _diagnose_amplify_trend(
        self,
        latest_index: float,
        deltas: list[float],
    ) -> tuple[str, int, float]:
        """Return a tuple describing trend direction, streak length, and stability.

        ``deltas`` is expected to be ordered from newest change to oldest.
        """

        if not deltas:
            return ("steady", 0, 1.0)

        tolerance = 0.05
        first_delta = deltas[0]
        if abs(first_delta) <= tolerance:
            direction = "steady"
        else:
            direction = "rising" if first_delta > 0 else "cooling"

        streak = 0
        for delta in deltas:
            if abs(delta) <= tolerance:
                if direction == "steady":
                    streak += 1
                    continue
                break
            if direction == "steady":
                direction = "rising" if delta > 0 else "cooling"
                streak = 1
                continue
            if direction == "rising" and delta > tolerance:
                streak += 1
                continue
            if direction == "cooling" and delta < -tolerance:
                streak += 1
                continue
            break

        # Stability is inversely related to volatility of the first few deltas.
        window = deltas[: min(4, len(deltas))]
        if not window:
            stability = 1.0
        else:
            avg_change = sum(abs(delta) for delta in window) / len(window)
            # Higher average change means lower stability. Clamp between 0 and 1.
            stability = max(0.0, min(1.0, 1.0 - (avg_change / max(abs(latest_index), 1.0))))

        return (direction, streak, round(stability, 3))

    def _amplify_volatility(self, indices: list[float]) -> float:
        if len(indices) < 2:
            return 0.0
        mean = sum(indices) / len(indices)
        variance = sum((value - mean) ** 2 for value in indices) / len(indices)
        return round(variance ** 0.5, 3)

    def _presence_score(
        self,
        latest_index: float,
        momentum: float,
        streak: int,
        stability: float,
    ) -> float:
        baseline = max(latest_index, 0.0)
        directional_bonus = max(momentum, 0.0)
        streak_bonus = streak * 0.75
        stability_bonus = stability * 2.0
        return round(baseline + directional_bonus + streak_bonus + stability_bonus, 2)

    def _format_presence_message(
        self,
        latest: Mapping[str, object],
        summary: Mapping[str, object],
    ) -> str:
        cycle = latest.get("cycle")
        index_value = latest.get("index")
        trend = summary.get("trend", "steady")

        if isinstance(index_value, (int, float)):
            return (
                f"Amplify presence cycle {cycle} :: index {float(index_value):.2f}"
                f" :: {trend}"
            )
        return f"Amplify presence cycle {cycle} :: {trend}"

    # ------------------------------------------------------------------
    # Signal health intelligence

    def _assess_signal_health(self, payload: Mapping[str, object]) -> dict[str, object]:
        pulses = payload.get("pulses", [])
        attestations = payload.get("attestations", [])
        pulse_summary = payload.get("pulse_summary", {})
        amplify = payload.get("amplify", {})

        cadence = self._pulse_cadence(pulses)
        attestation_total = len(attestations) if isinstance(attestations, Iterable) else 0
        try:
            wave_energy = float(pulse_summary.get("average_wave", 0.0))
        except (TypeError, ValueError, AttributeError):
            wave_energy = 0.0

        amplify_summary = amplify.get("summary", {}) if isinstance(amplify, Mapping) else {}
        trend = str(amplify_summary.get("trend", "steady"))
        momentum = self._coerce_float(amplify_summary.get("momentum", 0.0))
        stability = self._coerce_float(amplify_summary.get("stability", 0.0))
        volatility = self._coerce_float(amplify_summary.get("volatility", 0.0))

        score = 20.0 if pulses else 0.0
        score += self._score_cadence(cadence["average_gap_seconds"])
        score += min(20.0, attestation_total * 2.5)
        score += self._score_wave_energy(wave_energy)
        score += self._score_amplify(momentum, stability, trend, volatility)

        health_score = round(max(0.0, min(100.0, score)), 2)

        status = self._describe_signal_health(health_score)
        insights = [
            (
                f"Pulse cadence averaging {cadence['average_gap_seconds']:.0f}s across"
                f" {cadence['samples']} signals (span {cadence['span_seconds']:.0f}s)."
            ),
            (
                f"Amplify trend {trend} with momentum {momentum:.2f}"
                f" and stability {stability:.3f}; volatility {volatility:.3f}."
            ),
            (
                f"{attestation_total} attestations and wave energy {wave_energy:.2f}"
                f" keep the signal {status}."
            ),
        ]

        metrics = {
            "average_pulse_gap_seconds": cadence["average_gap_seconds"],
            "pulse_span_seconds": cadence["span_seconds"],
            "attestation_total": attestation_total,
            "wave_energy": round(wave_energy, 2),
            "amplify_trend": trend,
            "amplify_momentum": round(momentum, 3),
            "amplify_stability": round(stability, 3),
            "amplify_volatility": round(volatility, 3),
        }

        return {
            "health_score": health_score,
            "status": status,
            "insights": insights,
            "metrics": metrics,
        }

    def _pulse_cadence(self, pulses: Iterable[Mapping[str, object]]) -> dict[str, float]:
        timestamps: list[datetime] = []
        for entry in pulses:
            ts_raw = entry.get("timestamp")
            if isinstance(ts_raw, str):
                try:
                    timestamps.append(datetime.fromisoformat(ts_raw))
                except ValueError:
                    continue

        if len(timestamps) < 2:
            return {"average_gap_seconds": 0.0, "span_seconds": 0.0, "samples": len(timestamps)}

        timestamps.sort(reverse=True)
        gaps = [
            (timestamps[index] - timestamps[index + 1]).total_seconds()
            for index in range(len(timestamps) - 1)
        ]
        average_gap = sum(gaps) / len(gaps)
        span_seconds = (timestamps[0] - timestamps[-1]).total_seconds()
        return {
            "average_gap_seconds": round(average_gap, 2),
            "span_seconds": round(span_seconds, 2),
            "samples": len(timestamps),
        }

    def _score_cadence(self, average_gap_seconds: float) -> float:
        if average_gap_seconds <= 0:
            return 25.0
        hours = average_gap_seconds / 3600.0
        scaled = 25.0 * (1.0 / (1.0 + hours))
        return round(max(5.0, min(25.0, scaled)), 2)

    def _score_wave_energy(self, average_wave: float) -> float:
        scaled = (average_wave / 360.0) * 25.0
        return round(max(0.0, min(25.0, scaled)), 2)

    def _score_amplify(
        self, momentum: float, stability: float, trend: str, volatility: float
    ) -> float:
        trend = trend.lower()
        if trend == "rising":
            base = 10.0
        elif trend == "steady":
            base = 7.0
        else:
            base = 5.0
        base += max(momentum, 0.0) * 1.5
        base += max(stability, 0.0) * 5.0
        base -= max(volatility, 0.0) * 0.5
        return round(max(0.0, min(30.0, base)), 2)

    @staticmethod
    def _describe_signal_health(health_score: float) -> str:
        if health_score >= 75:
            return "vibrant"
        if health_score >= 55:
            return "stable"
        if health_score >= 35:
            return "watch"
        return "cooling"

    @staticmethod
    def _coerce_float(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


__all__ = ["PulseDashboardBuilder"]
