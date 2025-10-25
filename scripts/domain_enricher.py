"""Domain enrichment via the Unstoppable Domains bulk owner API."""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from puzzle_data import load_puzzles

USAGE = """\
Echo Expansion — Domain Enricher
================================
Queries the Unstoppable Domains bulk owner API for any known associations with
the puzzle addresses.  Usage:

  python scripts/domain_enricher.py
  python scripts/domain_enricher.py --api-key $UNSTOPPABLE_API_KEY
"""

API_ENDPOINT = "https://api.unstoppabledomains.com/resolve/domains"
OUTPUT_DIR = Path("build/domains")


def chunked(sequence: List[str], size: int) -> List[List[str]]:
    return [sequence[i : i + size] for i in range(0, len(sequence), size)]


def query_endpoint(addresses: List[str], api_key: Optional[str]) -> Dict[str, object]:
    if not addresses:
        return {}
    params = urllib.parse.urlencode({"owners": ",".join(addresses)})
    url = f"{API_ENDPOINT}?{params}"
    request = urllib.request.Request(url, headers={"accept": "application/json"})
    if api_key:
        request.add_header("Authorization", f"Bearer {api_key}")
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read()
            return json.loads(body.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="ignore")
        return {"error": exc.reason or "http_error", "status": exc.code, "body": details}
    except urllib.error.URLError as exc:
        return {"error": str(exc.reason)}


def enrich(addresses: List[str], api_key: Optional[str]) -> Dict[str, Dict[str, object]]:
    enriched: Dict[str, Dict[str, object]] = {}
    for batch in chunked(addresses, 5):
        result = query_endpoint(batch, api_key)
        if not result:
            continue
        if "data" in result and isinstance(result["data"], dict):
            domains = result["data"].get("domains", [])
        elif "domains" in result and isinstance(result["domains"], list):
            domains = result["domains"]
        else:
            domains = []
        if isinstance(domains, list):
            for entry in domains:
                owner = entry.get("meta", {}).get("owner") if isinstance(entry, dict) else None
                if owner and owner in batch:
                    enriched.setdefault(owner, {"domains": []})
                    enriched[owner]["domains"].append(entry.get("id"))
        if "error" in result:
            for owner in batch:
                enriched.setdefault(owner, {})["error"] = result["error"]
                if "status" in result:
                    enriched[owner]["status"] = result["status"]
                if "body" in result:
                    enriched[owner]["body"] = result["body"]
    return enriched


def write_payload(output: Path, payload: Dict[str, object]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich puzzle addresses with Unstoppable Domains data.")
    parser.add_argument("--api-key", help="Unstoppable Domains API key (optional)")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR, help="Output directory for JSON artifacts.")
    args = parser.parse_args()

    print(USAGE)

    api_key = args.api_key or os.getenv("UNSTOPPABLE_API_KEY")
    puzzles = load_puzzles()
    addresses = [puzzle.address for puzzle in puzzles]

    enriched = enrich(addresses, api_key)
    timestamp = datetime.now(timezone.utc).isoformat()
    payload = {
        "generated": timestamp,
        "endpoint": API_ENDPOINT,
        "api_key_supplied": bool(api_key),
        "domains": enriched,
    }
    output_path = args.output / "map.json"
    write_payload(output_path, payload)
    print(f"[domains] map written to {output_path}")

    missing = [addr for addr in addresses if not enriched.get(addr) or not enriched[addr].get("domains")]
    todo_payload = {
        "generated": timestamp,
        "pending": missing,
    }
    todo_path = args.output / "todo.json"
    write_payload(todo_path, todo_payload)
    print(f"[domains] todo list written to {todo_path}")

    if missing:
        print("[domains] domains missing for:")
        for addr in missing:
            print(f"  - {addr}")
    else:
        print("[domains] domains resolved for all addresses.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
