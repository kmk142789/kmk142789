from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence

from revenue_mesh.hook_governance import authorize_billing
from services.revenue_mesh.billing import finish_job, start_job


@dataclass
class BillingPlan:
    """Represents a simple paid plan for agent work."""

    name: str
    currency: str = "USD"
    price_per_task: float = 0.0
    included_tasks: int = 0
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class Task:
    task_id: str
    client_id: str
    task_type: str
    payload: Dict[str, str]
    price: float
    status: str = "queued"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    packaging: Optional[Dict[str, str]] = None


@dataclass
class Receipt:
    receipt_id: str
    task_id: str
    client_id: str
    amount: float
    currency: str
    issued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    memo: str = ""


@dataclass
class AuditEntry:
    entry_id: str
    event: str
    details: Dict[str, str]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class RevenueMeshRuntime:
    """Layered runtime for billing, onboarding, routing, and packaging."""

    def __init__(self) -> None:
        self.billing_plans: Dict[str, BillingPlan] = {}
        self.clients: Dict[str, BillingPlan] = {}
        self.queue: List[Task] = []
        self.in_progress: List[Task] = []
        self.receipts: List[Receipt] = []
        self.audit_log: List[AuditEntry] = []
        self.completed_tasks: List[Task] = []

    def register_plan(self, plan: BillingPlan, actor: str = "system") -> None:
        authorize_billing(actor)
        self.billing_plans[plan.name] = plan
        self._audit("billing_plan_registered", {"plan": plan.name, "currency": plan.currency})

    def onboard_client(self, client_id: str, plan_name: str, actor: str = "system") -> None:
        authorize_billing(actor)
        if plan_name not in self.billing_plans:
            raise ValueError(f"Unknown billing plan: {plan_name}")
        self.clients[client_id] = self.billing_plans[plan_name]
        self._audit("client_onboarded", {"client_id": client_id, "plan": plan_name})

    def enqueue_task(
        self, client_id: str, task_type: str, payload: Optional[Dict[str, str]] = None, *, packaging_hint: str = ""
    ) -> Task:
        if client_id not in self.clients:
            raise ValueError(f"Client not onboarded: {client_id}")
        payload = payload or {}
        plan = self.clients[client_id]
        price = plan.price_per_task
        task = Task(
            task_id=str(uuid.uuid4()),
            client_id=client_id,
            task_type=task_type,
            payload={**payload, "packaging_hint": packaging_hint},
            price=price,
        )
        self.queue.append(task)
        self._audit("task_enqueued", {"task_id": task.task_id, "client_id": client_id, "task_type": task_type})
        return task

    def route_next_job(self) -> Optional[Task]:
        if not self.queue:
            return None
        task = self.queue.pop(0)
        task.status = "in_progress"
        self.in_progress.append(task)
        self._audit("task_routed", {"task_id": task.task_id, "client_id": task.client_id})
        return task

    def package_output(self, task_id: str, bundle: Dict[str, str]) -> Dict[str, str]:
        task = self._get_task(task_id)
        if task is None:
            raise ValueError(f"Unknown task: {task_id}")
        task.packaging = bundle
        task.status = "completed"
        if task in self.in_progress:
            self.in_progress.remove(task)
        self.completed_tasks.append(task)
        self._audit("output_packaged", {"task_id": task_id, "bundle_keys": ",".join(sorted(bundle.keys()))})
        return bundle

    def record_receipt(self, task_id: str, memo: str = "", actor: str = "system") -> Receipt:
        authorize_billing(actor)
        task = self._get_task(task_id)
        if task is None:
            raise ValueError(f"Unknown task: {task_id}")
        receipt = Receipt(
            receipt_id=str(uuid.uuid4()),
            task_id=task.task_id,
            client_id=task.client_id,
            amount=task.price,
            currency=self.clients[task.client_id].currency,
            memo=memo,
        )
        self.receipts.append(receipt)
        self._audit("receipt_issued", {"receipt_id": receipt.receipt_id, "task_id": task.task_id})
        return receipt

    def audit_entries(self, events: Optional[Sequence[str]] = None) -> List[AuditEntry]:
        if events is None:
            return list(self.audit_log)
        return [entry for entry in self.audit_log if entry.event in events]

    def snapshot(self) -> Dict[str, object]:
        return {
            "plans": list(self.billing_plans.values()),
            "clients": list(self.clients.keys()),
            "queued_tasks": len(self.queue),
            "in_progress_tasks": len(self.in_progress),
            "completed_tasks": len(self.completed_tasks),
            "receipts": len(self.receipts),
            "audit_events": len(self.audit_log),
        }

    def _get_task(self, task_id: str) -> Optional[Task]:
        for task in self.queue + self.in_progress + self.completed_tasks:
            if task.task_id == task_id:
                return task
        return None

    def _audit(self, event: str, details: Dict[str, str]) -> None:
        entry = AuditEntry(entry_id=str(uuid.uuid4()), event=event, details=details)
        self.audit_log.append(entry)


def run_paid_task(client_key: str, job_type: str, unit_price_cents: int, task_fn, **kwargs):
    job_id = start_job(client_key, job_type, unit_price_cents, metadata=kwargs)

    # Run the underlying agent task
    units = task_fn(**kwargs)  # e.g. returns "minutes used" or "files scanned"

    total = finish_job(job_id, units)
    return {"job_id": job_id, "units": units, "total_cents": total}

