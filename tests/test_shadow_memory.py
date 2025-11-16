from datetime import datetime, timedelta, timezone

from echo.memory.shadow import ShadowMemoryManager, ShadowMemoryPolicy
from echo.privacy.zk_layer import (
    EventCommitmentCircuit,
    HashCommitmentBackend,
    ZeroKnowledgePrivacyLayer,
)


def _fixed_clock(start: datetime):
    current = {"value": start}

    def now() -> datetime:
        return current["value"]

    def advance(delta: timedelta) -> None:
        current["value"] = current["value"] + delta

    return now, advance


def _privacy_layer() -> ZeroKnowledgePrivacyLayer:
    layer = ZeroKnowledgePrivacyLayer()
    layer.register_backend(HashCommitmentBackend())
    layer.register_circuit(EventCommitmentCircuit())
    return layer


def test_shadow_memory_manager_expires_records() -> None:
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    clock, advance = _fixed_clock(start)
    manager = ShadowMemoryManager(
        clock=clock,
        policy=ShadowMemoryPolicy(default_ttl_seconds=60, min_ttl_seconds=10, max_ttl_seconds=120),
    )

    manager.create_shadow_memory({"secret": "value"}, tags=["Launch / Signal"])
    snapshot = manager.snapshot()
    assert snapshot.active_count == 1
    assert snapshot.commitments

    advance(timedelta(seconds=90))
    snapshot = manager.snapshot()
    assert snapshot.active_count == 0


def test_shadow_memory_attestation_emits_proof() -> None:
    manager = ShadowMemoryManager(privacy_layer=_privacy_layer())
    manager.create_shadow_memory({"insight": "bridge"}, tags=["launch"])

    attestation = manager.attest_influence(decision_id="launch-sequence")
    assert attestation is not None
    assert attestation.proof is not None
    assert attestation.proof.verified
    assert attestation.record_ids
