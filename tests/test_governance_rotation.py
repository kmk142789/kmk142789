from types import SimpleNamespace
import sys
import types

import pytest


def _install_stub_core_modules():
    core = types.ModuleType("echo_governance_core")
    sys.modules.setdefault("echo_governance_core", core)

    for module_name in ("anomaly", "policy_engine", "recovery", "vault"):
        full_name = f"echo_governance_core.{module_name}"
        module = types.ModuleType(full_name)
        module.get_latest_anomaly = lambda: {}
        module.disable_actor = lambda actor=None: actor
        module.restore_last_snapshot = lambda: None
        module.rotate_signing_keys = lambda: None
        sys.modules.setdefault(full_name, module)


_install_stub_core_modules()

from governance.alignment_fabric import ConditionLanguage
from governance import vault_keeper


def test_condition_language_supports_attribute_chains():
    context = {
        "anomaly": SimpleNamespace(score=0.92),
        "vault": {"integrity": 0.8},
        "true": True,
    }

    evaluator = ConditionLanguage("anomaly.score > 0.7 and vault.integrity < 0.9 and true == true").evaluator

    assert evaluator(context) is True


def test_vault_keeper_uses_condition_language(tmp_path, monkeypatch, capsys):
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(
        """
rotation_rules:
  - condition: "anomaly.score > 0.7"
    action: "rotate_keys"
  - condition: "vault.integrity < 0.85"
    action: "restore_snapshot"
  - condition: "actor.flags.blocked == true"
    action: "force_deny"
        """
    )

    monkeypatch.setattr(vault_keeper, "POLICY_PATH", str(policy_path))
    monkeypatch.setattr(vault_keeper, "compute_integrity", lambda: 0.8)
    monkeypatch.setattr(
        vault_keeper,
        "get_latest_anomaly",
        lambda: {"score": 0.95, "actor": "malice", "actor_blocked": True},
    )

    rotate_calls: list[str] = []
    restore_calls: list[str] = []
    deny_calls: list[str] = []

    monkeypatch.setattr(vault_keeper, "rotate_signing_keys", lambda: rotate_calls.append("rotated"))
    monkeypatch.setattr(vault_keeper, "restore_last_snapshot", lambda: restore_calls.append("restored"))
    monkeypatch.setattr(vault_keeper, "disable_actor", lambda actor_id: deny_calls.append(actor_id))

    vault_keeper.run_keeper()

    captured = capsys.readouterr()

    assert rotate_calls == ["rotated"]
    assert restore_calls == ["restored"]
    assert deny_calls == ["malice"]
    assert "Rotated signing keys" in captured.out
    assert "Restored last snapshot" in captured.out
    assert "Disabled malicious actor" in captured.out
