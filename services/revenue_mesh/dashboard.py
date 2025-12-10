"""Helpers for rendering or exporting revenue dashboard data."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from .runtime import AuditEntry, Receipt, Task


def _serialize_task(task: Task) -> Dict[str, object]:
    return {
        "task_id": task.task_id,
        "client_id": task.client_id,
        "task_type": task.task_type,
        "status": task.status,
        "price": task.price,
        "packaging": task.packaging,
        "created_at": task.created_at.isoformat(),
    }


def _serialize_receipt(receipt: Receipt) -> Dict[str, object]:
    return {
        "receipt_id": receipt.receipt_id,
        "task_id": receipt.task_id,
        "client_id": receipt.client_id,
        "amount": receipt.amount,
        "currency": receipt.currency,
        "memo": receipt.memo,
        "issued_at": receipt.issued_at.isoformat(),
    }


def _serialize_audit(entry: AuditEntry) -> Dict[str, object]:
    return {
        "entry_id": entry.entry_id,
        "event": entry.event,
        "details": entry.details,
        "created_at": entry.created_at.isoformat(),
    }


def build_dashboard_snapshot(runtime) -> Dict[str, object]:
    """Return a structured, serializable snapshot of the runtime state."""

    income = sum(receipt.amount for receipt in runtime.receipts)
    currency = runtime.receipts[0].currency if runtime.receipts else None

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "income": income,
        "currency": currency,
        "clients": list(runtime.clients.keys()),
        "queued": [_serialize_task(task) for task in runtime.queue],
        "in_progress": [_serialize_task(task) for task in runtime.in_progress],
        "completed": [_serialize_task(task) for task in runtime.completed_tasks],
        "receipts": [_serialize_receipt(receipt) for receipt in runtime.receipts],
        "audit": [_serialize_audit(entry) for entry in runtime.audit_log],
    }


__all__: List[str] = ["build_dashboard_snapshot"]
