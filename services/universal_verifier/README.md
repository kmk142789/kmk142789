# Echo Universal Verifier

A lightweight FastAPI stub that returns deterministic responses for Verifiable Credential (VC) verification requests.
It exists so other packages can exercise a "verification" service without pulling in heavyweight cryptography
libraries. The stub keeps the interface stable while the real implementation is designed.

## HTTP API

The application lives in [`app.py`](app.py) and exposes a single `POST /verify` endpoint. Requests must include:

- `format`: either `"jwt-vc"` or `"jsonld-vc"`.
- `credential`: any JSON payload representing the credential under test.
- `options` *(optional)*: arbitrary key/value pairs. They are accepted to mirror typical VC verifier
  interfaces but are ignored by the stub.

A successful request returns a JSON body similar to:

```json
{
  "ok": true,
  "format": "jwt-vc",
  "checks": ["schema", "expiry", "signature", "issuer-did"],
  "telemetry": {"cycle": "vNext", "policy_profile": "sovereign-default"}
}
```

If `format` is not recognised or the credential body is empty, `ok` is set to `false`.
No network calls or cryptography are performed – the response is fully deterministic.

## Running the service locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

The server listens on `http://127.0.0.1:8000`. You can exercise the endpoint with `curl`:

```bash
curl -X POST http://127.0.0.1:8000/verify \
  -H "Content-Type: application/json" \
  -d '{
        "format": "jwt-vc",
        "credential": {"sub": "did:example:123", "nbf": 1715126400}
      }'
```

## Relationship to the Echo Evolver

The wider project uses EchoEvolver to simulate artefact generation and network propagation.
That engine has moved away from filesystem and socket side effects in favour of in-memory simulations.
The verifier follows the same principle: results are pure data structures that higher-level orchestration can
consume during tests, demos, or documentation builds without requiring elevated permissions.

Future work may swap the stub for a real verifier backend; the request and response envelopes documented
here are intended to remain stable so the transition can happen without breaking downstream consumers.
