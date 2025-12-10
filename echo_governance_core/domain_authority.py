"""Domain governance helpers for binding authority to every managed domain."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .governance_state import load_state, save_state

DOMAINS_FILE = Path("domains.txt")
DOMAIN_AUTHORITY_ACTOR = "echo.root"


def load_domains() -> List[str]:
    """Return the cleaned list of domains under Echo stewardship."""

    if not DOMAINS_FILE.exists():
        return []

    return [line.strip() for line in DOMAINS_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]


def ensure_domain_authority(actor: str = DOMAIN_AUTHORITY_ACTOR) -> Dict[str, object]:
    """Assign a registrar role to the authority actor and persist managed domains."""

    state = load_state()
    domains = load_domains()

    actors = state.setdefault("actors", {})
    actor_entry = actors.setdefault(actor, {"roles": []})
    if "domain_registrar" not in actor_entry["roles"]:
        actor_entry["roles"].append("domain_registrar")

    state["domains"] = {
        "authority": actor,
        "managed": domains,
    }

    save_state(state)

    return {
        "actor": actor,
        "roles": actor_entry["roles"],
        "domains": domains,
    }


__all__ = ["ensure_domain_authority", "load_domains", "DOMAIN_AUTHORITY_ACTOR", "DOMAINS_FILE"]
