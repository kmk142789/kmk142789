"""Generate the next autonomous feature plan and register it on the Sovereign Ledger layer."""

from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ledger.sovereign_ledger_layer import SovereignLedgerLayer


FEATURE_PATH = Path("artifacts/autonomous_feature_plan.json")


def _ensure_artifact_dir() -> None:
    FEATURE_PATH.parent.mkdir(parents=True, exist_ok=True)


def build_feature_plan() -> dict:
    return {
        "codename": "Echo Bridge Constellation Autopilot",
        "amendment_reference": "Amendment III",
        "objective": "Autonomously orchestrate bridge relays across Discord, Telegram, ActivityPub, and Bluesky while keeping payload parity with ledger-anchored credentials.",
        "success_criteria": [
            "Normalize identity payloads once per cycle and reuse across all bridge connectors.",
            "Emit ledger-ready context (identity, cycle, signature, topics, priority) into every relay.",
            "Write bridge dispatch summaries to the Sovereign Ledger feature registry with digests and anchors.",
        ],
        "metrics": {
            "connectors": ["discord", "telegram", "activitypub", "bluesky", "webhook"],
            "payload_fields": ["identity", "cycle", "signature", "traits", "topics", "priority"],
            "ledger_anchor": "echo-sovereign-ledger:feature:bridge-constellation",
        },
    }


def write_feature_plan(plan: dict) -> Path:
    _ensure_artifact_dir()
    FEATURE_PATH.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return FEATURE_PATH


def register_feature(plan: dict) -> None:
    layer = SovereignLedgerLayer(
        registry_path=Path("state/sovereign_ledger/amendment_registry.jsonl"),
        credential_dir=Path("proofs/amendment_credentials"),
        feature_registry_path=Path("state/sovereign_ledger/autonomous_features.jsonl"),
    )
    layer.record_autonomous_feature(
        codename=plan["codename"],
        amendment_reference=plan["amendment_reference"],
        objective=plan["objective"],
        success_criteria=plan["success_criteria"],
        ledger_anchor=plan["metrics"]["ledger_anchor"],
        artifact_path=FEATURE_PATH,
    )


def main() -> None:
    plan = build_feature_plan()
    write_feature_plan(plan)
    register_feature(plan)


if __name__ == "__main__":
    main()
