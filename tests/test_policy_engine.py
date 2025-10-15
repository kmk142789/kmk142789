"""Tests for the policy engine."""

from __future__ import annotations

import json

from echo.policy_engine import PolicyEngine


def _write_policy(tmp_path, content: str) -> None:
    policy_dir = tmp_path / "policy"
    policy_dir.mkdir()
    (policy_dir / "default.yaml").write_text(content, encoding="utf-8")


def _write_codeowners(tmp_path, content: str) -> None:
    owners = tmp_path / "CODEOWNERS"
    owners.write_text(content, encoding="utf-8")


def test_policy_passes_with_matching_owners_and_tests(tmp_path):
    _write_policy(
        tmp_path,
        """
protected_paths:
  - pattern: "src/**"
    level: error
test_gates:
  - name: pytest
    required: true
""",
    )
    _write_codeowners(tmp_path, "src/* @team")
    engine = PolicyEngine(policy_dir=tmp_path / "policy", codeowners_path=tmp_path / "CODEOWNERS")
    report = engine.evaluate_paths(
        ["src/module.py"],
        test_results={"pytest": {"status": "passed"}},
    )
    assert report.passed


def test_policy_flags_missing_owner_and_tests(tmp_path):
    _write_policy(
        tmp_path,
        """
protected_paths:
  - pattern: "src/**"
    level: error
test_gates:
  - name: pytest
    required: true
""",
    )
    _write_codeowners(tmp_path, "docs/* @team")
    engine = PolicyEngine(policy_dir=tmp_path / "policy", codeowners_path=tmp_path / "CODEOWNERS")
    report = engine.evaluate_paths(["src/module.py"], test_results={})
    assert not report.passed
    details = json.loads(json.dumps(report.to_dict()))
    assert len(details["issues"]) >= 1
