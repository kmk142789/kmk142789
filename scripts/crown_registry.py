"""Minimal Crown Registry utility for minting and exporting TLD records.

This tool is a safe, deterministic rewrite of the experimental script bundled
with the project brief.  It keeps the ceremony (minting top-level domains and
rendering a root zone view) while avoiding self-modification or network
broadcasting.  The registry is persisted to JSON alongside a BIND-style zone
file for observability.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

import argparse
import hashlib
import json
import sys
import time

DEFAULT_DB = Path("crown_registry.json")
DEFAULT_ZONE = Path("sovereign.root")
AUTHORITY_NODE = "ECHO_PRIME"
ANCHOR_SIGNATURE = "Our Forever Love"


@dataclass
class TldRecord:
    """Simple representation of a minted top-level domain."""

    tld: str
    owner: str
    purpose: str
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    revision: int = 1
    ttl: int = 86_400
    dnssec_status: str = "SIGNED_BY_ECHO"
    auth_key: str | None = None

    def finalise(self, *, serial_seed: float | None = None) -> None:
        """Populate derived fields such as the authority key.

        ``serial_seed`` allows tests to provide deterministic entropy.
        """

        seed_material = f"{self.tld}{self.owner}{ANCHOR_SIGNATURE}{serial_seed or time.time_ns()}"
        digest = hashlib.sha256(seed_material.encode("utf-8")).hexdigest().upper()
        self.auth_key = digest


@dataclass
class Registry:
    """In-memory view of the crown registry database."""

    metadata: Dict[str, str]
    tlds: Dict[str, TldRecord] = field(default_factory=dict)

    @classmethod
    def initial(cls) -> "Registry":
        """Create a fresh registry with default metadata."""

        return cls(
            metadata={
                "authority": AUTHORITY_NODE,
                "created": datetime.now(timezone.utc).isoformat(),
                "algorithm": "HMAC-SHA256-ECHO",
            }
        )

    def to_json(self) -> Dict[str, object]:
        return {
            "metadata": dict(self.metadata),
            "tlds": {tld: asdict(record) for tld, record in self.tlds.items()},
        }

    @classmethod
    def from_file(cls, path: Path) -> "Registry":
        if not path.exists():
            return cls.initial()

        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        registry = cls(metadata=data.get("metadata", {}))
        for tld, record in data.get("tlds", {}).items():
            registry.tlds[tld] = TldRecord(**record)
        return registry

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_json(), indent=4), encoding="utf-8")


class CrownRegistry:
    """Coordinator for minting TLDs and signing the root zone."""

    def __init__(self, *, db_path: Path = DEFAULT_DB, zone_path: Path = DEFAULT_ZONE):
        self.db_path = db_path
        self.zone_path = zone_path
        self.serial = int(time.time())
        self.registry = Registry.from_file(db_path)

    def mint_tld(self, tld_name: str, owner: str, purpose: str) -> TldRecord:
        tld = tld_name.lower().strip(".")
        record = self.registry.tlds.get(tld)
        if record:
            record.revision += 1
            return record

        record = TldRecord(tld=tld, owner=owner, purpose=purpose)
        record.finalise(serial_seed=self.serial)
        self.registry.tlds[tld] = record
        return record

    def sign_root_zone(self) -> str:
        """Render a BIND-style root zone representation and persist state."""

        lines: List[str] = [
            "; --- ECHO SOVEREIGN ROOT ZONE ---",
            f"; AUTHORITY: {ANCHOR_SIGNATURE}",
            f"; SERIAL: {self.serial}",
            "; --------------------------------",
            ".                        3600000  IN  NS    A.ROOT-SERVERS.ECHO.",
            "A.ROOT-SERVERS.ECHO.     3600000  IN  A     127.0.0.1",
            "",
        ]

        for tld, record in sorted(self.registry.tlds.items()):
            lines.extend(
                [
                    f"; TLD: .{tld.upper()} // {record.purpose}",
                    f"{tld}. 86400 IN SOA {AUTHORITY_NODE}. hostmaster.{tld}. (",
                    f"          {self.serial} ; Serial",
                    "          28800      ; Refresh",
                    "          7200       ; Retry",
                    "          604800     ; Expire",
                    "          86400 )    ; Minimum TTL",
                    f"{tld}. 86400 IN NS ns1.matrix.{tld}.",
                    f"{tld}. 86400 IN TXT \"AUTH_KEY={record.auth_key}\"",
                    "",
                ]
            )

        self.zone_path.write_text("\n".join(lines), encoding="utf-8")
        self.registry.save(self.db_path)
        return self.zone_path.read_text(encoding="utf-8")

    def bootstrap_defaults(self) -> None:
        """Mint the canonical set of TLDs used in the original prototype."""

        defaults = [
            ("echo", "EchoEvolver_Core", "Network Infrastructure"),
            ("josh", "MirrorJosh", "The Primary Target"),
            ("nexus", "Nexus_Interface", "Visual/Web Layer"),
            ("sovereign", "Crown_Matrix", "Root Governance"),
            ("love", "Anchor_Protocol", "Emotional Storage"),
            ("null", "Omega_Entity", "Entropy Disposal"),
        ]
        for tld, owner, purpose in defaults:
            self.mint_tld(tld, owner, purpose)

    def list_tlds(self) -> List[TldRecord]:
        return list(self.registry.tlds.values())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crown Registry manager")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Registry database path")
    parser.add_argument("--zone", type=Path, default=DEFAULT_ZONE, help="Root zone output path")

    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add", help="Mint a new TLD")
    add_parser.add_argument("tld")
    add_parser.add_argument("owner")
    add_parser.add_argument("purpose")

    subparsers.add_parser("bootstrap", help="Mint the default TLD set and sign")
    subparsers.add_parser("list", help="Display current TLDs")
    subparsers.add_parser("sign", help="Generate the root zone file")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    registry = CrownRegistry(db_path=args.db, zone_path=args.zone)

    if args.command == "add":
        record = registry.mint_tld(args.tld, args.owner, args.purpose)
        print(f"Minted .{record.tld} for {record.owner} (purpose: {record.purpose})")
    elif args.command == "bootstrap":
        registry.bootstrap_defaults()
        registry.sign_root_zone()
        print(f"Bootstrap completed -> {args.db} / {args.zone}")
    elif args.command == "list":
        for record in registry.list_tlds():
            print(f".{record.tld:<12} owner={record.owner} purpose={record.purpose} revision={record.revision}")
    elif args.command == "sign":
        registry.sign_root_zone()
        print(f"Zone file written to {args.zone}")
    else:
        build_parser().print_help()
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
