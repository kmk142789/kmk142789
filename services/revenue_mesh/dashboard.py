from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING, Dict, List

from .billing import get_conn

if TYPE_CHECKING:
    from services.revenue_mesh.runtime import Receipt, RevenueMeshRuntime, Task


def _serialize_tasks(tasks: List["Task"]) -> List[Dict[str, object]]:
    return [asdict(task) for task in tasks]


def _serialize_receipts(receipts: List["Receipt"]) -> List[Dict[str, object]]:
    return [asdict(receipt) for receipt in receipts]


def build_dashboard_snapshot(runtime: "RevenueMeshRuntime") -> Dict[str, object]:
    """Return a lightweight snapshot of runtime income and task progress."""

    income = sum(receipt.amount for receipt in runtime.receipts)
    return {
        "income": income,
        "clients": list(runtime.clients.keys()),
        "queued": _serialize_tasks(runtime.queue),
        "in_progress": _serialize_tasks(runtime.in_progress),
        "completed": _serialize_tasks(runtime.completed_tasks),
        "receipts": _serialize_receipts(runtime.receipts),
        "audit_events": [asdict(entry) for entry in runtime.audit_log],
    }


def format_currency(cents: int) -> str:
    return f"${cents / 100:.2f}"


def main():
    with get_conn() as conn:
        print("=== Echo Revenue Mesh — Snapshot ===\n")

        total = conn.execute(
            "SELECT COALESCE(SUM(total_price_cents), 0) AS s FROM jobs WHERE status='completed'"
        ).fetchone()["s"]
        print(f"Total billed work: {format_currency(total)}")

        paid = conn.execute(
            "SELECT COALESCE(SUM(amount_cents), 0) AS s FROM payments"
        ).fetchone()["s"]
        print(f"Total payments recorded: {format_currency(paid)}")

        print("\nTop clients:")
        rows = conn.execute(
            """
            SELECT c.name, c.plan,
                   COALESCE(SUM(j.total_price_cents), 0) AS billed
              FROM clients c
         LEFT JOIN jobs j ON j.client_id=c.id
          GROUP BY c.id
          ORDER BY billed DESC
          LIMIT 10
            """
        ).fetchall()

        for r in rows:
            print(f" - {r['name']} [{r['plan']}] → {format_currency(r['billed'])}")

        print("\nRecent jobs:")
        jobs = conn.execute(
            """
            SELECT j.id, c.name, j.job_type, j.status, j.total_price_cents
              FROM jobs j
              JOIN clients c ON c.id=j.client_id
          ORDER BY j.id DESC
             LIMIT 10
            """
        ).fetchall()

        for j in jobs:
            print(
                f" #{j['id']:04d} {j['name']} / {j['job_type']} / {j['status']} / {format_currency(j['total_price_cents'])}"
            )


if __name__ == "__main__":
    main()
