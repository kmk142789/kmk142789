import pytest

from services.revenue_mesh import BillingPlan, RevenueMeshRuntime, build_dashboard_snapshot


def test_billing_onboarding_and_routing_flow():
    runtime = RevenueMeshRuntime()
    runtime.register_plan(BillingPlan(name="starter", price_per_task=5.0, currency="USD"))
    runtime.onboard_client("client-1", "starter")

    queued = runtime.enqueue_task("client-1", "triage", {"scope": "web"}, packaging_hint="tar")
    assert queued.status == "queued"
    assert runtime.snapshot()["queued_tasks"] == 1

    routed = runtime.route_next_job()
    assert routed is not None
    assert routed.status == "in_progress"
    assert runtime.snapshot()["queued_tasks"] == 0

    packaged = runtime.package_output(routed.task_id, {"report": "local://reports/web.tar"})
    assert "report" in packaged
    assert runtime.completed_tasks[0].status == "completed"

    receipt = runtime.record_receipt(routed.task_id, memo="triage complete")
    assert receipt.amount == pytest.approx(5.0)
    assert receipt.client_id == "client-1"

    audit_events = [entry.event for entry in runtime.audit_entries()]
    assert "client_onboarded" in audit_events
    assert "receipt_issued" in audit_events


def test_offline_dashboard_snapshot_contains_income_and_tasks():
    runtime = RevenueMeshRuntime()
    runtime.register_plan(BillingPlan(name="pro", price_per_task=12.5, currency="EUR"))
    runtime.onboard_client("acme", "pro")
    task = runtime.enqueue_task("acme", "analysis", {"asset": "db"})
    runtime.route_next_job()
    runtime.package_output(task.task_id, {"bundle": "ipfs://example"})
    runtime.record_receipt(task.task_id, memo="analysis")

    snapshot = build_dashboard_snapshot(runtime)
    assert snapshot["income"] == pytest.approx(12.5)
    assert snapshot["clients"] == ["acme"]
    assert snapshot["completed"][0]["status"] == "completed"
    assert snapshot["receipts"][0]["memo"] == "analysis"
