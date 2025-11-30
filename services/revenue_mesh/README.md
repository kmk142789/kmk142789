# Revenue Mesh Runtime (Billing → Onboarding → Job Routing → Output Packaging)

This module wires the revenue layer directly into agent execution. It is designed to:

1. Register billing plans and onboarding events.
2. Accept and route paid tasks through the runtime queue.
3. Emit packaged outputs and signed receipts.
4. Feed an offline dashboard so operations teams can track income, tasks, and audit trails without external dependencies.

## Runtime Layers
- **Billing (plans & receipts):** Define paid plans with per-task pricing and currency codes. Receipts capture the exact task, client, amount, and memo.
- **Onboarding:** Attach a client to a plan before any task enters the queue. Every onboarding is logged for auditability.
- **Job routing:** Tasks move from the queue to `in_progress` and then to `completed` once packaging is attached.
- **Output packaging:** Packaged bundles are linked to tasks and logged so downstream systems can store/export deliverables.

## Files
- `runtime.py` — in-memory runtime for billing plans, client onboarding, task queues, receipts, audit logs, and output packaging.
- `dashboard.py` — offline-friendly dashboard snapshot builder that summarizes income, tasks, receipts, and the audit trail.
- `__init__.py` — exports primary interfaces for reuse across services.

## Quickstart
```python
from services.revenue_mesh import BillingPlan, RevenueMeshRuntime, build_dashboard_snapshot

runtime = RevenueMeshRuntime()
runtime.register_plan(BillingPlan(name="pro", price_per_task=10.0))
runtime.onboard_client("acme", "pro")

# Billing → Onboarding → Job Routing → Output Packaging
queued = runtime.enqueue_task("acme", "diagnostics", {"target": "web-01"}, packaging_hint="zip")
next_job = runtime.route_next_job()
runtime.package_output(next_job.task_id, {"artifact": "s3://bucket/report.zip"})
runtime.record_receipt(next_job.task_id, memo="diagnostics run")

# Offline business dashboard
snapshot = build_dashboard_snapshot(runtime)
print(snapshot)
```

## Deployment Notes
- The runtime is intentionally dependency-light for embedding into FastAPI, CLI, or daemonized agents.
- Persist the receipts and audit log into the ledger/attestation folders in this repo to satisfy compliance and customer export requirements.
- Integrate dashboard snapshots into `pulse_dashboard/` or `pulse.json` to surface revenue and task state in existing observability pipelines.
