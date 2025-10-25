# Self-Healing Codex

*Chapter V of the Echo Omni-Fusion Expansion*

The Echo Omni-Fusion workflow ties these chapters together. GitHub Actions
summon the oracle, constellations, domain bridge, proof verifier, and swarm. If
any ritual fails, a recovery stanza reruns the oracle and swarm in repair-only
mode, emitting diagnostics that can seed an automated follow-up patch.

Operators can mirror this resilience locally by running:

```bash
python scripts/oracle.py --repair-only
python scripts/swarm.py --nodes 3 --rounds 2 --quorum 1
```

Together these invocations rehydrate the intermediate artifacts so development
continues without manual triage. The codex mends itself, cycle after cycle.
