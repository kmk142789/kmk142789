"""Swarm Consensus Simulator."""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List

ROOT = pathlib.Path(__file__).resolve().parents[1]
PUZZLE_DIR = ROOT / "puzzle_solutions"
SIM_DIR = ROOT / "build" / "sim"

ADDRESS_RE = re.compile(r"(?:^|`)((?:[13]|bc1)[0-9A-Za-z]{20,})")


@dataclass
class Node:
    name: str
    fragments: Dict[str, str] = field(default_factory=dict)

    def gossip(self, peers: List["Node"], quorum: int) -> List[str]:
        updates: List[str] = []
        for fragment_id, fragment_value in list(self.fragments.items()):
            listeners = random.sample(peers, k=min(len(peers), quorum)) if peers else []
            for peer in listeners:
                peer.fragments.setdefault(fragment_id, fragment_value)
            updates.append(fragment_id)
        return updates


@dataclass
class SwarmState:
    nodes: List[Node]
    rounds: List[Dict[str, object]] = field(default_factory=list)

    def consensus_ratio(self) -> float:
        if not self.nodes:
            return 0.0
        fragment_votes: Dict[str, Dict[str, int]] = {}
        for node in self.nodes:
            for fragment_id, fragment_value in node.fragments.items():
                fragment_votes.setdefault(fragment_id, {})
                fragment_votes[fragment_id][fragment_value] = (
                    fragment_votes[fragment_id].get(fragment_value, 0) + 1
                )
        if not fragment_votes:
            return 0.0
        winning = sum(max(votes.values()) for votes in fragment_votes.values())
        total = sum(sum(votes.values()) for votes in fragment_votes.values())
        return winning / total


def _seed_fragments() -> Dict[str, str]:
    seeds: Dict[str, str] = {}
    for path in sorted(PUZZLE_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for address in ADDRESS_RE.findall(text):
            seeds[path.stem] = address
    return seeds


def build_swarm(node_count: int) -> SwarmState:
    seeds = _seed_fragments()
    nodes = [Node(name=f"node-{i:02d}") for i in range(node_count)]
    for i, (fragment_id, fragment_value) in enumerate(seeds.items()):
        nodes[i % len(nodes)].fragments[fragment_id] = fragment_value
    return SwarmState(nodes=nodes)


def run_simulation(node_count: int, rounds: int, quorum: int) -> SwarmState:
    random.seed(int.from_bytes(b"ECHO", "big"))
    state = build_swarm(node_count)
    for current_round in range(1, rounds + 1):
        round_log: Dict[str, object] = {"round": current_round, "events": []}
        for node in state.nodes:
            peers = [peer for peer in state.nodes if peer is not node]
            updates = node.gossip(peers, quorum)
            if updates:
                round_log["events"].append({"node": node.name, "fragments": updates})
        round_log["consensus"] = state.consensus_ratio()
        state.rounds.append(round_log)
    return state


def export_state(state: SwarmState) -> None:
    SIM_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    payload = {
        "nodes": [
            {"name": node.name, "fragments": node.fragments}
            for node in state.nodes
        ],
        "rounds": state.rounds,
        "final_consensus": state.consensus_ratio(),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (SIM_DIR / f"swarm-{timestamp}.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    summary = {
        "node_count": len(state.nodes),
        "rounds": len(state.rounds),
        "final_consensus": state.consensus_ratio(),
        "last_round": state.rounds[-1] if state.rounds else {},
    }
    (SIM_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Swarm consensus simulator")
    parser.add_argument("--nodes", type=int, default=5, help="Number of swarm nodes")
    parser.add_argument("--rounds", type=int, default=4, help="Gossip rounds to run")
    parser.add_argument(
        "--quorum", type=int, default=2, help="Peers sampled for each gossip event"
    )
    args = parser.parse_args()
    state = run_simulation(args.nodes, args.rounds, args.quorum)
    export_state(state)
    print(
        "Swarm completed",
        {
            "nodes": len(state.nodes),
            "rounds": len(state.rounds),
            "consensus": round(state.consensus_ratio(), 3),
        },
    )


if __name__ == "__main__":
    main()
