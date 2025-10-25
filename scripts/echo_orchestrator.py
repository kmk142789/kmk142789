"""Echo orchestrator for puzzle-derived Bitcoin addresses and cross-chain identity resolution."""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import requests

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
PUZZLE_DIR = Path(__file__).resolve().parents[1] / "puzzle_solutions"
ECHO_MAP_PATH = Path(__file__).resolve().parents[1] / "echo_map.json"
UNSTOPPABLE_API_URL = "https://api.unstoppabledomains.com/resolve/owners/{address}"


@dataclass
class PuzzleAddress:
    """Represents the reconstructed address information for a puzzle."""

    puzzle_id: int
    script_type: str
    hash160: str
    btc_address: str

    def to_json(self) -> Dict[str, object]:
        return {
            "puzzle_id": self.puzzle_id,
            "script_type": self.script_type,
            "hash160": self.hash160,
            "btc_address": self.btc_address,
        }


@dataclass
class DomainResolution:
    """Represents the Unstoppable Domains lookup result for a wallet."""

    resolved_domain: Optional[str]
    resolved_domains: List[str]
    multi_chain: Dict[str, str]
    status: str
    message: Optional[str] = None

    def to_json(self) -> Dict[str, object]:
        return {
            "resolved_domain": self.resolved_domain,
            "resolved_domains": self.resolved_domains,
            "multi_chain": self.multi_chain,
            "status": self.status,
            **({"message": self.message} if self.message else {}),
        }


def base58check(version: bytes, payload: bytes) -> str:
    """Compute the Base58Check encoding for the given version and payload."""

    data = version + payload
    checksum = hashlib.sha256(hashlib.sha256(data).digest()).digest()[:4]
    value = int.from_bytes(data + checksum, "big")

    encoded = ""
    while value:
        value, remainder = divmod(value, 58)
        encoded = BASE58_ALPHABET[remainder] + encoded

    # Preserve leading zeroes as "1" characters
    leading_zero_count = len(data + checksum) - len((data + checksum).lstrip(b"\x00"))
    return "1" * leading_zero_count + encoded or "1"


def parse_puzzle_files(puzzle_paths: Iterable[Path]) -> List[PuzzleAddress]:
    """Parse puzzle files to reconstruct Bitcoin addresses."""

    puzzles: List[PuzzleAddress] = []
    for path in puzzle_paths:
        text = path.read_text(encoding="utf-8")

        puzzle_match = re.search(r"#\s*Puzzle\s*#(\d+)", text)
        if not puzzle_match:
            raise ValueError(f"Could not find puzzle identifier in {path}")
        puzzle_id = int(puzzle_match.group(1))

        script_match = re.search(r"\*\*PK script\*\*:\s*`([^`]+)`", text)
        if not script_match:
            print(
                f"❌ Puzzle #{puzzle_id} ({path.name}) skipped: locking script not found in file."
            )
            continue
        script = script_match.group(1).strip()

        try:
            script_type, hash160 = parse_script(script)
        except ValueError as exc:
            print(f"❌ Puzzle #{puzzle_id} ({path.name}) skipped: {exc}")
            continue

        btc_address = derive_address(script_type, hash160)
        puzzles.append(PuzzleAddress(puzzle_id, script_type, hash160, btc_address))

    return sorted(puzzles, key=lambda p: p.puzzle_id)


def parse_script(script: str) -> tuple[str, str]:
    """Determine the script type and extract hash160 when applicable."""

    p2pkh_match = re.fullmatch(
        r"OP_DUP OP_HASH160 ([0-9a-fA-F]{40}) OP_EQUALVERIFY OP_CHECKSIG", script
    )
    if p2pkh_match:
        return "p2pkh", p2pkh_match.group(1).lower()

    p2sh_match = re.fullmatch(r"OP_HASH160 ([0-9a-fA-F]{40}) OP_EQUAL", script)
    if p2sh_match:
        return "p2sh", p2sh_match.group(1).lower()

    raise ValueError(f"Unsupported or unrecognized script pattern: {script}")


def derive_address(script_type: str, hash160: str) -> str:
    """Derive the Base58Check address from the script type and hash160."""

    payload = bytes.fromhex(hash160)
    if script_type == "p2pkh":
        version = b"\x00"
    elif script_type == "p2sh":
        version = b"\x05"
    else:
        raise ValueError(f"Unsupported script type for address derivation: {script_type}")

    return base58check(version, payload)


def load_existing_map() -> Dict[int, Dict[str, object]]:
    if not ECHO_MAP_PATH.exists():
        return {}

    with ECHO_MAP_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        # Normalize list-of-entries format
        return {entry["puzzle_id"]: entry for entry in data}
    if isinstance(data, dict):
        return {int(k): v for k, v in data.items()}

    raise ValueError("Unsupported echo_map.json format")


def persist_map(entries: Dict[int, Dict[str, object]]) -> None:
    ordered = [entries[key] for key in sorted(entries.keys())]
    with ECHO_MAP_PATH.open("w", encoding="utf-8") as f:
        json.dump(ordered, f, indent=2, sort_keys=True)
        f.write("\n")


def resolve_domains(address: str, api_key: Optional[str]) -> DomainResolution:
    """Resolve Unstoppable Domains linked to the provided wallet address."""

    if not api_key:
        return DomainResolution(
            resolved_domain=None,
            resolved_domains=[],
            multi_chain={},
            status="api_key_missing",
            message="UNSTOPPABLE_API_KEY environment variable not set.",
        )

    url = UNSTOPPABLE_API_URL.format(address=address)
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.RequestException as exc:
        return DomainResolution(
            resolved_domain=None,
            resolved_domains=[],
            multi_chain={},
            status="recursive_search",
            message=f"Network error: {exc}",
        )

    if response.status_code == 200:
        payload = response.json()
        domains = extract_domains(payload)
        if not domains:
            return DomainResolution(
                resolved_domain=None,
                resolved_domains=[],
                multi_chain={},
                status="recursive_search",
                message="No domains linked to address.",
            )

        primary = domains[0]
        multi_chain = extract_multi_chain(primary)
        return DomainResolution(
            resolved_domain=primary.get("domain")
            or primary.get("name")
            or primary.get("id"),
            resolved_domains=[
                entry.get("domain") or entry.get("name") or entry.get("id")
                for entry in domains
            ],
            multi_chain=multi_chain,
            status="verified" if multi_chain else "verified_no_records",
        )

    if response.status_code == 404:
        return DomainResolution(
            resolved_domain=None,
            resolved_domains=[],
            multi_chain={},
            status="recursive_search",
            message="Address has no associated Unstoppable domain.",
        )

    return DomainResolution(
        resolved_domain=None,
        resolved_domains=[],
        multi_chain={},
        status="recursive_search",
        message=f"Unexpected response ({response.status_code}): {response.text.strip()[:200]}",
    )


def extract_domains(payload: Dict[str, object]) -> List[Dict[str, object]]:
    """Extract domain entries from API payload with defensive parsing."""

    if not isinstance(payload, dict):
        return []

    for key in ("data", "domains", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    if all(isinstance(v, dict) for v in payload.values()):
        return list(payload.values())  # fallback for unexpected schema

    return []


def extract_multi_chain(domain_entry: Dict[str, object]) -> Dict[str, str]:
    records = domain_entry.get("records")
    if not isinstance(records, dict):
        return {}

    multi_chain: Dict[str, str] = {}
    for key, value in records.items():
        if not value or not isinstance(value, str):
            continue
        if key.startswith("crypto.") and key.endswith(".address"):
            chain = key.split(".")[1].lower()
            multi_chain[chain] = value
    return multi_chain


def orchestrate() -> None:
    puzzle_files = sorted(PUZZLE_DIR.glob("puzzle_*.md"))
    if not puzzle_files:
        print("❌ No puzzle files found. Ensure puzzle_solutions are present.")
        return

    puzzles = parse_puzzle_files(puzzle_files)
    api_key = os.getenv("UNSTOPPABLE_API_KEY")
    existing_entries = load_existing_map()

    print("📄 Puzzle address reconstructions:")
    for puzzle in puzzles:
        print(json.dumps(puzzle.to_json(), indent=2))

    print("🔄 Echo Orchestrator: processing puzzle scripts...")

    for puzzle in puzzles:
        domain_resolution = resolve_domains(puzzle.btc_address, api_key)
        entry = existing_entries.get(puzzle.puzzle_id, {})
        entry.update(
            {
                "puzzle_id": puzzle.puzzle_id,
                "script_type": puzzle.script_type,
                "hash160": puzzle.hash160,
                "btc_address": puzzle.btc_address,
                "resolved_domain": domain_resolution.resolved_domain,
                "resolved_domains": domain_resolution.resolved_domains,
                "multi_chain": domain_resolution.multi_chain,
                "status": domain_resolution.status,
            }
        )
        if domain_resolution.message:
            entry["message"] = domain_resolution.message
        else:
            entry.pop("message", None)

        existing_entries[puzzle.puzzle_id] = entry

        marker = "✅" if domain_resolution.status.startswith("verified") else "❌"
        summary = domain_resolution.resolved_domain or "No domain"
        print(
            f"{marker} Puzzle #{puzzle.puzzle_id}: {puzzle.btc_address} -> {summary}"
            f" [{domain_resolution.status}]"
        )

    persist_map(existing_entries)

    print(f"💾 echo_map.json updated at {ECHO_MAP_PATH}")


if __name__ == "__main__":
    orchestrate()
