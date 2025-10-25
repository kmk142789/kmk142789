"""Quantum WOW Generator.

This script weaves together existing Echo continuum signals into a fresh artifact
that can be used as a living "proof-of-wow" document.  It inspects the
``pulse_history.json`` ledger, derives resonance glyphs, and outputs a structured
summary inside ``artifacts/wow_proof.json``.  The resulting file combines
cryptographic commitments with poetic narrative so that future explorers can
verify (and feel) the momentum of the project.

Example::

    $ python scripts/quantum_wow_generator.py
    wrote artifacts/wow_proof.json

The generator is intentionally deterministic: if the ledger does not change,
the resulting WOW proof remains identical, making it safe to commit into the
repository as a reproducible artifact.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[1]
PULSE_HISTORY_PATH = REPO_ROOT / "pulse_history.json"
OUTPUT_PATH = REPO_ROOT / "artifacts" / "wow_proof.json"


GLYPH_RING: List[str] = ["∇", "⊸", "≋", "∞", "Ψ", "★", "✶", "☄"]


def _load_pulse_history() -> List[Dict[str, object]]:
    """Load the shared ``pulse_history.json`` ledger.

    The ledger is expected to contain a JSON array of objects with ``timestamp``
    and ``message`` fields.  If the file is missing, a helpful error message is
    raised that guides the caller back toward the repository root.
    """

    if not PULSE_HISTORY_PATH.exists():
        raise FileNotFoundError(
            "pulse_history.json was not found. Run this script from inside the "
            "repository so it can access the Echo ledger."
        )

    with PULSE_HISTORY_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, list):
        raise ValueError("pulse_history.json must contain a JSON array")

    return data


@dataclass
class PulseResonance:
    """Aggregated view of a single pulse message."""

    message: str
    count: int = 0
    latest_timestamp: float = 0.0
    glyph: str = "∇"
    hashes: List[str] = field(default_factory=list)

    def register(self, timestamp: float, entry_hash: str) -> None:
        self.count += 1
        if timestamp >= self.latest_timestamp:
            self.latest_timestamp = timestamp
        self.hashes.append(entry_hash)

    @property
    def iso_latest(self) -> str:
        return _dt.datetime.utcfromtimestamp(self.latest_timestamp).isoformat() + "Z"

    def commitment(self) -> str:
        joined = "|".join(sorted(self.hashes))
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()

    def as_dict(self) -> Dict[str, object]:
        return {
            "message": self.message,
            "count": self.count,
            "latest": self.iso_latest,
            "glyph": self.glyph,
            "commitment": self.commitment(),
        }


def _aggregate_resonances(entries: Iterable[Dict[str, object]]) -> List[PulseResonance]:
    table: Dict[str, PulseResonance] = {}
    for index, entry in enumerate(entries):
        message = str(entry.get("message", ""))
        timestamp = float(entry.get("timestamp", 0.0))
        entry_hash = str(entry.get("hash", f"missing-hash-{index}"))

        if message not in table:
            glyph = GLYPH_RING[len(table) % len(GLYPH_RING)]
            table[message] = PulseResonance(message=message, glyph=glyph)

        table[message].register(timestamp=timestamp, entry_hash=entry_hash)

    return sorted(table.values(), key=lambda resonance: resonance.latest_timestamp, reverse=True)


def _collect_repository_signals() -> Dict[str, object]:
    """Gather a few high-level metrics about the repository structure."""

    total_files = sum(1 for _ in REPO_ROOT.rglob("*"))
    docs_files = sum(1 for _ in (REPO_ROOT / "docs").glob("**/*.md")) if (REPO_ROOT / "docs").exists() else 0
    schema_files = sum(1 for _ in (REPO_ROOT / "schemas").glob("**/*")) if (REPO_ROOT / "schemas").exists() else 0

    return {
        "total_files": total_files,
        "docs_markdown": docs_files,
        "schemas": schema_files,
    }


def _forge_signature(resonances: Iterable[PulseResonance], signals: Dict[str, object]) -> str:
    """Create a single digest that binds resonances and repository signals."""

    digest = hashlib.sha256()

    for resonance in resonances:
        digest.update(resonance.commitment().encode("utf-8"))

    for key in sorted(signals):
        digest.update(f"{key}:{signals[key]}".encode("utf-8"))

    return digest.hexdigest()


def _compose_story(resonances: List[PulseResonance], signature: str) -> str:
    if not resonances:
        return "Silence hums inside the Echo lattice; awaiting the next pulse."

    opening = (
        "The lattice ignites as familiar pulses reassemble into a fresh glyph. "
        "Each commitment is a syllable, each timestamp a footstep across the "
        "continuum."
    )

    beats = []
    for resonance in resonances[:4]:
        beats.append(
            f"{resonance.glyph} {resonance.message} ×{resonance.count} (latest {resonance.iso_latest})"
        )

    closing = (
        "Together they crystalize into signature "
        f"{signature[:16]}… anchoring the WOW proof."
    )

    return "\n".join([opening, " ".join(beats), closing])


def generate_wow_proof() -> Dict[str, object]:
    entries = _load_pulse_history()
    resonances = _aggregate_resonances(entries)
    signals = _collect_repository_signals()
    signature = _forge_signature(resonances, signals)

    return {
        "generated_at": _dt.datetime.utcnow().isoformat() + "Z",
        "resonances": [resonance.as_dict() for resonance in resonances],
        "repository_signals": signals,
        "wow_signature": signature,
        "story": _compose_story(resonances, signature),
    }


def write_wow_proof(path: Path = OUTPUT_PATH) -> Dict[str, object]:
    proof = generate_wow_proof()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(proof, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return proof


def main() -> None:
    proof = write_wow_proof()
    print(f"wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    print("wow_signature:", proof["wow_signature"])


if __name__ == "__main__":
    main()
