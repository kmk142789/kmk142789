from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from echo.pulseweaver.watchdog import RemediationResult, SelfHealingWatchdog, WatchdogConfig


def test_watchdog_runs_two_phase(tmp_path):
    event = {"status": "failure", "reason": "test", "ts": datetime.now(timezone.utc).isoformat()}
    log_path = tmp_path / "event_log.jsonl"
    log_path.write_text(json.dumps(event) + "\n", encoding="utf-8")

    proofs_dir = tmp_path / "proofs"
    transcripts_dir = tmp_path / "transcripts"

    def dry_run(payload):
        assert payload["reason"] == "test"
        return RemediationResult(success=True, notes=["dry run ok"], details={"stage": "dry"})

    def real_run(payload):
        assert payload["reason"] == "test"
        return RemediationResult(
            success=True,
            proof={"id": "proof-123", "status": "ok"},
            notes=["real run ok"],
            details={"stage": "real"},
        )

    watchdog = SelfHealingWatchdog(
        state_dir=tmp_path,
        event_log=log_path,
        proofs_dir=proofs_dir,
        transcripts_dir=transcripts_dir,
        dry_run_executor=dry_run,
        real_executor=real_run,
    )

    failures = watchdog.detect_failures()
    assert failures and failures[0]["reason"] == "test"

    report = watchdog.run_cycle(failures[0], reason="unit", config=WatchdogConfig(max_attempts=2))
    assert report.succeeded
    assert report.proof_path is not None and report.proof_path.exists()

    transcript_files = list(transcripts_dir.glob("*.json"))
    assert transcript_files, "transcript JSON not written"
    markdown_files = list(transcripts_dir.glob("*.md"))
    assert markdown_files, "transcript markdown not written"

    state_file = tmp_path / "watchdog_state.json"
    assert json.loads(state_file.read_text(encoding="utf-8"))["attempts"]["unit"] == 0
