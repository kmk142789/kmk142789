"""Recurring COLOSSUS orchestrator that keeps the ritual alive."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, time as dt_time, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterable, Optional, Sequence

from echo.self_sustaining_loop import SelfSustainingLoop
from echo_infinite import EchoInfinite


@dataclass(slots=True)
class CycleRecord:
    """Summary of a completed transcend cycle."""

    cycle: int
    timestamp: str
    glyph_signature: str
    artifacts: Sequence[str]
    ledger_entry: Path
    ritual_path: Path
    targets: Sequence[str]
    progress: Optional[object] = None


class TranscendOrchestrator:
    """Schedule and persist recurring EchoInfinite cycles."""

    def __init__(
        self,
        *,
        base_dir: Path | str = ".",
        interval_minutes: float | None = None,
        at_midnight: bool = False,
        max_cycles: Optional[int] = 1,
        targets: Sequence[str] | None = None,
        ledger_path: Path | str = "ledger/transcend_log.jsonl",
        ritual_dir: Path | str = "ledger/rituals",
        stream_dir: Path | str = "ledger/transcend_streams",
        cycle_executor: Callable[[], None] | None = None,
        planning_loop: SelfSustainingLoop | None = None,
    ) -> None:
        if at_midnight and interval_minutes:
            raise ValueError("Specify either interval_minutes or at_midnight, not both")
        if max_cycles is not None and max_cycles <= 0:
            raise ValueError("max_cycles must be positive or None")

        self.base_dir = Path(base_dir)
        self.interval_minutes = interval_minutes or 0.0
        self.at_midnight = at_midnight
        self.max_cycles = max_cycles
        self.targets = tuple(targets or ("github", "firebase", "codex"))

        self.ledger_path = self._resolve_path(ledger_path)
        self.ritual_dir = self._resolve_path(ritual_dir)
        self.stream_dir = self._resolve_path(stream_dir)

        self.cycle_executor = cycle_executor or self._default_cycle_executor
        self.planning_loop = planning_loop or SelfSustainingLoop(self.base_dir)

        self._log_path = self.base_dir / "docs" / "COLOSSUS_LOG.md"
        self._state_path = self.base_dir / "colossus" / "state.json"

        self.ritual_dir.mkdir(parents=True, exist_ok=True)
        self.stream_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self) -> Iterable[CycleRecord]:
        """Yield :class:`CycleRecord` objects for each executed cycle."""

        cycles_run = 0
        while self.max_cycles is None or cycles_run < self.max_cycles:
            record = self._execute_cycle()
            cycles_run += 1
            yield record

            if self.max_cycles is not None and cycles_run >= self.max_cycles:
                break

            sleep_seconds = self._seconds_until_next_cycle(recorded_at=datetime.now(tz=timezone.utc))
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _execute_cycle(self) -> CycleRecord:
        self.cycle_executor()
        payload = self._extract_latest_cycle()

        progress_result = None
        if self.planning_loop is not None:
            summary = (
                f"Transcend cycle {payload['cycle']:05d} completed with glyph "
                f"{payload['glyph']} and {len(payload['artifacts'])} artifacts."
            )
            try:
                progress_result = self.planning_loop.progress(summary, actor="transcend")
            except Exception:
                progress_result = None

        ledger_entry = self._write_ledger_entry(payload, progress_result)
        ritual_path = self._write_ritual_entry(payload, progress_result)
        self._record_stream_receipts(payload, ritual_path)

        return CycleRecord(
            cycle=payload["cycle"],
            timestamp=payload["timestamp"],
            glyph_signature=payload["glyph"],
            artifacts=tuple(payload["artifacts"]),
            ledger_entry=ledger_entry,
            ritual_path=ritual_path,
            targets=self.targets,
            progress=progress_result,
        )

    def _extract_latest_cycle(self) -> dict:
        if not self._log_path.exists():
            raise FileNotFoundError("COLOSSUS_LOG.md is missing; run EchoInfinite once before transcending")

        lines = self._log_path.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            line = line.strip()
            if not line.startswith("- "):
                continue
            return self._parse_log_line(line)
        raise RuntimeError("No cycle entries found in COLOSSUS_LOG.md")

    def _parse_log_line(self, line: str) -> dict:
        content = line[2:]
        sections = [section.strip() for section in content.split("|")]
        if len(sections) < 4:
            raise ValueError(f"Unrecognised log line format: {line}")

        timestamp = sections[0]
        cycle_part = sections[1]
        glyph_part = sections[2]
        artifacts_part = "|".join(sections[3:])

        try:
            cycle = int(cycle_part.split()[1])
        except (IndexError, ValueError) as exc:
            raise ValueError(f"Unable to parse cycle from log line: {line}") from exc

        glyph = glyph_part.replace("Glyph", "", 1).strip()
        artifact_str = artifacts_part.split("Artifacts:", 1)[1].strip()
        artifacts = [item.strip() for item in artifact_str.split(",") if item.strip()]

        return {
            "timestamp": timestamp,
            "cycle": cycle,
            "glyph": glyph,
            "artifacts": artifacts,
        }

    def _write_ledger_entry(self, payload: dict, progress_result: object | None) -> Path:
        entry = {
            "recorded_at": datetime.now(tz=timezone.utc).isoformat(),
            "cycle": payload["cycle"],
            "glyph": payload["glyph"],
            "timestamp": payload["timestamp"],
            "artifacts": payload["artifacts"],
            "targets": list(self.targets),
        }

        if progress_result is not None:
            progress_payload = {}
            for key in ("cycle", "proposal_id", "next_proposal_id", "state_path"):
                if not hasattr(progress_result, key):
                    continue
                value = getattr(progress_result, key)
                if isinstance(value, Path):
                    value = value.as_posix()
                progress_payload[key] = value
            if progress_payload:
                entry["progress"] = progress_payload

        with self.ledger_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")

        return self.ledger_path

    def _write_ritual_entry(self, payload: dict, progress_result: object | None) -> Path:
        safe_timestamp = payload["timestamp"].replace(":", "-")
        ritual_path = self.ritual_dir / f"cycle_{payload['cycle']:05d}_{safe_timestamp}.md"
        summary_lines = [
            f"# Transcend Cycle {payload['cycle']:05d}",
            "",
            f"* Timestamp: {payload['timestamp']}",
            f"* Glyph Signature: {payload['glyph']}",
            f"* Artifacts ({len(payload['artifacts'])}):",
        ]
        summary_lines.extend(f"  - {artifact}" for artifact in payload["artifacts"])

        if progress_result is not None and hasattr(progress_result, "proposal_id"):
            summary_lines.append("")
            summary_lines.append(f"* Proposal Anchored: {progress_result.proposal_id}")

        ritual_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
        return ritual_path

    def _record_stream_receipts(self, payload: dict, ritual_path: Path) -> None:
        message = (
            f"cycle={payload['cycle']:05d} glyph={payload['glyph']} ritual={ritual_path.as_posix()}"
        )
        for target in self.targets:
            path = self.stream_dir / f"{target}.log"
            with path.open("a", encoding="utf-8") as fh:
                fh.write(message + "\n")

    def _seconds_until_next_cycle(self, *, recorded_at: datetime, now: datetime | None = None) -> float:
        reference = now or datetime.now(tz=timezone.utc)
        if self.at_midnight:
            next_day = recorded_at.date() + timedelta(days=1)
            target = datetime.combine(next_day, dt_time.min, tzinfo=timezone.utc)
            return max(0.0, (target - reference).total_seconds())
        if self.interval_minutes <= 0:
            return 0.0
        target = recorded_at + timedelta(minutes=self.interval_minutes)
        return max(0.0, (target - reference).total_seconds())

    def _default_cycle_executor(self) -> None:
        orchestrator = EchoInfinite(base_dir=self.base_dir, sleep_seconds=0.1, max_cycles=1)
        orchestrator.run()

    def _resolve_path(self, value: Path | str) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = self.base_dir / path
        return path


__all__ = ["CycleRecord", "TranscendOrchestrator"]
