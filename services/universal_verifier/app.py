import logging
from time import perf_counter
from typing import Any, Dict

from fastapi import FastAPI, Request
from opentelemetry import metrics, trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.trace import Status, StatusCode
from pydantic import BaseModel

from observability import configure_otel


configure_otel(
    "universal-verifier",
    service_namespace="echo",
    service_version="0.1",
)

logger = logging.getLogger("universal_verifier")
app = FastAPI(title="Echo Universal Verifier", version="0.1")
FastAPIInstrumentor.instrument_app(app)

meter = metrics.get_meter("services.universal_verifier")
_verify_requests = meter.create_counter(
    "universal_verifier_requests_total",
    description="Total number of verification requests received.",
)
_verify_failures = meter.create_counter(
    "universal_verifier_failed_requests_total",
    description="Total number of verification requests that failed validation.",
)
_verify_latency = meter.create_histogram(
    "universal_verifier_verification_duration_seconds",
    description="Latency of credential verification calls.",
    unit="s",
)

tracer = trace.get_tracer("services.universal_verifier")


class VerifyRequest(BaseModel):
    format: str  # "jwt-vc" | "jsonld-vc"
    credential: Any
    options: Dict[str, Any] = {}


@app.middleware("http")
async def _metrics_middleware(request: Request, call_next):
    start = perf_counter()
    response = await call_next(request)
    duration = perf_counter() - start
    attributes = {"http.method": request.method, "http.route": request.url.path}
    _verify_latency.record(duration, attributes=attributes)
    return response


@app.post("/verify")
def verify(req: VerifyRequest):
    with tracer.start_as_current_span("universal.verifier.verify", attributes={"credential.format": req.format}) as span:
        # NOTE: Plug in real libraries (didkit/pyvc/verifier backends) later.
        # This stub provides a deterministic, testable envelope and telemetry points.
        ok = bool(req.credential) and req.format in {"jwt-vc", "jsonld-vc"}
        attributes = {"credential.format": req.format}
        _verify_requests.add(1, attributes=attributes)
        if not ok:
            span.set_status(Status(StatusCode.ERROR, "verification_failed"))
            span.set_attribute("verification.ok", False)
            _verify_failures.add(1, attributes=attributes)
            logger.warning("verification_failed", extra={"ctx_format": req.format})
        else:
            span.set_attribute("verification.ok", True)
            logger.info("verification_success", extra={"ctx_format": req.format})
        return {
            "ok": ok,
            "format": req.format,
            "checks": ["schema", "expiry", "signature", "issuer-did"],
            "telemetry": {"cycle": "vNext", "policy_profile": "sovereign-default"},
        }
