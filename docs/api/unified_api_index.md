# Unified API Index

This index summarises the active HTTP interfaces that make up the Echo unified API surface. A machine-readable view lives alongside this document at [`unified_api_index.json`](./unified_api_index.json).

## Echo Computer Agent

- **Specification**: [`echo_computer_agent.openapi.json`](./echo_computer_agent.openapi.json)
- **Title / Version**: Echo Computer Agent API / 1.0.0
- **Description**: API for interacting with the Echo computer assistant agent.

| Method | Path | Purpose | Request body | Response payload |
| --- | --- | --- | --- | --- |
| GET | `/functions` | Enumerate the functions that the agent can call. | _None_ | `FunctionListResponse` containing `functions[]` entries that mirror backend tools. |
| POST | `/chat` | Submit a chat request that optionally executes a backend function. | `ChatRequest` with the user `message`, optional `inputs` object, and boolean `execute` flag. | `ChatResponse` describing the selected `function`, human-readable `message`, structured `data`, and contextual `metadata`. |

### Key Schemas

- **ChatRequest** — accepts the user-facing `message`, optional structured `inputs`, and an `execute` toggle to control whether the agent should run the resolved tool.  
- **ChatResponse** — returns the resolved `function`, explanatory `message`, structured `data`, and `metadata` payload.  
- **FunctionDescription** — captures the function `name`, human-readable `description`, JSON Schema `parameters`, and optional categorisation `metadata`.  
- **FunctionListResponse** — wraps an array of `FunctionDescription` entries and powers the `/functions` discovery call.

## Echo Universal Verifier

- **Implementation**: [`services/universal_verifier/app.py`](../../services/universal_verifier/app.py)
- **Title / Version**: Echo Universal Verifier / 0.1
- **Description**: FastAPI stub that deterministically evaluates Verifiable Credential payloads for downstream demonstrations.

| Method | Path | Purpose | Request body | Response payload |
| --- | --- | --- | --- | --- |
| POST | `/verify` | Validate a credential envelope and emit telemetry-friendly results. | JSON object with `format` (`"jwt-vc"` or `"jsonld-vc"`), arbitrary `credential` payload, and optional `options` map. | JSON object containing `ok`, the echoed `format`, static `checks` array, and `telemetry` metadata that tags the processing cycle and policy profile. |

### Integration Notes

- The service instruments traces, metrics, and logs via `observability.configure_otel`, exposing counters for request volume, failures, and latency histograms compatible with OTLP collectors.  
- Middleware records per-request latency and attaches HTTP attributes so dashboards can slice traffic across the unified surface.  
- Verification spans record success/failure outcomes, enriching cross-service views when combined with the agent chat telemetry.
