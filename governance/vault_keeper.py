import logging
from types import SimpleNamespace

import yaml
from echo_governance_core.anomaly import get_latest_anomaly
from echo_governance_core.policy_engine import disable_actor
from echo_governance_core.recovery import restore_last_snapshot
from echo_governance_core.vault import rotate_signing_keys
from governance.alignment_fabric import ConditionLanguage
from governance.vault_integrity import compute_integrity

POLICY_PATH = "governance/rotation_policy.yaml"


def load_policy():
    with open(POLICY_PATH) as fp:
        return yaml.safe_load(fp)


def evaluate_conditions(policy):
    anomaly = get_latest_anomaly() or {}
    integrity = compute_integrity()

    actor_id = anomaly.get("actor")
    actor_blocked = anomaly.get("actor_blocked", False)
    actor_flags = SimpleNamespace(blocked=actor_blocked)

    anomaly_context = SimpleNamespace(**{**anomaly, "score": anomaly.get("score", 0.0)})

    context = {
        "anomaly": anomaly_context,
        "vault": SimpleNamespace(integrity=integrity),
        "actor": SimpleNamespace(flags=actor_flags, id=actor_id),
        "true": True,
        "false": False,
    }

    return context


def run_keeper():
    policy = load_policy()
    ctx = evaluate_conditions(policy)

    for rule in policy["rotation_rules"]:
        cond = rule["condition"]
        action = rule["action"]

        try:
            evaluator = ConditionLanguage(cond).evaluator
            should_trigger = evaluator(ctx)
        except Exception as exc:  # noqa: BLE001 - governance guardrail path
            logging.error("Invalid rotation condition %s: %s", cond, exc)
            continue

        if should_trigger:
            if action == "rotate_keys":
                rotate_signing_keys()
                print("[AVK] Rotated signing keys.")

            elif action == "restore_snapshot":
                restore_last_snapshot()
                print("[AVK] Restored last snapshot.")

            elif action == "force_deny":
                disable_actor(getattr(ctx["actor"], "id", None))
                print("[AVK] Disabled malicious actor.")


if __name__ == "__main__":
    run_keeper()
