from __future__ import annotations

from typing import Dict, List

from revenue_mesh.hook_governance import authorize_billing
from .runtime import Receipt, RevenueMeshRuntime, Task


def _format_tasks(tasks: List[Task]) -> List[Dict[str, str]]:
    formatted = []
    for task in tasks:
        formatted.append(
            {
                "task_id": task.task_id,
                "client_id": task.client_id,
                "task_type": task.task_type,
                "status": task.status,
                "packaging": ",".join(sorted(task.packaging.keys())) if task.packaging else "pending",
            }
        )
    return formatted


def _format_receipts(receipts: List[Receipt]) -> List[Dict[str, str]]:
    formatted = []
    for receipt in receipts:
        formatted.append(
            {
                "receipt_id": receipt.receipt_id,
                "task_id": receipt.task_id,
                "client_id": receipt.client_id,
                "amount": f"{receipt.amount:.2f} {receipt.currency}",
                "issued_at": receipt.issued_at.isoformat(),
                "memo": receipt.memo,
            }
        )
    return formatted


def build_dashboard_snapshot(runtime: RevenueMeshRuntime, actor: str = "system") -> Dict[str, object]:
    """Offline-friendly dashboard payload showing income and job state."""

    authorize_billing(actor)

    total_income = sum(receipt.amount for receipt in runtime.receipts)
    recent_audit = [
        {
            "event": entry.event,
            "details": entry.details,
            "created_at": entry.created_at.isoformat(),
        }
        for entry in runtime.audit_log[-20:]
    ]

    return {
        "income": total_income,
        "clients": list(runtime.clients.keys()),
        "queued": _format_tasks(runtime.queue),
        "completed": _format_tasks(runtime.completed_tasks),
        "receipts": _format_receipts(runtime.receipts),
        "audit_trail": recent_audit,
        "plans": [{"name": plan.name, "price_per_task": plan.price_per_task, "currency": plan.currency} for plan in runtime.billing_plans.values()],
    }

