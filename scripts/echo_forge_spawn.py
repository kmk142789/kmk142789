#!/usr/bin/env python3
"""Convenience script to invoke the Echo Habitat Bot Forge."""

import argparse
import json
import os

import requests

DEFAULT_API = "http://localhost:8000"


def main() -> None:
    parser = argparse.ArgumentParser(description="Spawn a forged worker via the Orchestrator API")
    parser.add_argument("archetype", help="codesmith|testpilot|archivist|storyweaver")
    parser.add_argument(
        "intent",
        nargs=argparse.REMAINDER,
        help="optional natural-language intent for the forged bot",
    )
    parser.add_argument(
        "--api",
        default=os.getenv("ECHO_FORGE_API", DEFAULT_API),
        help="Override the orchestrator API base URL",
    )
    args = parser.parse_args()

    intent = " ".join(args.intent).strip()
    payload = {"archetype": args.archetype, "intent": intent}
    response = requests.post(f"{args.api}/forge/spawn", json=payload, timeout=15)
    data = response.json()

    if response.ok and data.get("bot_id"):
        try:
            health = requests.get(f"{args.api}/forge/{data['bot_id']}/health", timeout=15)
            if health.ok:
                data["health"] = health.json()
        except requests.RequestException as exc:  # pragma: no cover - network best-effort
            data.setdefault("health", {"error": str(exc)})

    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
