"""Self-healing watchdog that coordinates automated remediation attempts."""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional

__all__ = [
    "RemediationResult",
    "WatchdogConfig",
    "WatchdogReport",
    "SelfHealingWatchdog",
]


@dataclass(slots=True)
class RemediationResult:
    """Represents the outcome of a remediation phase."""

    success: bool
    proof: Optional[Mapping[str, Any]] = None
    notes: Iterable[str] = field(default_factory=list)
    details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class WatchdogConfig:
    """Configuration for a :class:`SelfHealingWatchdog` run."""

    enabled: bool = True
    dry_run_only: bool = False
    max_attempts: int = 1
    cooldown_seconds: int = 0


@dataclass(slots=True)
class WatchdogReport:
    """Summarises a single watchdog cycle."""

    reason: str
    started_at: datetime
    dry_run: RemediationResult
    real_run: Optional[RemediationResult]
    proof_path: Optional[Path]
    succeeded: bool
    attempts: int


def _redact(value: Any, *, key_hint: str | None = None) -> Any:
    if isinstance(value, Mapping):
        return {k: _redact(v, key_hint=k) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(item, key_hint=key_hint) for item in value]
    if isinstance(value, str):
        hint = (key_hint or "").lower()
        if any(marker in hint for marker in ("token", "secret", "password", "key")):
            return "***redacted***"
    return value


class SelfHealingWatchdog:
    """Monitors failure signals and performs self-healing remediation."""

    def __init__(
        self,
        *,
        state_dir: Path | str = Path("state"),
        event_log: Path | str | None = None,
        transcripts_dir: Path | str | None = None,
        proofs_dir: Path | str | None = None,
        dry_run_executor: Callable[[Mapping[str, Any]], RemediationResult],
        real_executor: Callable[[Mapping[str, Any]], RemediationResult],
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._state_dir = Path(state_dir)
        self._event_log = Path(event_log) if event_log else self._state_dir / "event_log.jsonl"
        self._transcripts_dir = (
            Path(transcripts_dir)
            if transcripts_dir
            else self._state_dir / "watchdog_transcripts"
        )
        self._proofs_dir = Path(proofs_dir) if proofs_dir else self._state_dir / "watchdog_proofs"
        self._dry_run_executor = dry_run_executor
        self._real_executor = real_executor
        self._clock = clock or time.time
        self._lock = threading.RLock()
        self._attempts: Dict[str, int] = {}
        self._last_attempt: float = 0.0
        self._last_report: Optional[WatchdogReport] = None
        for path in (self._state_dir, self._transcripts_dir, self._proofs_dir):
            path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _persist_state(self) -> None:
        state_path = self._state_dir / "watchdog_state.json"
        payload = {
            "last_attempt": self._last_report.started_at.isoformat() if self._last_report else None,
            "last_success": (
                self._last_report.started_at.isoformat()
                if self._last_report and self._last_report.succeeded
                else None
            ),
            "cooldown_until": self._last_attempt + (self._last_config.cooldown_seconds if hasattr(self, "_last_config") else 0),
            "attempts": self._attempts,
        }
        state_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def _write_transcript(
        self,
        report: WatchdogReport,
        *,
        event: Mapping[str, Any],
        config: WatchdogConfig,
    ) -> None:
        timestamp = report.started_at.isoformat().replace(":", "-")
        base_name = f"{timestamp}-{report.reason.replace(' ', '_')}"
        json_payload = {
            "reason": report.reason,
            "started_at": report.started_at.isoformat(),
            "dry_run": {
                "success": report.dry_run.success,
                "notes": list(report.dry_run.notes),
                "details": _redact(report.dry_run.details),
            },
            "real_run": None,
            "proof_path": str(report.proof_path) if report.proof_path else None,
            "succeeded": report.succeeded,
            "attempts": report.attempts,
            "config": {
                "dry_run_only": config.dry_run_only,
                "max_attempts": config.max_attempts,
                "cooldown_seconds": config.cooldown_seconds,
            },
            "event": _redact(event),
        }
        if report.real_run is not None:
            json_payload["real_run"] = {
                "success": report.real_run.success,
                "notes": list(report.real_run.notes),
                "details": _redact(report.real_run.details),
            }
        transcript_path = self._transcripts_dir / f"{base_name}.json"
        transcript_path.write_text(json.dumps(json_payload, indent=2, sort_keys=True), encoding="utf-8")
        markdown_lines = [
            f"# Watchdog Transcript — {report.reason}",
            "",
            f"*Started:* {report.started_at.isoformat()}",
            f"*Succeeded:* {'yes' if report.succeeded else 'no'}",
            f"*Attempts:* {report.attempts}",
            "",
            "## Dry Run",
        ]
        for note in report.dry_run.notes:
            markdown_lines.append(f"- {note}")
        if report.real_run is not None:
            markdown_lines.append("")
            markdown_lines.append("## Real Run")
            for note in report.real_run.notes:
                markdown_lines.append(f"- {note}")
        if report.proof_path:
            markdown_lines.append("")
            markdown_lines.append(f"Proof stored at ``{report.proof_path}``")
        (self._transcripts_dir / f"{base_name}.md").write_text(
            "\n".join(markdown_lines),
            encoding="utf-8",
        )

    def _persist_proof(self, proof: Mapping[str, Any]) -> Path:
        proof_id = str(proof.get("id") or uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat().replace(":", "-")
        path = self._proofs_dir / f"{timestamp}-{proof_id}.json"
        payload = dict(proof)
        payload.setdefault("id", proof_id)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def status(self) -> Mapping[str, Any]:
        with self._lock:
            if not self._last_report:
                return {
                    "last_attempt": None,
                    "succeeded": None,
                    "attempts": self._attempts,
                }
            return {
                "last_attempt": self._last_report.started_at.isoformat(),
                "succeeded": self._last_report.succeeded,
                "attempts": self._attempts,
                "proof_path": str(self._last_report.proof_path) if self._last_report.proof_path else None,
            }

    def run_cycle(
        self,
        event: Mapping[str, Any],
        *,
        reason: str,
        config: Optional[WatchdogConfig] = None,
    ) -> WatchdogReport:
        config = config or WatchdogConfig(enabled=os.getenv("ECHO_WATCHDOG_ENABLED", "true").lower() != "false")
        if not config.enabled:
            raise RuntimeError("Watchdog disabled by configuration")
        now = self._clock()
        with self._lock:
            last_attempt_delta = now - self._last_attempt
            if config.cooldown_seconds and last_attempt_delta < config.cooldown_seconds:
                raise RuntimeError("Cooldown active; skipping remediation")
            attempts = self._attempts.get(reason, 0)
            if config.max_attempts and attempts >= config.max_attempts:
                raise RuntimeError("Maximum remediation attempts exceeded")
            self._attempts[reason] = attempts + 1
            started_at = datetime.now(timezone.utc)
            dry_run_result = self._dry_run_executor(event)
            real_result: Optional[RemediationResult] = None
            proof_path: Optional[Path] = None
            succeeded = dry_run_result.success
            if succeeded and not config.dry_run_only:
                real_result = self._real_executor(event)
                succeeded = succeeded and real_result.success
                if real_result and real_result.success and real_result.proof:
                    proof_path = self._persist_proof(real_result.proof)
            attempts_used = self._attempts[reason]
            if succeeded:
                self._attempts[reason] = 0
            report = WatchdogReport(
                reason=reason,
                started_at=started_at,
                dry_run=dry_run_result,
                real_run=real_result,
                proof_path=proof_path,
                succeeded=succeeded,
                attempts=attempts_used,
            )
            self._last_attempt = now
            self._last_report = report
            self._last_config = config  # type: ignore[attr-defined]
            self._write_transcript(report, event=event, config=config)
            self._persist_state()
            return report

    def detect_failures(self) -> List[Mapping[str, Any]]:
        """Return failure events discovered in the event log."""

        if not self._event_log.exists():
            return []
        failures: List[Mapping[str, Any]] = []
        for raw_line in self._event_log.read_text(encoding="utf-8").splitlines():
            if not raw_line.strip():
                continue
            try:
                event = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, MutableMapping) and str(event.get("status")).lower() == "failure":
                failures.append(event)
        return failures


WatchdogExecutor = Callable[[Mapping[str, Any]], RemediationResult]
