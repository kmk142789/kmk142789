from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_MANIFEST_SOURCES = {"manifest/*.json", "governance/*.json", "contracts/*.json"}
REQUIRED_MANIFEST_VALIDATORS = {"json_schema", "signature_chain", "uql_preflight"}
REQUIRED_CONSTRAINT_SETS = {"access_control", "supply_bounds", "ritual_safety"}
REQUIRED_TOPICS = {"governance.cr", "ledger.append", "ritual.invoke"}
REQUIRED_UQL_MODULES = {"access", "risk", "compliance"}
REQUIRED_INTERFACES = {"governance_kernel", "change_request_pipeline", "ritual_engine"}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def format_issue(path: Path, message: str) -> str:
    return f"{path.as_posix()}: {message}"


def check_kernel(path: Path) -> list[str]:
    issues: list[str] = []
    data = load_json(path)

    version = data.get("version")
    if not isinstance(version, str) or not version:
        issues.append(format_issue(path, "missing or invalid version"))

    kernel = data.get("kernel")
    if not isinstance(kernel, dict):
        issues.append(format_issue(path, "missing kernel definition"))
        return issues

    manifest_loader = kernel.get("manifest_loader")
    if not isinstance(manifest_loader, dict):
        issues.append(format_issue(path, "missing manifest_loader"))
    else:
        if manifest_loader.get("enabled") is not True:
            issues.append(format_issue(path, "manifest_loader.enabled must be true"))
        sources = set(manifest_loader.get("sources", []))
        if not REQUIRED_MANIFEST_SOURCES.issubset(sources):
            missing = sorted(REQUIRED_MANIFEST_SOURCES - sources)
            issues.append(format_issue(path, f"manifest_loader.sources missing {missing}"))
        validators = set(manifest_loader.get("validators", []))
        if not REQUIRED_MANIFEST_VALIDATORS.issubset(validators):
            missing = sorted(REQUIRED_MANIFEST_VALIDATORS - validators)
            issues.append(format_issue(path, f"manifest_loader.validators missing {missing}"))

    uql_enforcer = kernel.get("uql_enforcer")
    if not isinstance(uql_enforcer, dict):
        issues.append(format_issue(path, "missing uql_enforcer"))
    else:
        if uql_enforcer.get("enabled") is not True:
            issues.append(format_issue(path, "uql_enforcer.enabled must be true"))
        constraint_sets = set(uql_enforcer.get("constraint_sets", []))
        if not REQUIRED_CONSTRAINT_SETS.issubset(constraint_sets):
            missing = sorted(REQUIRED_CONSTRAINT_SETS - constraint_sets)
            issues.append(format_issue(path, f"uql_enforcer.constraint_sets missing {missing}"))

    state_machine = kernel.get("state_machine")
    if not isinstance(state_machine, dict):
        issues.append(format_issue(path, "missing state_machine"))
    else:
        states = state_machine.get("states")
        if not isinstance(states, list) or not states:
            issues.append(format_issue(path, "state_machine.states must be a non-empty list"))
        else:
            initial_state = state_machine.get("initial_state")
            if initial_state not in states:
                issues.append(format_issue(path, "state_machine.initial_state must be in states"))
            transitions = state_machine.get("transitions")
            if not isinstance(transitions, dict):
                issues.append(format_issue(path, "state_machine.transitions must be a mapping"))
            else:
                for source_state, targets in transitions.items():
                    if source_state not in states:
                        issues.append(
                            format_issue(
                                path, f"state_machine.transitions has invalid state {source_state}"
                            )
                        )
                    if not isinstance(targets, list) or not targets:
                        issues.append(
                            format_issue(
                                path, f"state_machine.transitions.{source_state} must be a list"
                            )
                        )
                    else:
                        invalid = [target for target in targets if target not in states]
                        if invalid:
                            issues.append(
                                format_issue(
                                    path,
                                    "state_machine.transitions contains unknown states "
                                    f"{sorted(set(invalid))}",
                                )
                            )
            guards = state_machine.get("guards", {})
            if not isinstance(guards, dict):
                issues.append(format_issue(path, "state_machine.guards must be a mapping"))
            else:
                invalid = [state for state in guards.keys() if state not in states]
                if invalid:
                    issues.append(
                        format_issue(
                            path,
                            "state_machine.guards contains unknown states "
                            f"{sorted(set(invalid))}",
                        )
                    )

    dispatcher = kernel.get("event_dispatcher")
    if not isinstance(dispatcher, dict):
        issues.append(format_issue(path, "missing event_dispatcher"))
    else:
        topics = set(dispatcher.get("topics", []))
        if not REQUIRED_TOPICS.issubset(topics):
            missing = sorted(REQUIRED_TOPICS - topics)
            issues.append(format_issue(path, f"event_dispatcher.topics missing {missing}"))
        handlers = dispatcher.get("handlers")
        if not isinstance(handlers, dict):
            issues.append(format_issue(path, "event_dispatcher.handlers must be a mapping"))
        else:
            for topic in topics:
                if topic not in handlers:
                    issues.append(format_issue(path, f"event_dispatcher.handlers missing {topic}"))
            for topic, handler_list in handlers.items():
                if not isinstance(handler_list, list) or not handler_list:
                    issues.append(
                        format_issue(
                            path,
                            f"event_dispatcher.handlers.{topic} must be a non-empty list",
                        )
                    )
        retries = dispatcher.get("retries")
        if not isinstance(retries, int) or retries < 0:
            issues.append(format_issue(path, "event_dispatcher.retries must be >= 0"))
        dead_letter = dispatcher.get("dead_letter")
        if not isinstance(dead_letter, str) or not dead_letter:
            issues.append(format_issue(path, "event_dispatcher.dead_letter must be set"))

    constraints = kernel.get("constraints")
    if not isinstance(constraints, dict):
        issues.append(format_issue(path, "missing constraints"))
    else:
        uql = constraints.get("uql")
        if not isinstance(uql, dict):
            issues.append(format_issue(path, "constraints.uql must be a mapping"))
        else:
            if uql.get("syntax_version") != "1.0":
                issues.append(format_issue(path, "constraints.uql.syntax_version must be 1.0"))
            modules = set(uql.get("modules", []))
            if not REQUIRED_UQL_MODULES.issubset(modules):
                missing = sorted(REQUIRED_UQL_MODULES - modules)
                issues.append(format_issue(path, f"constraints.uql.modules missing {missing}"))
            if uql.get("default_action") != "deny":
                issues.append(format_issue(path, "constraints.uql.default_action must be deny"))
        solver = constraints.get("solver")
        if not isinstance(solver, dict):
            issues.append(format_issue(path, "constraints.solver must be a mapping"))
        else:
            if solver.get("type") != "sat+uql":
                issues.append(format_issue(path, "constraints.solver.type must be sat+uql"))
            max_iterations = solver.get("max_iterations")
            if not isinstance(max_iterations, int) or max_iterations < 1:
                issues.append(format_issue(path, "constraints.solver.max_iterations must be >= 1"))
            timeout_ms = solver.get("timeout_ms")
            if not isinstance(timeout_ms, int) or timeout_ms < 1:
                issues.append(format_issue(path, "constraints.solver.timeout_ms must be >= 1"))

    return issues


def check_interface_map(path: Path, mode: str) -> list[str]:
    issues: list[str] = []
    data = load_json(path)
    interfaces = data.get("interfaces")
    if not isinstance(interfaces, dict):
        return [format_issue(path, "interfaces must be a mapping")]

    missing = sorted(REQUIRED_INTERFACES - interfaces.keys())
    if missing:
        issues.append(format_issue(path, f"missing interfaces {missing}"))

    for name in REQUIRED_INTERFACES & interfaces.keys():
        spec = interfaces.get(name)
        if not isinstance(spec, dict):
            issues.append(format_issue(path, f"interfaces.{name} must be a mapping"))
            continue
        inputs = spec.get("inputs")
        outputs = spec.get("outputs")
        if not isinstance(inputs, list) or not inputs:
            issues.append(format_issue(path, f"interfaces.{name}.inputs must be a non-empty list"))
        if not isinstance(outputs, list) or not outputs:
            issues.append(format_issue(path, f"interfaces.{name}.outputs must be a non-empty list"))
        if mode == "strong":
            guarantees = spec.get("guarantees")
            if not isinstance(guarantees, list) or not guarantees:
                issues.append(
                    format_issue(path, f"interfaces.{name}.guarantees must be a non-empty list")
                )
        if mode == "weak":
            assumptions = spec.get("assumptions")
            if not isinstance(assumptions, list) or not assumptions:
                issues.append(
                    format_issue(path, f"interfaces.{name}.assumptions must be a non-empty list")
                )

    return issues


def check_reference_instance(root: Path) -> list[str]:
    issues: list[str] = []
    reference_root = root / "federation" / "reference-instance"
    if not reference_root.exists():
        return [format_issue(reference_root, "reference instance layout missing")]

    for required_dir in ("manifest", "governance", "contracts", "logs"):
        dir_path = reference_root / required_dir
        if not dir_path.is_dir():
            issues.append(format_issue(dir_path, "required directory missing"))

    for filename in ("governance_kernel.json", "interface_map_strong.json", "interface_map_weak.json"):
        canonical_path = root / filename
        reference_path = reference_root / filename
        if not reference_path.exists():
            issues.append(format_issue(reference_path, "missing reference instance file"))
            continue
        canonical = json.dumps(load_json(canonical_path), sort_keys=True, indent=2)
        reference = json.dumps(load_json(reference_path), sort_keys=True, indent=2)
        if canonical != reference:
            issues.append(
                format_issue(
                    reference_path, f"reference instance drift detected vs {canonical_path}"
                )
            )

    return issues


def run(root: Path) -> int:
    issues: list[str] = []
    kernel_path = root / "governance_kernel.json"
    strong_path = root / "interface_map_strong.json"
    weak_path = root / "interface_map_weak.json"

    issues.extend(check_kernel(kernel_path))
    issues.extend(check_interface_map(strong_path, "strong"))
    issues.extend(check_interface_map(weak_path, "weak"))
    issues.extend(check_reference_instance(root))

    if issues:
        print("Federation readiness check failed:\n")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Federation readiness check passed.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate federation readiness against the Echo governance kernel."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root path.",
    )
    args = parser.parse_args()
    raise SystemExit(run(args.root))


if __name__ == "__main__":
    main()
