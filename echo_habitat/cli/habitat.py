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

    args = parser.parse_args()

    if args.cmd == "task":
        spec = {"kind": args.kind, "prompt": args.prompt}
        response = requests.post(f"{API}/task", json=spec, timeout=10)
        print(json.dumps(response.json(), indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
