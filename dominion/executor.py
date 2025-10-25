"""Plan execution for Dominion."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

from .events import DominionJournal, DominionReceipt, JournalEntry, utc_now_iso
from .plans import ActionIntent, DominionPlan
from .policy import AllowlistPolicy, IdempotencyPolicy, PolicyEngine, PolicyViolation, RedactionPolicy
from .registry import AdapterRegistry


class PlanExecutor:
    """Apply Dominion plans with journaling, dry-runs and rollback."""

    def __init__(
        self,
        *,
        root: Path | str = ".",
        registry: AdapterRegistry | None = None,
        policy_engine: PolicyEngine | None = None,
        workdir: Path | str | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self.registry = registry or AdapterRegistry(self.root)
        self.filesystem = self.registry.filesystem()
        self.git = self.registry.git()
        self.workdir = Path(workdir).resolve() if workdir else self.root / "build" / "dominion"
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.journal_dir = self.workdir / "journals"
        self.receipt_dir = self.workdir / "receipts"
        self.state_dir = self.workdir / "state"
        self.journal_dir.mkdir(parents=True, exist_ok=True)
        self.receipt_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        if policy_engine is None:
            policy_engine = PolicyEngine(
                allowlist=AllowlistPolicy({"file.write", "http.post"}),
                redaction=RedactionPolicy({"secret", "token"}),
                idempotency=IdempotencyPolicy(self.state_dir / "idempotency.json"),
            )
        self.policy = policy_engine

    def apply(self, plan: DominionPlan, *, dry_run: bool = False) -> DominionReceipt:
        """Apply a plan and return a receipt."""

        self.policy.validate(plan)
        journal_entries: List[JournalEntry] = []
        applied = 0
        skipped = 0
        snapshots: List[Tuple[str, object]] = []

        try:
            for intent in plan.intents:
                if dry_run:
                    journal_entries.append(
                        JournalEntry(
                            intent_id=intent.intent_id,
                            action_type=intent.action_type,
                            status="dry-run",
                            message=f"Simulated execution for {intent.action_type}",
                        )
                    )
                    continue

                status, message, snapshot = self._execute_intent(intent)
                if status == "applied":
                    applied += 1
                else:
                    skipped += 1
                journal_entries.append(
                    JournalEntry(
                        intent_id=intent.intent_id,
                        action_type=intent.action_type,
                        status=status,
                        message=message,
                    )
                )
                if snapshot is not None:
                    snapshots.append((intent.action_type, snapshot))
        except Exception as exc:
            if not dry_run:
                self._rollback(snapshots)
                self.policy.rollback(plan)
            raise

        if dry_run:
            summary = {
                "applied": applied,
                "skipped": skipped,
                "dry_run": True,
                "plan_digest": plan.digest,
            }
            return DominionReceipt(
                plan_id=plan.plan_id,
                applied_at=utc_now_iso(),
                status="dry-run",
                summary=summary,
            )

        self.policy.mark_applied(plan)
        receipt = self._write_receipt(plan, applied=applied, skipped=skipped)
        self._write_journal(plan, journal_entries)
        return receipt

    def _execute_intent(self, intent: ActionIntent) -> Tuple[str, str, object | None]:
        if intent.action_type == "file.write":
            target = intent.target or intent.payload.get("path")
            if not target:
                raise PolicyViolation("file.write intents require a target path")
            content = str(intent.payload.get("content", ""))
            snapshot = self.filesystem.snapshot(target)
            if snapshot.exists and snapshot.content is not None and snapshot.content.decode("utf-8") == content:
                return "skipped", f"No changes required for {target}", None
            self.filesystem.write_text(target, content)
            return "applied", f"Wrote {len(content)} bytes to {target}", snapshot

        if intent.action_type == "http.post":
            url = intent.target or intent.payload.get("url")
            if not url:
                raise PolicyViolation("http.post intents require a target URL")
            payload = dict(intent.payload.get("json", intent.payload))
            response = self.registry.http().post(url, payload)
            return "applied", f"POST {url} -> {response.status}", None

        raise PolicyViolation(f"Unsupported action type: {intent.action_type}")

    def _rollback(self, snapshots: List[Tuple[str, object]]) -> None:
        for action, snapshot in reversed(snapshots):
            if action == "file.write":
                self.filesystem.restore(snapshot)

    def _write_journal(self, plan: DominionPlan, entries: List[JournalEntry]) -> Path:
        journal = DominionJournal(plan_id=plan.plan_id, entries=entries)
        payload = {
            "plan_id": journal.plan_id,
            "created_at": journal.created_at,
            "entries": [entry.__dict__ for entry in journal.entries],
        }
        path = self.journal_dir / f"plan_{plan.plan_id}.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def _write_receipt(self, plan: DominionPlan, *, applied: int, skipped: int) -> DominionReceipt:
        git_status = self.git.status()
        summary: Dict[str, object] = {
            "applied": applied,
            "skipped": skipped,
            "plan_digest": plan.digest,
            "git_head": git_status.head,
            "git_dirty": git_status.dirty,
        }
        redacted_summary = self.policy.redact(summary)
        receipt = DominionReceipt(
            plan_id=plan.plan_id,
            applied_at=utc_now_iso(),
            status="applied",
            summary=redacted_summary,
        )
        path = self.receipt_dir / f"plan_{plan.plan_id}.json"
        path.write_text(json.dumps(receipt.__dict__, indent=2, sort_keys=True), encoding="utf-8")
        return receipt

