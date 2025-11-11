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

        indices = [entry["index"] for entry in history if isinstance(entry.get("index"), (int, float))]
        summary: dict[str, object] = {"cycles_tracked": len(snapshots)}
        if indices:
            avg_index = sum(indices) / len(indices)
            summary["average_index"] = round(avg_index, 2)
            summary["peak_index"] = round(max(indices), 2)
            if len(indices) >= 2:
                summary["momentum"] = round(indices[0] - indices[1], 2)
        summary["latest_commit"] = latest.get("commit_sha")
        summary["presence"] = (
            f"Amplify presence cycle {latest.get('cycle')} @ index {latest.get('index'):.2f}"
            if isinstance(latest.get("index"), (int, float))
            else f"Amplify presence cycle {latest.get('cycle')}"
        )

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


__all__ = ["PulseDashboardBuilder"]
