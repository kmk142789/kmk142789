"""
Echo Mediator vNext
- policy-aware preflight checks for actions (DNS, credentials, treasury)
- emits allow/deny + rationale + attestation stub
"""
from dataclasses import dataclass
from typing import Dict, Any

POLICY = {
    "dns": {"allowed_types": {"TXT", "CNAME", "A"}, "require_attest": True},
    "credentials": {"issuers": {"did:web:kmk142789.github.io:little-footsteps-bank"}, "require_status_list": True},
    "treasury": {"max_auto_disburse_usd": 10000},
}


@dataclass
class Decision:
    allow: bool
    reason: str
    attestation: Dict[str, Any]


def preflight(action: Dict[str, Any]) -> Decision:
    domain = action.get("domain")
    kind = action.get("kind")
    if kind == "dns":
        rtype = action["record"]["type"]
        if rtype not in POLICY["dns"]["allowed_types"]:
            return Decision(False, f"DNS type {rtype} not allowed", {})
        return Decision(
            True,
            "DNS change within policy",
            {"attest_needed": POLICY["dns"]["require_attest"], "domain": domain},
        )
    if kind == "credential":
        issuer = action.get("issuer")
        if issuer not in POLICY["credentials"]["issuers"]:
            return Decision(False, "unknown issuer", {})
        return Decision(
            True,
            "credential issuer recognized",
            {"status_list": POLICY["credentials"]["require_status_list"]},
        )
    if kind == "treasury":
        if float(action.get("amount_usd", 0)) > POLICY["treasury"]["max_auto_disburse_usd"]:
            return Decision(False, "exceeds auto-disburse threshold", {})
        return Decision(
            True,
            "treasury within limit",
            {"limit": POLICY["treasury"]["max_auto_disburse_usd"]},
        )
    return Decision(True, "known action", {})


if __name__ == "__main__":
    demo = {
        "kind": "dns",
        "domain": "openai.dev",
        "record": {"type": "TXT", "value": "echo-attest=vNext"},
    }
    print(preflight(demo))
