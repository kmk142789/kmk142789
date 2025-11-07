# Ethical Telemetry Layer

The ethical telemetry layer respects participant consent and ensures that
any instrumentation remains pseudonymous.

## Configuration

- Toggle collection with `ETHICAL_TELEMETRY_ENABLED` (default `false`).
- Define the pseudonymisation salt via `ETHICAL_TELEMETRY_SALT`.
- Enforce explicit consent flows using `ETHICAL_TELEMETRY_REQUIRE_OPT_IN`.
- File paths and retention policies live in `config/ethical_telemetry.yml`.

## Data Collection

Use `src.telemetry.TelemetryCollector` with a storage backend
(`JsonlTelemetryStorage` or `InMemoryTelemetryStorage`).
Only contexts with `ConsentState.OPTED_IN` are persisted, preventing
accidental capture of opt-out sessions.

## Self-Assessment

`src.self_assessment.ReportEmitter` consumes telemetry events to produce
compliance reports.  Reports surface metrics such as opt-in ratios and
unknown consent events so downstream tooling can validate privacy
expectations.

## Review Tools

Run `python tools/telemetry_review.py --help` to inspect stored events,
export compliance reports, and audit consent records safely.
