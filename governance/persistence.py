import json
from datetime import datetime
from pathlib import Path

BASE = Path(".offline_state")
BASE.mkdir(exist_ok=True)

def load_json(file: str):
    path = BASE / file
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)

def save_json(file: str, data):
    path = BASE / file
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ---- Governance Objects ---- #

def load_policies():
    return load_json("policies.json")

def save_policies(policies):
    save_json("policies.json", policies)

def load_roles():
    return load_json("roles.json")

def save_roles(roles):
    save_json("roles.json", roles)

# ---- Audit Log ---- #

def log_action(actor, action, details):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "actor": actor,
        "action": action,
        "details": details,
    }
    log = load_json("audit_log.json")
    log.setdefault("events", []).append(entry)
    save_json("audit_log.json", log)

# ---- Snapshots ---- #

def save_snapshot(state):
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    save_json(f"snapshot_{timestamp}.json", state)
