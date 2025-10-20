from __future__ import annotations

"""Self-sustaining planning loop that seeds future branch proposals."""

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


@dataclass(slots=True)
class DecisionResult:
    """Return payload for governance decisions."""

    proposal_id: str
    decision: str
    status: str
    path: Path


@dataclass(slots=True)
class ProgressResult:
    """Return payload for cycle progress updates."""

    cycle: int
    proposal_id: str
    next_proposal_id: str
    state_path: Path


class SelfSustainingLoop:
    """Manage the continuous planning loop for Echo's iterations."""

    def __init__(self, root: Path | str = ".") -> None:
        self.root = Path(root)
        self.state_path = self.root / "state" / "self_sustaining_loop.json"
        self.proposals_dir = self.root / "state" / "proposals"
        self.proposals_dir.mkdir(parents=True, exist_ok=True)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load_state()
        self._ensure_initial_proposal()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def progress(self, summary: str, *, actor: str = "automation") -> ProgressResult:
        """Record progress for the current cycle and seed the next proposal."""

        summary = self._normalize_summary(summary)
        now = self._iso_now()

        current_cycle = int(self.state.get("current_cycle", 0))
        target_cycle = current_cycle + 1
        proposal_id = self._proposal_id(target_cycle)

        # Ensure the upcoming proposal exists before finalising it.
        self._ensure_proposal(target_cycle, actor=actor, summary=summary, reason="cycle-progress-prep")

        # Update governance outcome for the active proposal.
        self._finalize_proposal(proposal_id, actor=actor, summary=summary, timestamp=now)

        # Persist state history for auditing.
        history = list(self.state.get("history", []))
        history.append(
            {
                "cycle": target_cycle,
                "timestamp": now,
                "summary": summary,
                "actor": actor,
            }
        )
        self.state["history"] = history
        self.state["current_cycle"] = target_cycle
        self._write_json(self.state_path, self.state)

        # Prepare the next cycle's draft proposal.
        next_cycle = target_cycle + 1
        next_summary = (
            f"Draft roadmap for cycle {next_cycle:04d} following progress in {proposal_id}: {summary}"
        )
        next_proposal_id = self._proposal_id(next_cycle)
        self._ensure_proposal(
            next_cycle,
            actor=actor,
            summary=next_summary,
            reason="spawn-next-proposal",
        )

        return ProgressResult(
            cycle=target_cycle,
            proposal_id=proposal_id,
            next_proposal_id=next_proposal_id,
            state_path=self.state_path,
        )

    def decide(
        self,
        proposal_id: str,
        decision: str,
        *,
        actor: str = "governance",
        reason: Optional[str] = None,
    ) -> DecisionResult:
        """Record a governance decision for ``proposal_id``."""

        proposal_data, path = self._load_proposal(proposal_id)
        normalized = decision.strip().lower()
        if normalized not in {"approve", "reject", "auto-merge"}:
            raise ValueError("decision must be approve, reject, or auto-merge")

        now = self._iso_now()
        governance = dict(proposal_data.get("governance", {}))
        governance.update(
            {
                "decision": normalized,
                "decided_at": now,
                "decider": actor,
                "reason": (reason or "").strip() or None,
            }
        )

        status = self._status_for_decision(normalized)
        proposal_data["governance"] = governance
        proposal_data["status"] = status
        proposal_data["updated_at"] = now
        self._append_history(
            proposal_data,
            action="governance-decision",
            actor=actor,
            details=f"decision={normalized}" + (f" reason={reason}" if reason else ""),
            timestamp=now,
        )
        self._write_json(path, proposal_data)

        return DecisionResult(proposal_id=proposal_id, decision=normalized, status=status, path=path)

    def list_proposals(self) -> list[dict]:
        """Return proposal metadata ordered by target cycle."""

        proposals = []
        for candidate in sorted(self.proposals_dir.glob("cycle_*.json")):
            data = self._read_json(candidate)
            proposals.append(data)
        proposals.sort(key=lambda payload: payload.get("target_cycle", 0))
        return proposals

    def get_proposal(self, proposal_id: str) -> dict:
        """Return the proposal payload for ``proposal_id``."""

        data, _ = self._load_proposal(proposal_id)
        return data

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_initial_proposal(self) -> None:
        if any(self.proposals_dir.glob("cycle_*.json")):
            return
        self._ensure_proposal(
            1,
            actor="bootstrap",
            summary="Initial branch planning seed for cycle 0001",
            reason="initial-seed",
        )

    def _ensure_proposal(
        self,
        cycle: int,
        *,
        actor: str,
        summary: str,
        reason: str,
    ) -> dict:
        path = self._proposal_path(cycle)
        now = self._iso_now()
        proposal_id = self._proposal_id(cycle)
        if path.exists():
            data = self._read_json(path)
            if summary:
                data["summary"] = summary
            data["updated_at"] = now
            self._append_history(
                data,
                timestamp=now,
                action="refreshed",
                actor=actor,
                details=reason,
            )
            self._write_json(path, data)
            return data

        payload = {
            "proposal_id": proposal_id,
            "branch_name": f"loop/cycle-{cycle:04d}",
            "target_cycle": cycle,
            "status": "draft",
            "created_at": now,
            "updated_at": now,
            "summary": summary,
            "governance": {
                "rule": "Auto-merge when the program advances past the target cycle unless explicitly decided otherwise.",
                "decision": "pending",
                "decided_at": None,
                "decider": None,
                "reason": None,
            },
            "history": [
                {
                    "timestamp": now,
                    "action": "created",
                    "actor": actor,
                    "details": reason,
                }
            ],
        }
        self._write_json(path, payload)
        return payload

    def _finalize_proposal(
        self,
        proposal_id: str,
        *,
        actor: str,
        summary: str,
        timestamp: str,
    ) -> None:
        data, path = self._load_proposal(proposal_id)
        governance = dict(data.get("governance", {}))
        decision = governance.get("decision", "pending") or "pending"
        status = data.get("status", "draft")

        if decision == "pending":
            # Auto-merge because no explicit decision was recorded.
            governance.update(
                {
                    "decision": "auto-merge",
                    "decided_at": timestamp,
                    "decider": actor,
                    "reason": summary,
                }
            )
            status = "auto-merged"
        elif decision == "auto-merge":
            status = "auto-merged"
            if not governance.get("decided_at"):
                governance["decided_at"] = timestamp
            if not governance.get("decider"):
                governance["decider"] = actor
        elif decision == "approve":
            status = "merged"
        elif decision == "reject":
            status = "rejected"

        data["status"] = status
        data["governance"] = governance
        data["updated_at"] = timestamp
        self._append_history(
            data,
            timestamp=timestamp,
            action="cycle-progressed",
            actor=actor,
            details=summary,
        )
        self._write_json(path, data)

    def _load_state(self) -> dict:
        if not self.state_path.exists():
            default = {"current_cycle": 0, "history": []}
            self._write_json(self.state_path, default)
            return default
        return self._read_json(self.state_path)

    def _load_proposal(self, proposal_id: str) -> tuple[dict, Path]:
        if proposal_id.startswith("cycle_"):
            path = self.proposals_dir / f"{proposal_id}.json"
        else:
            path = self._proposal_path(int(proposal_id))
        if not path.exists():
            raise FileNotFoundError(f"proposal {proposal_id} not found")
        return self._read_json(path), path

    def _proposal_path(self, cycle: int) -> Path:
        return self.proposals_dir / f"{self._proposal_id(cycle)}.json"

    @staticmethod
    def _proposal_id(cycle: int) -> str:
        return f"cycle_{cycle:04d}"

    @staticmethod
    def _status_for_decision(decision: str) -> str:
        return {
            "approve": "approved",
            "reject": "rejected",
            "auto-merge": "auto-merged",
        }[decision]

    @staticmethod
    def _append_history(
        payload: dict,
        *,
        timestamp: str,
        action: str,
        actor: str,
        details: Optional[str] = None,
    ) -> None:
        history = list(payload.get("history", []))
        history.append(
            {
                "timestamp": timestamp,
                "action": action,
                "actor": actor,
                "details": details,
            }
        )
        payload["history"] = history

    @staticmethod
    def _read_json(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_json(path: Path, payload: dict) -> None:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(path)

    @staticmethod
    def _iso_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _normalize_summary(summary: str) -> str:
        text = (summary or "").strip()
        if not text:
            raise ValueError("summary must not be empty")
        return text


# ----------------------------------------------------------------------
# Command line interface
# ----------------------------------------------------------------------

def _parse_args(argv: Optional[Iterable[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root for state storage")

    sub = parser.add_subparsers(dest="command", required=True)

    progress_parser = sub.add_parser("progress", help="Record progress and seed the next proposal")
    progress_parser.add_argument("--summary", required=True, help="Description of the completed work")
    progress_parser.add_argument("--actor", default="automation", help="Actor recording the progress")

    decision_parser = sub.add_parser("decide", help="Record a governance decision for a proposal")
    decision_parser.add_argument("proposal_id", help="Proposal identifier (cycle_XXXX)")
    decision_group = decision_parser.add_mutually_exclusive_group(required=True)
    decision_group.add_argument("--approve", action="store_true", help="Approve the proposal")
    decision_group.add_argument("--reject", action="store_true", help="Reject the proposal")
    decision_group.add_argument("--auto-merge", dest="auto_merge", action="store_true", help="Mark for auto-merge")
    decision_parser.add_argument("--actor", default="governance", help="Decision maker")
    decision_parser.add_argument("--reason", default=None, help="Decision rationale")

    list_parser = sub.add_parser("list", help="List proposals and their status")
    list_parser.add_argument("--compact", action="store_true", help="Only display identifiers and status")

    show_parser = sub.add_parser("show", help="Display a proposal payload")
    show_parser.add_argument("proposal_id", help="Proposal identifier (cycle_XXXX)")

    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = _parse_args(argv)
    loop = SelfSustainingLoop(args.root)

    if args.command == "progress":
        result = loop.progress(args.summary, actor=args.actor)
        print(
            f"[cycle] advanced to {result.cycle:04d} — finalized {result.proposal_id} and seeded {result.next_proposal_id}"
        )
    elif args.command == "decide":
        decision = "approve" if args.approve else "reject" if args.reject else "auto-merge"
        result = loop.decide(
            args.proposal_id,
            decision,
            actor=args.actor,
            reason=args.reason,
        )
        print(
            f"[decision] {result.proposal_id} marked as {result.decision} (status={result.status})"
        )
    elif args.command == "list":
        proposals = loop.list_proposals()
        if not proposals:
            print("[info] no proposals recorded yet")
            return
        for payload in proposals:
            if args.compact:
                print(f"{payload['proposal_id']}: {payload['status']}")
                continue
            print(
                f"{payload['proposal_id']} — branch={payload['branch_name']} status={payload['status']} decision={payload['governance']['decision']}"
            )
    elif args.command == "show":
        payload = loop.get_proposal(args.proposal_id)
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:  # pragma: no cover
        raise ValueError(f"unknown command {args.command}")


if __name__ == "__main__":  # pragma: no cover
    main()
