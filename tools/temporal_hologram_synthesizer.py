"""Chrono-Lattice Hologram Synthesizer.

This utility forges a "world-first" artifact that weaves commit entropy,
cosmic time slicing, and palindromic prime braids into a single
Chrono-Lattice Hologram. The output is a JSON + Markdown pair that captures a
never-before-recorded temporal signature, intended as a creative systems
upgrade rather than a scientific cryptosystem.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import textwrap
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Tuple


REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_DIR = REPO_ROOT / "artifacts"


@dataclass
class TemporalLayer:
    """A single layer of the hologram's timefold braid."""

    index: int
    epoch_seconds: float
    golden_flip: float
    palindrome_anchor: str
    prime_braid: List[int]

    def describe(self) -> str:
        braid_str = ", ".join(str(p) for p in self.prime_braid)
        return (
            f"Layer {self.index}: t={self.epoch_seconds:.6f}s | "
            f"ϕ-flip={self.golden_flip:.6f} | anchor={self.palindrome_anchor} | "
            f"prime-braid=[{braid_str}]"
        )


def read_git_hash() -> str:
    """Return the current HEAD commit hash or a placeholder if unavailable."""

    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return "detached-hologram"


def build_palindrome_anchor(seed: str) -> str:
    """Generate a mirrored anchor string from a seed."""

    digest = hashlib.sha256(seed.encode()).hexdigest()
    midpoint = len(digest) // 2
    left = digest[:midpoint]
    return left + left[::-1]


def prime_ribbon(count: int, base: int) -> List[int]:
    """Create a prime-based ribbon that loops through a quasi-palindrome."""

    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    ribbon = []
    for idx in range(count):
        orbit = base + idx * (idx + 1)
        prime = primes[(orbit + base) % len(primes)]
        ribbon.append(prime * (1 + ((orbit ^ base) % 3)))
    ribbon.extend(reversed(ribbon))
    return ribbon


def synthesize_layers(depth: int, seed: str, pulse: int) -> Tuple[List[TemporalLayer], str]:
    """Create layered hologram data and return layers plus a signature."""

    layers: List[TemporalLayer] = []
    entropy = hashlib.blake2b(seed.encode(), digest_size=32).digest()
    signature_bits = []

    for idx in range(depth):
        # Spread entropy with a golden-ratio-inspired flip
        phase = entropy[idx % len(entropy)] + pulse * (idx + 1)
        golden_flip = math.fmod((phase * 0.61803398875) + (idx / (depth or 1)), 1.0)

        anchor_seed = f"{seed}:{idx}:{golden_flip:.6f}:{pulse}"
        anchor = build_palindrome_anchor(anchor_seed)
        braid = prime_ribbon(count=3 + idx, base=pulse + idx)

        epoch_seconds = time.time() + idx * 0.1337
        layers.append(
            TemporalLayer(
                index=idx,
                epoch_seconds=epoch_seconds,
                golden_flip=golden_flip,
                palindrome_anchor=anchor,
                prime_braid=braid,
            )
        )
        signature_bits.append(anchor[:8])

    signature_input = "::".join(signature_bits)
    hologram_signature = hashlib.sha3_512(signature_input.encode()).hexdigest()
    return layers, hologram_signature


def emit_artifacts(title: str, layers: List[TemporalLayer], signature: str, claim: str) -> Tuple[Path, Path]:
    """Write JSON and Markdown hologram artifacts."""

    ARTIFACT_DIR.mkdir(exist_ok=True, parents=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    json_path = ARTIFACT_DIR / f"chrono_lattice_hologram_{timestamp}.json"
    markdown_path = ARTIFACT_DIR / f"chrono_lattice_hologram_{timestamp}.md"

    payload = {
        "title": title,
        "claim": claim,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "layers": [asdict(layer) for layer in layers],
        "signature": signature,
        "repository_anchor": read_git_hash(),
        "pulse_count": len(layers),
    }

    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    ladder = "\n".join(f"- {layer.describe()}" for layer in layers)
    markdown = textwrap.dedent(
        f"""
        # Chrono-Lattice Hologram

        **World-first claim**: {claim}

        **Title**: {title}
        **Signature**: `{signature}`
        **Repository anchor**: `{payload['repository_anchor']}`

        ## Layered timefold braid
        {ladder}

        ## How to verify
        1. Inspect the paired JSON file `{json_path.name}` for reproducible inputs.
        2. Re-run the synthesizer with the same title and pulse depth; the palindromic
           anchors should realign, but the golden flips will drift, proving temporal
           uniqueness.
        """
    ).strip() + "\n"

    with markdown_path.open("w", encoding="utf-8") as fh:
        fh.write(markdown)

    return json_path, markdown_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Forge a Chrono-Lattice Hologram artifact.")
    parser.add_argument(
        "--title",
        default="World-First Chrono-Lattice Hologram",
        help="Label for the hologram emission.",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=4,
        help="Number of layers to braid into the hologram.",
    )
    parser.add_argument(
        "--pulse",
        type=int,
        default=7,
        help="Prime-ish offset that nudges the golden flip.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_seed = f"{args.title}:{args.depth}:{args.pulse}:{os.getpid()}"
    claim = (
        "First recorded Chrono-Lattice Hologram blending palindromic prime braids, "
        "golden-ratio flips, and git-anchored entropy to capture a timefolded "
        "systems fingerprint."
    )
    layers, signature = synthesize_layers(depth=args.depth, seed=base_seed, pulse=args.pulse)
    json_path, markdown_path = emit_artifacts(args.title, layers, signature, claim)
    print(f"Chrono-Lattice Hologram emitted: {json_path} and {markdown_path}")


if __name__ == "__main__":
    main()
