"""Policy engine enforcing repository governance rules."""

from __future__ import annotations

import argparse
import json
import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

try:  # pragma: no cover - optional dependency
    import yaml
except ModuleNotFoundError:  # pragma: no cover - fallback
    yaml = None

_REPO_ROOT = Path(__file__).resolve().parent.parent
_POLICY_DIR = _REPO_ROOT / "echo" / "policy"
_CODEOWNERS_PATH = _REPO_ROOT / ".github" / "CODEOWNERS"


@dataclass
class PolicyIssue:
    level: str
    message: str
    path: str | None = None


@dataclass
class PolicyReport:
    passed: bool
    issues: List[PolicyIssue] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "issues": [issue.__dict__ for issue in self.issues],
        }


class PolicyEngine:
    def __init__(
        self,
        policy_dir: Path | None = None,
        codeowners_path: Path | None = None,
    ) -> None:
        self.policy_dir = policy_dir or _POLICY_DIR
        self.codeowners_path = codeowners_path or _CODEOWNERS_PATH
        self.policies = self._load_policies()
        self.codeowners = self._load_codeowners()

    def _load_policies(self) -> dict:
        config: dict = {
            "protected_paths": [],
            "required_reviewers": [],
            "test_gates": [],
            "allowed_actions": {},
        }
        if not self.policy_dir.exists():
            return config
        for yaml_file in sorted(self.policy_dir.glob("*.yaml")):
            data = _load_policy_yaml(yaml_file)
            for key in config:
                if key in data:
                    if isinstance(config[key], list):
                        config[key].extend(data[key])
                    elif isinstance(config[key], dict):
                        config[key].update(data[key])
        return config

    def _load_codeowners(self) -> List[tuple[str, List[str]]]:
        owners: List[tuple[str, List[str]]] = []
        if not self.codeowners_path.exists():
            return owners
        for line in self.codeowners_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            pattern, *owners_list = parts
            owners.append((pattern, owners_list))
        return owners

    def _owners_for(self, path: str) -> List[str]:
        matches: List[str] = []
        for pattern, owners in self.codeowners:
            if fnmatch.fnmatch(path, pattern):
                matches = owners
        return matches

    def evaluate_paths(
        self,
        paths: Iterable[str],
        *,
        test_results: Optional[Dict[str, dict]] = None,
    ) -> PolicyReport:
        issues: List[PolicyIssue] = []
        for changed in paths:
            owners = self._owners_for(changed)
            if not owners:
                issues.append(PolicyIssue("error", f"No CODEOWNERS match for {changed}", changed))
            for rule in self.policies.get("protected_paths", []):
                pattern = rule.get("pattern")
                if pattern and fnmatch.fnmatch(changed, pattern):
                    if rule.get("enforce", False):
                        message = rule.get("message") or f"Protected path touched: {changed}"
                        level = rule.get("level", "error")
                        issues.append(PolicyIssue(level, message, changed))
        if test_results is None:
            test_results = {}
        for gate in self.policies.get("test_gates", []):
            name = gate.get("name")
            if not name:
                continue
            required = gate.get("required", True)
            status = (test_results.get(name) or {}).get("status")
            if required and status != "passed":
                issues.append(
                    PolicyIssue(
                        "error",
                        gate.get("message")
                        or f"Test gate '{name}' not satisfied (status={status!r})",
                        None,
                    )
                )
        passed = not any(issue.level == "error" for issue in issues)
        return PolicyReport(passed=passed, issues=issues)

    def explain(self, path: str) -> dict:
        owners = self._owners_for(path)
        applicable = [
            rule
            for rule in self.policies.get("protected_paths", [])
            if rule.get("pattern") and fnmatch.fnmatch(path, rule["pattern"])
        ]
        return {"owners": owners, "protected_paths": applicable}

    def diff_paths(self, diff: str) -> List[str]:
        from subprocess import CalledProcessError, run

        try:
            result = run(
                ["git", "diff", "--name-only", diff],
                cwd=_REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, CalledProcessError):
            return []
        return [line for line in result.stdout.splitlines() if line]

    def check_diff(self, diff: str, test_results_path: Path | None = None) -> PolicyReport:
        changed = self.diff_paths(diff)
        results = None
        if test_results_path and test_results_path.exists():
            results = json.loads(test_results_path.read_text(encoding="utf-8"))
        return self.evaluate_paths(changed, test_results=results)


def _cmd_check(args: argparse.Namespace) -> int:
    engine = PolicyEngine()
    report = engine.check_diff(args.diff, test_results_path=args.tests)
    print(json.dumps(report.to_dict(), indent=2))
    return 0 if report.passed else 1


def _cmd_explain(args: argparse.Namespace) -> int:
    engine = PolicyEngine()
    info = engine.explain(args.path)
    print(json.dumps(info, indent=2))
    return 0


def build_parser(subparsers: argparse._SubParsersAction) -> None:
    policy_parser = subparsers.add_parser("policy", help="Policy engine commands")
    policy_sub = policy_parser.add_subparsers(dest="policy_command", required=True)

    check_parser = policy_sub.add_parser("check", help="Evaluate policy for a diff range")
    check_parser.add_argument("--diff", required=True, help="Git diff range to evaluate")
    check_parser.add_argument(
        "--tests",
        type=Path,
        help="Optional JSON file containing test gate results",
    )
    check_parser.set_defaults(func=_cmd_check)

    explain_parser = policy_sub.add_parser("explain", help="Explain policies for a path")
    explain_parser.add_argument("--path", required=True)
    explain_parser.set_defaults(func=_cmd_explain)


__all__ = ["PolicyEngine", "PolicyIssue", "PolicyReport", "build_parser"]


def _load_policy_yaml(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text) or {}
    return _minimal_yaml(text)


def _minimal_yaml(text: str) -> dict:
    result: dict = {}
    key_stack: list[tuple[int, dict]] = []
    current_key: str | None = None
    current_list: list | None = None
    current_map: dict | None = None
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line:
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if not stripped:
            continue
        if not stripped.startswith("-") and stripped.endswith(":"):
            current_key = stripped[:-1]
            result.setdefault(current_key, [])
            current_list = result[current_key]
            current_map = None
            key_stack.append((indent, result))
            continue
        if stripped.startswith("- "):
            if current_key is None:
                continue
            entry_text = stripped[2:]
            current_map = {}
            current_list.append(current_map)
            if entry_text:
                key, _, value = entry_text.partition(":")
                current_map[key.strip()] = _coerce_value(value.strip())
            continue
        if current_map is not None:
            key, _, value = stripped.partition(":")
            current_map[key.strip()] = _coerce_value(value.strip())
    return result


def _coerce_value(value: str):
    value = value.strip()
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.startswith("\"") and value.endswith("\""):
        return value.strip("\"")
    return value

