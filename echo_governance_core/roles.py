"""Role definitions for the offline governance core."""

ROLES = {
    "superadmin": {
        "can": ["*"],
    },
    "agent_runtime": {
        "can": [
            "run:*",
            "spawn_agent",
            "read_metrics",
            "write_logs",
        ],
    },
    "billing_agent": {
        "can": [
            "billing_access",
            "issue_receipt",
            "view_transactions",
        ],
    },
    "mesh_agent": {
        "can": ["mesh:discover", "mesh:sync", "mesh:handoff"],
    },
    "os_agent": {
        "can": ["os:load_model", "os:memory_write", "os:spawn"],
    },
    "alignment_agent": {
        "can": ["alignment:update", "alignment:read"],
    },
    "domain_registrar": {
        "can": [
            "domain:*",
            "dns:*",
            "registrar:*",
        ],
    },
}

__all__ = ["ROLES"]
