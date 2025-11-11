from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from .parser import discover_artifacts
from .parser.models import Artifact, ArtifactType, CrossLink
from .rules import run_all
from .rules.base import ComplianceContext, Finding, FindingSeverity
from .schema_utils import validate_artifact


@dataclass
class EngineResult:
    artifacts: Dict[ArtifactType, Artifact]
    crosslinks: List[CrossLink]
    findings: List[Finding]
    validations: Dict[str, List[str]]
    mermaid: str
    graphviz: str
    matrix: Dict[str, int]


def _build_mermaid(findings: List[Finding]) -> str:
    edges: Dict[str, set] = defaultdict(set)
    for finding in findings:
        for clause in finding.references:
            for payload in clause.structured_data:
                data = payload.payload
                if isinstance(data, dict) and data.get("action") and data.get("role"):
                    action = data["action"].replace(" ", "_")
                    target = data.get("scope") or data.get("shared_with") or data.get("requires") or "output"
                    if isinstance(target, list):
                        target_label = ", ".join(target)
                    else:
                        target_label = str(target)
                    edges[finding.rule_id].add((data["role"], target_label, data["action"]))
    lines = ["flowchart TD"]
    added_nodes: set[str] = set()
    for _, edge_set in edges.items():
        for role, target, action in edge_set:
            role_id = role.replace(" ", "_")
            target_id = target.replace(" ", "_")
            if role_id not in added_nodes:
                lines.append(f"    {role_id}[{role}]")
                added_nodes.add(role_id)
            if target_id not in added_nodes:
                lines.append(f"    {target_id}[{target}]")
                added_nodes.add(target_id)
            lines.append(f"    {role_id} -->|{action}| {target_id}")
    return "\n".join(lines)


def _build_graphviz(findings: List[Finding]) -> str:
    lines = ["digraph AuthorityFlow {"]
    for finding in findings:
        for clause in finding.references:
            for payload in clause.structured_data:
                data = payload.payload
                if isinstance(data, dict) and data.get("action") and data.get("role"):
                    target = data.get("scope") or data.get("shared_with") or data.get("requires") or "output"
                    lines.append(
                        f'    "{data["role"]}" -> "{target}" [label="{data["action"]}"]'
                    )
    lines.append("}")
    return "\n".join(lines)


def _matrix(findings: List[Finding]) -> Dict[str, int]:
    counts = {
        "Pass": sum(1 for finding in findings if finding.severity == FindingSeverity.ALIGNMENT),
        "Soft": sum(1 for finding in findings if finding.severity == FindingSeverity.TENSION),
        "Fail": sum(1 for finding in findings if finding.severity == FindingSeverity.CONTRADICTION),
    }
    return counts


def _write_jsonl(findings: List[Finding], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for finding in findings:
            record = finding.to_dict()
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _write_matrix_json(matrix: Dict[str, int], findings: List[Finding], path: Path) -> None:
    data = {"matrix": matrix, "findings": [finding.to_dict() for finding in findings]}
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _build_fixit(findings: List[Finding]) -> Dict[str, List[str]]:
    suggestions: Dict[str, List[str]] = defaultdict(list)
    for finding in findings:
        if finding.severity == FindingSeverity.ALIGNMENT:
            continue
        for clause in finding.references:
            file_path = clause.source.file
            if finding.severity == FindingSeverity.CONTRADICTION:
                suggestion = f"Harmonize {finding.title} (rule {finding.rule_id})."
            else:
                suggestion = f"Document mitigations for {finding.title} (rule {finding.rule_id})."
            if suggestion not in suggestions[file_path]:
                suggestions[file_path].append(suggestion)
    return suggestions


def _render_markdown(matrix: Dict[str, int], findings: List[Finding], fixits: Dict[str, List[str]]) -> str:
    lines = ["# Aster Compliance Engine Report", ""]
    lines.append("## Summary Matrix")
    lines.append("| Outcome | Count |")
    lines.append("| --- | --- |")
    for label in ["Pass", "Soft", "Fail"]:
        lines.append(f"| {label} | {matrix.get(label, 0)} |")
    lines.append("")

    lines.append("## Detailed Findings")
    if not findings:
        lines.append("No findings detected.")
    else:
        for finding in findings:
            lines.append(f"### {finding.severity.value.title()}: {finding.title}")
            lines.append(f"* Rule ID: {finding.rule_id}")
            lines.append(f"* Description: {finding.description}")
            if finding.rationale:
                lines.append(f"* Rationale: {finding.rationale}")
            if finding.references:
                lines.append("* References:")
                for clause in finding.references:
                    lines.append(
                        f"  * `{clause.source.file}:{clause.source.line_start}-{clause.source.line_end}` → {clause.id}"
                    )
            lines.append("")

    lines.append("## Fix-it Plan")
    if not fixits:
        lines.append("All controls aligned — monitor for drift only.")
    else:
        for path, suggestions in sorted(fixits.items()):
            lines.append(f"- **{path}**")
            for suggestion in suggestions:
                lines.append(f"  - {suggestion}")
    lines.append("")
    return "\n".join(lines)


def run(input_dir: Path, output_dir: Path) -> EngineResult:
    artifacts, crosslinks = discover_artifacts(input_dir)
    context = ComplianceContext(artifacts=artifacts, crosslinks=crosslinks)
    findings = run_all(context)

    validations: Dict[str, List[str]] = {}
    for artifact in artifacts.values():
        errors = validate_artifact(artifact)
        validations[str(artifact.source_path)] = errors

    mermaid = _build_mermaid(findings)
    graphviz = _build_graphviz(findings)
    matrix = _matrix(findings)
    fixits = _build_fixit(findings)
    report_markdown = _render_markdown(matrix, findings, fixits)

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "CONTRADICTIONS.md").write_text(report_markdown, encoding="utf-8")
    (output_dir / "authority_flow.mmd").write_text(mermaid, encoding="utf-8")
    (output_dir / "authority_flow.dot").write_text(graphviz, encoding="utf-8")
    _write_jsonl(findings, output_dir / "evidence.jsonl")
    _write_matrix_json(matrix, findings, output_dir / "matrix.json")

    return EngineResult(
        artifacts=artifacts,
        crosslinks=crosslinks,
        findings=findings,
        validations=validations,
        mermaid=mermaid,
        graphviz=graphviz,
        matrix=matrix,
    )
