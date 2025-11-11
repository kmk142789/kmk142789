from pathlib import Path

from compliance.parser import discover_artifacts
from compliance.rules import run_all
from compliance.rules.base import ComplianceContext, FindingSeverity


def test_rule_findings_span_severities():
    artifacts, crosslinks = discover_artifacts(Path("identity"))
    context = ComplianceContext(artifacts=artifacts, crosslinks=crosslinks)
    findings = run_all(context)

    severity_map = {finding.rule_id: finding.severity for finding in findings}
    assert severity_map["AUTH-ASSET_RELEASE"] == FindingSeverity.CONTRADICTION
    assert severity_map["CUST-EMERGENCY"] == FindingSeverity.TENSION
    assert severity_map["ID-ISSUANCE"] == FindingSeverity.ALIGNMENT
    assert "DIST-DISCRETIONARY" in severity_map
    assert "TRAN-AUDIT-FREQUENCY" in severity_map
