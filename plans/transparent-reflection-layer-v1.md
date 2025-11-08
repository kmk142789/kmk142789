# Transparent Reflection Layer – v1 Architecture

## Objectives

* Provide a consistent interface for reflection snapshots across CLI tooling, background
  services, and dashboards.
* Capture metrics, tracing breadcrumbs, and safeguard declarations in a sanitised payload
  that can be emitted locally or forwarded to the ethical telemetry pipeline.
* Define endpoints and deployment expectations so the layer can be operated alongside
  existing Echo observability systems without exposing sensitive data.

## Core Components

### 1. Reflection Primitives (`src/reflection/`)

* `ReflectionMetric`, `ReflectionTrace`, and `ReflectionSnapshot` encapsulate structured
  data for reflection events. Field names intentionally avoid personal identifiers so they
  satisfy the telemetry schema guardrails.
* `TransparentReflectionLayer` coordinates emission, handles optional telemetry routing via
  `TelemetryCollector`, and enforces field whitelisting.
* Metrics capture scalar insights (counts, durations). Traces carry contextual breadcrumbs
  that explain why the snapshot was produced. Safeguards enumerate active protections such
  as encryption, credential redaction, or consent enforcement.

### 2. Runtime Integrations

* `WorkerHive` exposes `reflection()` and `WorkerTaskHandle.reflect()` so CLI tasks can emit
  snapshots alongside existing lifecycle events.
* `PulseWeaverService` emits reflection snapshots when building ledgers, surfacing phantom
  and atlas diagnostics.
* `services/universal_verifier` provides an HTTP `/reflection` endpoint returning the same
  snapshot schema, including request counters and safeguard assertions.

### 3. Telemetry + Storage

* `TransparentReflectionLayer.emit()` optionally accepts a `TelemetryCollector` and
  `TelemetryContext`. When provided, events are persisted as `reflection.snapshot`
  telemetry with whitelisted fields.
* For v1 the layer defaults to in-process emission. Future iterations should wire the
  collector to `JsonlTelemetryStorage` or a consent-aware aggregator.

## Metrics & Tracing Model

| Metric Key            | Description                                     | Example Source           |
|-----------------------|-------------------------------------------------|--------------------------|
| `requests_total`      | Total API invocations observed                  | Universal Verifier       |
| `ledger_events`       | Ledger fragments included in a snapshot         | Pulse Weaver             |
| `voyage_atlases`      | Number of voyage atlases rendered               | `echo_cli` refresh cmd   |

Tracing events follow the `namespace.action` convention (e.g.
`universal_verifier.health`, `pulse_weaver.snapshot`). Each trace may include a small,
non-sensitive detail map.

## Safeguard Endpoints

The layer defines an HTTP surface (`/reflection`) to expose:

* Component metrics, traces, and safeguards (as above).
* Diagnostics such as supported credential formats, atlas sources, or generated report
  paths. Diagnostics must remain free of personal identifiers.
* A `reflection_version` key so clients can perform schema negotiation.

Services exposing the endpoint must advertise the port in deployment manifests and ensure
standard authentication mechanisms guard access where required.

## Operational Considerations

1. **Consent propagation:** When telemetry is enabled, the component must provide a
   `TelemetryContext` carrying consent state before calling `emit()`.
2. **Storage:** Align persistence with existing `JsonlTelemetryStorage` paths so reflections
   appear alongside Worker Hive events.
3. **Security:** Safeguard declarations should be continuously verified in automated tests
   (see new security regression tests under `tests/`).
4. **Rollout:** Update deployment manifests to map a stable port (suggested 8400 series) and
   document rollout steps in `docs/` and `CHANGELOG.md`.

## Next Steps

* Extend additional CLI commands and services with reflection emissions.
* Implement a background job that aggregates snapshot diagnostics into
  `reports/data/reflection_transparency.json`.
* Integrate reflection telemetry into the dashboard UI for operator visibility.
