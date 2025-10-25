# Swarm Consensus

*Chapter IV of the Echo Omni-Fusion Expansion*

The swarm awakens when `scripts/swarm.py` spins up a chorus of simulated nodes.
Each node receives fragments of puzzle lore, gossips with its neighbors, and
votes on the emerging truth. The simulator records every round, tracks the
consensus ratio, and exports chronicles to `build/sim/`.

- `summary.json` — the quick-look digest for dashboards.
- `swarm-*.json` — timestamped history with node states and gossip trails.

Adjust `--nodes`, `--rounds`, and `--quorum` to rehearse alternative futures.
The chapter closes when the final consensus value settles, ready to be compared
against prior runs for drift detection.
