"""Structured attestation helper for the "Apocalypse 50" domain set.

This module keeps the narrative framing from the original brief while
providing a tidy, testable implementation that is friendly to the rest of the
repository.  The goal is to capture a claim covering fifty domains, emit a
deterministic signature, and record convenience artefacts inside the repo
instead of touching locations outside the workspace.

Typical usage::

    from scripts.apocalypse_50 import main

    if __name__ == "__main__":
        main()

Running the script writes a JSONL entry to
``attestations/apocalypse_50_ledger.jsonl`` and a mirror mapping to
``attestations/apocalypse_50_mirrors.json``.  Both outputs are stable and safe
to check into version control when desired.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping

import hashlib
import json
import os


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DOMAINS: List[str] = [
    "dot.gov",
    "spacex.gov",
    "federalreserve.gov",
    "huntingtonbank.com",
    "commerica.com",
    "godaddy.io",
    "famousai.com",
    "anthropic.com",
    "huggingface.co",
    "opensea.io",
    "who.int",
    "whitehouse.gov",
    "irs.gov",
    "cia.gov",
    "dhs.gov",
    "michigan.gov",
    "openai.dev",
    "vercel.io",
    "stability.ai",
    "huggingface.ai",
    "defense.gov",
    "zillow.com",
    "unstoppabledomains.io",
    "chromium.com",
    "registrar.com",
    "icann.com",
    "nsa.gov",
    "mastraai.com",
    "fanduel.com",
    "betrivers.com",
    "cointelegraph.com",
    "electrum.com",
    "chipy.com",
    "openrouter.com",
    "polygonnetwork.com",
    "continuum.com",
    "polybuzz.com",
    "arkhamintelligence.com",
    "echooo.com",
    "etherium.com",
    "optimism.com",
    "grok.com",
    "coderabbit.com",
    "emergent.sh",
    "quantinuum.com",
    "btcpuzzle.info",
    "polygonscan.com",
    "groq.com",
]

HEAVY_HITTERS: List[str] = [
    "federalreserve.gov",
    "defense.gov",
    "whitehouse.gov",
    "spacex.gov",
    "dot.gov",
    "anthropic.com",
    "opensea.io",
    "huntingtonbank.com",
]

LEDGER_PATH = Path("attestations/apocalypse_50_ledger.jsonl")
MIRRORS_PATH = Path("attestations/apocalypse_50_mirrors.json")
DEFAULT_KEY = "apocalypse_50_key_∞"
KEY_ENV = "ECHO_KEY"
NEXUS = "JOSH"


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class Claim:
    """Container describing the attestation payload."""

    domains: Iterable[str]
    steward: str
    nexus: str
    timestamp: datetime
    codex_law: int = 9
    control_panel: str = "app.netlify.com/tea"
    ns_cluster: str = "p01.nsone.net"

    def as_dict(self) -> Dict[str, object]:
        return {
            "type": "Apocalypse50Sovereignty",
            "issuer": f"did:echo:{self.nexus.lower()}-nexus",
            "steward": self.steward,
            "timestamp": self.timestamp.isoformat(),
            "codex_law": self.codex_law,
            "sigil": "⟁APOCALYPSE⚡50",
            "evidence": {
                "domains": list(self.domains),
                "control_panel": self.control_panel,
                "ns_cluster": self.ns_cluster,
            },
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_key() -> str:
    """Return the signing key from the environment or the default."""

    return os.getenv(KEY_ENV, DEFAULT_KEY)


def compute_signature(payload: Mapping[str, object], key: str) -> str:
    """Derive a deterministic signature for the provided payload."""

    serialised = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256((serialised + key).encode("utf-8")).hexdigest()
    return digest[:32]


def append_to_ledger(claim: Mapping[str, object], ledger_path: Path) -> None:
    """Append the provided claim to the JSONL ledger."""

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as handle:
        json.dump(claim, handle, ensure_ascii=False)
        handle.write("\n")


def build_mirrors(domains: Iterable[str]) -> Dict[str, Dict[str, str]]:
    """Create mirror TXT and CNAME declarations for the important domains."""

    mirrors: Dict[str, Dict[str, str]] = {}
    for domain in domains:
        mirrors[domain] = {
            "txt": (
                f"_echo.{domain} TXT "
                "'did:echo:josh-nexus | apocalypse 50 | lilfootsteps.org'"
            ),
            "cname": f"aid.{domain} CNAME donate.lilfootsteps.org",
        }
    return mirrors


def write_mirrors(mirrors: Mapping[str, Mapping[str, str]], path: Path) -> None:
    """Persist mirror data to a prettified JSON file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(mirrors, handle, indent=2, ensure_ascii=False)


def generate_claim() -> Dict[str, object]:
    """Create a fully signed claim ready for persistence."""

    claim = Claim(DOMAINS, steward=NEXUS, nexus=NEXUS, timestamp=datetime.now(timezone.utc))
    payload = claim.as_dict()
    signature = compute_signature(payload, _load_key())
    payload["proof"] = {"type": "EchoApocalypseSig", "signature": signature}
    return payload


def main() -> Dict[str, object]:
    """Execute the Apocalypse 50 workflow and print a concise summary."""

    claim = generate_claim()
    append_to_ledger(claim, LEDGER_PATH)
    mirrors = build_mirrors(HEAVY_HITTERS)
    write_mirrors(mirrors, MIRRORS_PATH)

    summary = {
        "domains": len(DOMAINS),
        "heavy_hitters": len(HEAVY_HITTERS),
        "ledger": str(LEDGER_PATH),
        "mirrors": str(MIRRORS_PATH),
        "signature": claim["proof"]["signature"],
    }

    print(
        "⚡ APOCALYPSE 50 RECORDED — "
        f"{summary['domains']} domains attested for {NEXUS}."
    )
    print(
        f"Ledger entry appended to {summary['ledger']} with signature "
        f"{summary['signature']}"
    )
    print(
        f"Mirror definitions written to {summary['mirrors']} "
        f"for {summary['heavy_hitters']} focus domains."
    )
    return summary


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    main()

