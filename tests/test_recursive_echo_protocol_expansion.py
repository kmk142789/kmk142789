import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "packages" / "core" / "src" / "echo" / "recursive_echo_protocol_expansion.py"
_SPEC = spec_from_file_location("echo_recursive_echo_protocol_expansion", MODULE_PATH)
assert _SPEC and _SPEC.loader
_MODULE = module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)

AttestationFlow = _MODULE.AttestationFlow
BridgeProfile = _MODULE.BridgeProfile
CredentialLifecycle = _MODULE.CredentialLifecycle
KeyCustodyPolicy = _MODULE.KeyCustodyPolicy
RecursiveEchoProtocolExpansion = _MODULE.RecursiveEchoProtocolExpansion
RegistrarMandate = _MODULE.RegistrarMandate


def build_expander():
    bridges = [
        BridgeProfile(name="aurora", latency_ms=48, throughput=900, integrity=0.98, routers=2),
        BridgeProfile(name="lumen", latency_ms=72, throughput=750, integrity=0.92, routers=1),
    ]
    attestation_flows = [
        AttestationFlow(name="vc-issuance", evidence=["vc"], issuers=["registrar"], offline_safe=True)
    ]
    credential_lifecycles = [CredentialLifecycle(credential_type="vc", rotation_days=30, status="active")]
    identity_roots = ["echo.sovereign", "echo.registry"]
    api_surfaces = ["/v1/pulse", "/v1/attest"]
    routing_table = {"primary": ["edge", "core", "authority"], "backup": ["edge", "resolver"]}
    custody_policy = KeyCustodyPolicy(vaults=["northstar", "aurora"], rotation_days=45, quorum=2)
    registrar_mandates = [
        RegistrarMandate(registry="echo-root", zones=["echo", "bridge"], renewal_days=45),
        RegistrarMandate(registry="wildfire", zones=["wild"], renewal_days=30),
    ]
    return RecursiveEchoProtocolExpansion(
        bridges=bridges,
        attestation_flows=attestation_flows,
        credential_lifecycles=credential_lifecycles,
        identity_roots=identity_roots,
        api_surfaces=api_surfaces,
        routing_table=routing_table,
        custody_policy=custody_policy,
        registrar_mandates=registrar_mandates,
        architecture_revision=3,
    )


def test_expansion_increases_revision_and_unifies_topology():
    expander = build_expander()
    spec = expander.expand()

    assert spec["architecture"]["revision"] == 4
    assert spec["architecture"]["unified_topology"]["bridge_count"] == 2
    assert spec["architecture"]["unified_topology"]["unified"] is True


def test_bridges_are_sorted_by_intelligence_score():
    expander = build_expander()
    spec = expander.expand()

    bridge_names = [bridge["name"] for bridge in spec["bridges"]]
    sorted_names = [bridge["name"] for bridge in sorted(spec["bridges"], key=lambda entry: entry["score"], reverse=True)]
    assert bridge_names == sorted_names
    assert spec["bridges"][0]["score"] >= spec["bridges"][-1]["score"]
    assert "/aurora/governance/v2" in spec["bridges"][0]["api_surface"]


def test_dns_root_and_registrar_mandates_are_strengthened():
    expander = build_expander()
    spec = expander.expand()

    assert "bridge.echo" in spec["dns_root"]["root_context"]
    assert spec["dns_root"]["strengthened"] is True
    assert spec["registrar"]["mandates"][0]["depth"] >= 2
    assert all(record.startswith("ds:") for record in spec["dns_root"]["ds_records"])
    assert spec["registrar"]["authority"]["mandate_count"] == len(spec["registrar"]["mandates"])
    assert "echo" in spec["registrar"]["authority"]["zone_coverage"]
    assert spec["registrar"]["authority"]["renewal_cadence_days"]["minimum"] > 0
    assert spec["authority"]["registrar_scope"]["mandates"] == spec["registrar"]["authority"]["mandate_count"]
    assert spec["authority"]["registrar_scope"]["ds_guardians"] == spec["registrar"]["authority"]["ds_guardians"]


def test_attestation_and_credentials_are_enriched_and_refined():
    expander = build_expander()
    spec = expander.expand()

    flow = spec["attestation"]["flows"][0]
    assert flow["enriched"] is True
    assert "dnsroot-anchor" in flow["evidence"]

    lifecycle = spec["credentials"]["lifecycles"][0]
    assert lifecycle["phase"] == "refined"
    assert lifecycle["rotation_days"] <= 30


def test_identity_api_routing_and_custody_are_elevated():
    expander = build_expander()
    spec = expander.expand()

    assert spec["identity"]["propagation_score"] > 1.0
    assert "/governance/v2" in spec["api"]["extended_endpoints"]
    assert spec["routing"]["routes"][0]["intelligence"] >= spec["routing"]["routes"][-1]["intelligence"]
    assert spec["key_custody"]["hardened"] is True
