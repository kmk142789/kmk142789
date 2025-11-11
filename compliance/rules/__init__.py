from __future__ import annotations

from typing import List

from . import amendments, authority, custody, distributions, identity, transparency
from .base import ComplianceContext, Finding


RULE_MODULES = [
    authority,
    custody,
    distributions,
    amendments,
    identity,
    transparency,
]


def run_all(context: ComplianceContext) -> List[Finding]:
    findings: List[Finding] = []
    for module in RULE_MODULES:
        findings.extend(module.evaluate(context))
    return findings
