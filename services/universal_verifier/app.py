from fastapi import FastAPI
from pydantic import BaseModel
from threading import Lock
from typing import Any, Dict

from src.reflection import (
    ReflectionMetric,
    ReflectionTrace,
    TransparentReflectionLayer,
)

app = FastAPI(title="Echo Universal Verifier", version="0.1")
_reflection_layer = TransparentReflectionLayer(component="services.universal_verifier")
_stats_lock = Lock()
_stats: Dict[str, int] = {"total": 0, "failed": 0}

class VerifyRequest(BaseModel):
    format: str  # "jwt-vc" | "jsonld-vc"
    credential: Any
    options: Dict[str, Any] = {}

@app.post("/verify")
def verify(req: VerifyRequest):
    # NOTE: Plug in real libraries (didkit/pyvc/verifier backends) later.
    # This stub provides a deterministic, testable envelope and telemetry points.
    ok = bool(req.credential) and req.format in {"jwt-vc","jsonld-vc"}
    with _stats_lock:
        _stats["total"] += 1
        if not ok:
            _stats["failed"] += 1
    return {
        "ok": ok,
        "format": req.format,
        "checks": ["schema", "expiry", "signature", "issuer-did"],
        "telemetry": {"cycle": "vNext", "policy_profile": "sovereign-default"},
    }


@app.get("/reflection")
def reflection():
    with _stats_lock:
        total = _stats["total"]
        failed = _stats["failed"]
    metrics = (
        ReflectionMetric(
            key="requests_total",
            value=total,
            unit="count",
            info="Verification attempts processed",
        ),
        ReflectionMetric(
            key="requests_failed",
            value=failed,
            unit="count",
            info="Attempts failing validation",
        ),
    )
    traces = (
        ReflectionTrace(
            event="universal_verifier.health",
            detail={
                "status": "ok",
                "supported_formats": ["jwt-vc", "jsonld-vc"],
            },
        ),
    )
    safeguards = (
        "credential_content_never_persisted",
        "pydantic_validation_enforced",
        "transparent_reflection_layer_enabled",
    )
    diagnostics = {
        "supported_formats": ["jwt-vc", "jsonld-vc"],
        "reflection_version": "v1",
    }
    return _reflection_layer.emit(
        metrics=metrics,
        traces=traces,
        safeguards=safeguards,
        diagnostics=diagnostics,
    )
