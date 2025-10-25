#!/usr/bin/env python3
import argparse
import json

import requests

API = "http://localhost:8000"


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    new = sub.add_parser("task")
    new.add_argument("kind")
    new.add_argument("prompt")

    forge_parser = sub.add_parser("forge")
    forge_sub = forge_parser.add_subparsers(dest="forge_cmd")
    spawn = forge_sub.add_parser("spawn")
    spawn.add_argument("archetype")
    spawn.add_argument("intent", nargs=argparse.REMAINDER, help="Optional natural-language intent")

    health = forge_sub.add_parser("health")
    health.add_argument("bot_id")

    args = parser.parse_args()

    if args.cmd == "task":
        spec = {"kind": args.kind, "prompt": args.prompt}
        response = requests.post(f"{API}/task", json=spec, timeout=10)
        print(json.dumps(response.json(), indent=2))
    elif args.cmd == "forge":
        if args.forge_cmd == "spawn":
            intent = " ".join(args.intent).strip()
            payload = {"archetype": args.archetype, "intent": intent}
            response = requests.post(f"{API}/forge/spawn", json=payload, timeout=10)
            data = response.json()
            if response.ok and data.get("bot_id"):
                try:
                    health_resp = requests.get(
                        f"{API}/forge/{data['bot_id']}/health",
                        timeout=10,
                    )
                    if health_resp.ok:
                        data["health"] = health_resp.json()
                except requests.RequestException:
                    data.setdefault("health", {"error": "health-check failed"})
            print(json.dumps(data, indent=2))
        elif args.forge_cmd == "health":
            response = requests.get(f"{API}/forge/{args.bot_id}/health", timeout=10)
            print(json.dumps(response.json(), indent=2))
        else:
            forge_parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
