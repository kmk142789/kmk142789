import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from services.revenue_mesh.receipts import generate_receipt

DB_PATH = Path("services/revenue_mesh/revenue.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    schema_path = Path("services/revenue_mesh/schema.sql")
    with get_conn() as conn, schema_path.open() as fp:
        conn.executescript(fp.read())


def register_client(name: str, contact: str, plan: str, client_key: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO clients (client_key, name, contact, plan) VALUES (?, ?, ?, ?)",
            (client_key, name, contact, plan),
        )
        conn.commit()


def start_job(client_key: str, job_type: str, unit_price_cents: int, metadata: dict):
    with get_conn() as conn:
        client = conn.execute(
            "SELECT id FROM clients WHERE client_key=?", (client_key,),
        ).fetchone()
        if not client:
            raise ValueError(f"Unknown client_key {client_key}")

        cur = conn.execute(
            """
            INSERT INTO jobs (client_id, job_type, status, unit_price_cents, metadata)
            VALUES (?, ?, 'running', ?, ?)
            """,
            (client["id"], job_type, unit_price_cents, json.dumps(metadata)),
        )
        conn.commit()
        return cur.lastrowid


def finish_job(job_id: int, units: int):
    with get_conn() as conn:
        job = conn.execute(
            "SELECT unit_price_cents, client_id FROM jobs WHERE id=?", (job_id,),
        ).fetchone()
        if not job:
            raise ValueError(f"Unknown job {job_id}")

        total = units * job["unit_price_cents"]
        conn.execute(
            """
            UPDATE jobs
               SET status='completed',
                   finished_at=?,
                   units=?,
                   total_price_cents=?
             WHERE id=?
            """,
            (datetime.utcnow().isoformat(), units, total, job_id),
        )
        updated_job = conn.execute(
            "SELECT * FROM jobs WHERE id=?", (job_id,),
        ).fetchone()
        client = conn.execute(
            "SELECT * FROM clients WHERE id=?", (job["client_id"],),
        ).fetchone()
        receipt_path = generate_receipt(updated_job, client)
        conn.commit()
        return total, receipt_path


def record_payment(client_key: str, amount_cents: int, method: str, reference: str = ""):
    with get_conn() as conn:
        client = conn.execute(
            "SELECT id FROM clients WHERE client_key=?", (client_key,),
        ).fetchone()
        if not client:
            raise ValueError(f"Unknown client_key {client_key}")

        conn.execute(
            """
            INSERT INTO payments (client_id, amount_cents, method, reference)
            VALUES (?, ?, ?, ?)
            """,
            (client["id"], amount_cents, method, reference),
        )
        conn.commit()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "init_db":
        init_db()
        print("Initialized revenue database")
