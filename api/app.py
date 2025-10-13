from datetime import datetime
import glob
import hashlib
import json
import os

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Echo Continuum (read-only)")

LEDGER_DIR = os.environ.get("ECHO_LEDGER_DIR", ".attest")


class VerifyRequest(BaseModel):
    context: str


@app.get("/health")
def health():
    return {"status": "ok", "ts": datetime.utcnow().isoformat() + "Z"}


@app.post("/api/verify")
def verify(req: VerifyRequest):
    digest = hashlib.sha256(req.context.encode("utf-8")).hexdigest()
    return {"sha256": digest, "context": req.context}


@app.get("/api/state")
def state(limit: int = 50):
    entries = []
    for p in sorted(glob.glob(os.path.join(LEDGER_DIR, "*.json")))[-limit:]:
        with open(p, "r") as f:
            try:
                entries.append(json.load(f))
            except Exception:
                continue
    return {"count": len(entries), "entries": entries}
