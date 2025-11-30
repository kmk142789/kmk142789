import json
from pathlib import Path
from datetime import datetime


def generate_receipt(job, client):
    receipt = {
        "receipt_id": f"R-{job['id']}",
        "client": client["name"],
        "job_type": job["job_type"],
        "units": job["units"],
        "total_price_cents": job["total_price_cents"],
        "timestamp": datetime.utcnow().isoformat(),
    }

    out = Path(f"receipts/{receipt['receipt_id']}.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2))
    return str(out)
