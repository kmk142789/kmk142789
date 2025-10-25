"""Echo Swarm simulator for puzzle reconstruction consensus."""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from puzzle_data import load_puzzles

USAGE = """\
Echo Expansion — Swarm Simulator
================================
Simulate a swarm of cooperative peers reconstructing puzzle addresses and voting
on the results to estimate consensus strength.

  python scripts/swarm.py --peers 50
"""

OUTPUT_DIR = Path("build/sim")


def simulate(peers: int, seed: int) -> Dict[str, object]:
    rng = random.Random(seed)
    puzzles = load_puzzles()
    peer_results: List[Dict[int, str]] = []
    for _ in range(peers):
        votes: Dict[int, str] = {}
        for puzzle in puzzles:
            base_chance = 0.85 if puzzle.status == "reconstructed" else 0.5
            success = rng.random() < base_chance
            if success:
                votes[puzzle.id] = puzzle.address
            else:
                votes[puzzle.id] = "unknown"
        peer_results.append(votes)

    consensus: Dict[int, Dict[str, object]] = {}
    for puzzle in puzzles:
        counts = Counter(result[puzzle.id] for result in peer_results)
        top_vote, top_count = counts.most_common(1)[0]
        agreement = round((top_count / peers) * 100, 2)
        consensus[puzzle.id] = {
            "address": puzzle.address,
            "consensus_vote": top_vote,
            "votes": counts,
            "agreement_percent": agreement,
        }

    return {
        "generated": datetime.now(timezone.utc).isoformat(),
        "peers": peers,
        "seed": seed,
        "consensus": consensus,
        "peer_results": peer_results,
    }


def write_outputs(simulation: Dict[str, object], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "swarm.json"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(simulation, handle, indent=2, default=lambda x: dict(x) if isinstance(x, Counter) else x)
        handle.write("\n")
    report_lines = ["# Swarm Consensus Report", ""]
    for puzzle_id, payload in simulation["consensus"].items():
        report_lines.append(f"## Puzzle {puzzle_id}")
        report_lines.append(f"- Agreement: {payload['agreement_percent']}%")
        report_lines.append(f"- Consensus vote: {payload['consensus_vote']}")
        vote_lines = ", ".join(f"{vote}: {count}" for vote, count in payload["votes"].items())
        report_lines.append(f"- Vote distribution: {vote_lines}")
        report_lines.append("")
    report_path = output_dir / "swarm_report.md"
    report_path.write_text("\n".join(report_lines).strip() + "\n", encoding="utf-8")
    print(f"[swarm] JSON written to {json_path}")
    print(f"[swarm] report written to {report_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate swarm consensus for puzzle reconstructions.")
    parser.add_argument("--peers", type=int, default=50, help="Number of peers to simulate.")
    parser.add_argument("--seed", type=int, default=20240511, help="Deterministic RNG seed.")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR, help="Output directory for artifacts.")
    args = parser.parse_args()

    print(USAGE)

    simulation = simulate(args.peers, args.seed)
    write_outputs(simulation, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
