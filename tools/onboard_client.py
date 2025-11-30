import json
import uuid
from pathlib import Path

CLIENT_REGISTRY = Path("clients/registry.json")
CLIENT_PROFILES_DIR = Path("clients/profiles")
CLIENT_PROFILES_DIR.mkdir(parents=True, exist_ok=True)

from echo_governance_core.mint_agent import mint_agent


def _load_registry():
    if not CLIENT_REGISTRY.exists():
        return {"clients": []}
    with CLIENT_REGISTRY.open() as fp:
        return json.load(fp)


def _save_registry(reg):
    with CLIENT_REGISTRY.open("w") as fp:
        json.dump(reg, fp, indent=2)


def onboard_client(name: str, services: list):
    reg = _load_registry()
    client_id = f"client.{uuid.uuid4().hex[:8]}"
    client_actor = f"{client_id}.actor"

    profile = {
        "id": client_id,
        "name": name,
        "services": services,
        "actor": client_actor,
    }

    # write profile
    profile_path = CLIENT_PROFILES_DIR / f"{client_id}.json"
    with profile_path.open("w") as fp:
        json.dump(profile, fp, indent=2)

    # update registry
    reg["clients"].append({
        "id": client_id,
        "name": name,
    })
    _save_registry(reg)

    # register governance actor (low-privilege client role; you can define one)
    mint_agent(client_actor, roles=[])

    return profile_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="client name")
    parser.add_argument("--services", nargs="+", required=True, help="services ids e.g. tech_support diagnostics")
    args = parser.parse_args()

    path = onboard_client(args.name, args.services)
    print("Client profile created at:", path)
