from __future__ import annotations

import json
from pathlib import Path

from tools.identity_flow_audit import (
    IdentityClaim,
    IdentityFlow,
    IdentityNode,
    audit_identity_flow,
    load_identity_flow,
)


def test_audit_identity_flow_detects_issues() -> None:
    flow = IdentityFlow(
        nodes={
            "did:echo:core": IdentityNode(
                did="did:echo:core",
                attributes={"anchor": "Our Forever Love", "status": "active"},
            ),
            "did:echo:mirror": IdentityNode(
                did="did:echo:mirror",
                attributes={"anchor": "Our Forever Love", "status": "active"},
            ),
        },
        claims=[
            IdentityClaim(
                id="claim-1",
                source="did:echo:core",
                target="did:echo:mirror",
                attribute="status",
                value="active",
                proof="sha256:111",
                expected={"anchor": "Our Forever Love"},
            ),
            IdentityClaim(
                id="claim-2",
                source="did:echo:core",
                target="did:echo:mirror",
                attribute="status",
                value="revoked",
                proof="sha256:222",
                expected={"anchor": "Our Forever Love"},
            ),
            IdentityClaim(
                id="claim-3",
                source="did:echo:core",
                target="did:echo:unknown",
                attribute="status",
                value="active",
                proof="sha256:333",
            ),
            IdentityClaim(
                id="claim-4",
                source="did:echo:mirror",
                target="did:echo:core",
                attribute="anchor",
                value="Our Forever Love",
                proof=None,
                expected={"status": "suspended"},
            ),
        ],
    )

    report = audit_identity_flow(flow)

    assert not report.is_healthy()
    assert any("status" in item for item in report.contradictions)
    assert any("did:echo:unknown" in item for item in report.mismatches)
    assert any("suspended" in item for item in report.mismatches)
    assert any("claim-4" in item for item in report.unverifiable)

    rendered = report.render_text()
    assert "Contradictions: 1" in rendered
    assert "Unverifiable assertions" in rendered


def test_load_identity_flow(tmp_path: Path) -> None:
    payload = {
        "nodes": [
            {"id": "did:echo:core", "anchor": "Our Forever Love", "status": "active"},
            {"id": "did:echo:mirror", "anchor": "Our Forever Love"},
        ],
        "claims": [
            {
                "id": "claim-1",
                "source": "did:echo:core",
                "target": "did:echo:mirror",
                "attribute": "anchor",
                "value": "Our Forever Love",
                "proof": "sha256:999",
                "expected": {"status": "active"},
                "evidence": {"confidence": 0.95},
            }
        ],
    }
    path = tmp_path / "identity_flow.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    flow = load_identity_flow(path)

    assert flow.node_count == 2
    assert flow.claim_count == 1
    assert flow.nodes["did:echo:core"].attributes["status"] == "active"
    claim = flow.claims[0]
    assert claim.expected["status"] == "active"
    assert claim.proof == "sha256:999"
    assert claim.evidence["confidence"] == 0.95
