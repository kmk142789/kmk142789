from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from echo.atlas.temporal_ledger import TemporalLedger
from echo.pulseweaver.api import RateLimiter, create_router
from echo.pulseweaver.pulse_bus import PulseBus
from echo.pulseweaver.watchdog import RemediationResult, SelfHealingWatchdog
from echo.crypto import sign as sign_utils


def _derive_public_key(private_hex: str) -> str:
    secret = int(private_hex, 16)
    point = sign_utils._scalar_multiply(secret, sign_utils._SECP256K1_G)  # type: ignore[attr-defined]
    x, y = point  # type: ignore[misc]
    return (b"\x04" + x.to_bytes(32, "big") + y.to_bytes(32, "big")).hex()


def _build_app(tmp_path):
    private_key = "2" * 64
    public_key = _derive_public_key(private_key)

    def dry_run(event):
        return RemediationResult(success=True, notes=["dry"], details={})

    def real_run(event):
        return RemediationResult(
            success=True,
            proof={"id": "proof-xyz", "ts": datetime.now(timezone.utc).isoformat()},
            notes=["real"],
            details={},
        )

    watchdog = SelfHealingWatchdog(
        state_dir=tmp_path,
        dry_run_executor=dry_run,
        real_executor=real_run,
    )
    bus = PulseBus(state_dir=tmp_path, signing_key={"private_key": private_key, "key_id": "key"})
    bus.register_key("key", public_key)
    ledger = TemporalLedger(state_dir=tmp_path)
    limiter = RateLimiter(capacity=5, refill_rate=5)

    app = FastAPI()
    app.include_router(create_router(watchdog, bus, ledger, rate_limiter=limiter))
    return app, bus, ledger, watchdog


def test_api_endpoints(tmp_path):
    app, bus, ledger, watchdog = _build_app(tmp_path)
    client = TestClient(app)

    health = client.get("/pulse/health")
    assert health.status_code == 200
    assert health.json()["last_attempt"] is None

    repair = client.post("/pulse/repair", json={"reason": "tests", "event": {"status": "failure"}})
    assert repair.status_code == 200
    assert repair.json()["succeeded"] is True
    assert ledger.entries(), "ledger should record repair"

    # max attempts enforcement
    fail = client.post(
        "/pulse/repair",
        json={"reason": "tests", "event": {"status": "failure"}, "cooldown_seconds": 1000},
    )
    assert fail.status_code == 409

    outbox = bus.emit(
        repo="echo/example",
        ref="cafebabe",
        kind="merge",
        summary="merge",
        proof_id="proof-bus",
    )
    ingest = client.post("/pulse/ingest", json=outbox.envelope.model_dump(mode="json"))
    assert ingest.status_code == 200
    assert ingest.json()["proof_id"] == "proof-bus"

    entries = client.get("/ledger/entries")
    assert entries.status_code == 200
    assert entries.json()["entries"], "entries should be populated"

    graph = client.get("/ledger/graph.svg")
    assert graph.status_code == 200
    assert graph.text.startswith("<svg")

    bad_payload = outbox.envelope.model_dump(mode="json")
    bad_payload["signature"] = "0" * 64
    invalid = client.post("/pulse/ingest", json=bad_payload)
    assert invalid.status_code == 400


def test_rate_limit(tmp_path):
    app, bus, ledger, _watchdog = _build_app(tmp_path)
    limiter = RateLimiter(capacity=1, refill_rate=0)
    limited_app = FastAPI()
    limited_app.include_router(create_router(_watchdog, bus, ledger, rate_limiter=limiter))
    client = TestClient(limited_app)

    outbox = bus.emit(
        repo="echo/example",
        ref="cafebabe",
        kind="merge",
        summary="merge",
        proof_id="proof-rate",
    )
    ok = client.post("/pulse/ingest", json=outbox.envelope.model_dump(mode="json"))
    assert ok.status_code == 200
    denied = client.post("/pulse/ingest", json=outbox.envelope.model_dump(mode="json"))
    assert denied.status_code == 429
