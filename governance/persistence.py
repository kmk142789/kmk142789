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


def clear_offline_state():
    """Remove cached governance artifacts to reset local state.

    This is primarily used in tests or when resetting the governance node. Any
    missing files will simply be recreated on the next persistence call.
    """

    for item in BASE.glob("*"):
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            for child in item.glob("**/*"):
                if child.is_file():
                    child.unlink()
            item.rmdir()


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


def load_audit_log():
    """Return the list of audit log events (chronological order)."""

    return load_json("audit_log.json").get("events", [])


# ---- Snapshots ---- #

def save_snapshot(state):
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    save_json(f"snapshot_{timestamp}.json", state)


def list_snapshots():
    """List available offline governance snapshots sorted by timestamp."""

    return sorted([path.name for path in BASE.glob("snapshot_*.json")])


def load_snapshot(name: str):
    """Load a specific snapshot by filename, or return an empty dict."""

    path = BASE / name
    if not path.exists():
        return {}
    with path.open() as fp:
        return json.load(fp)
