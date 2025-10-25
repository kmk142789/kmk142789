"""Domain Reality Bridge.

Attempts to resolve Unstoppable Domain mappings for known puzzle addresses and
falls back to synthetic lineage domains when the remote service is unavailable.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import time
import urllib.error
import urllib.request
from typing import Dict, Iterable, List

ROOT = pathlib.Path(__file__).resolve().parents[1]
PUZZLE_DIR = ROOT / "puzzle_solutions"
BUILD_DIR = ROOT / "build" / "domains"
ADDRESS_RE = re.compile(r"(?:^|`)((?:[13]|bc1)[0-9A-Za-z]{20,})")

API_ENDPOINT = "https://resolve.unstoppabledomains.com/reverse/"
API_KEY_ENV = "UNSTOPPABLE_API_KEY"


def _iter_addresses() -> Iterable[str]:
    addresses: List[str] = []
    for path in sorted(PUZZLE_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        addresses.extend(ADDRESS_RE.findall(text))
    seen = set()
    for address in addresses:
        if address not in seen:
            seen.add(address)
            yield address


def _synthetic_domain(address: str) -> str:
    digest = sum(ord(ch) for ch in address)
    return f"echo-{digest % 23:02d}.unstoppable"


def _query_remote(address: str) -> Dict[str, object] | None:
    url = API_ENDPOINT + address
    headers = {"accept": "application/json"}
    api_key = os.getenv(API_KEY_ENV)
    if api_key:
        headers["authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return {"status": "live", "domains": payload.get("data", [])}
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"status": "not_found", "domains": []}
    except Exception:
        return None
    return None


def resolve_domains() -> Dict[str, Dict[str, object]]:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    mapping: Dict[str, Dict[str, object]] = {}
    for address in _iter_addresses():
        record = _query_remote(address)
        if record is None or not record.get("domains"):
            record = {
                "status": "synthetic",
                "domains": [_synthetic_domain(address)],
            }
        record["address"] = address
        record["resolved_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        mapping[address] = record
        (BUILD_DIR / f"{address}.json").write_text(
            json.dumps(record, indent=2), encoding="utf-8"
        )
    index_path = BUILD_DIR / "index.json"
    index_path.write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    return mapping


def main() -> None:
    mapping = resolve_domains()
    print(f"Resolved domains for {len(mapping)} addresses.")


if __name__ == "__main__":
    main()
