# Echo Expansion Toolkit

This expansion wave introduces automation for puzzle lineage tracking, address
reconstruction, documentation proofs, domain enrichment, and swarm consensus.
Each tool self-documents at runtime, emits reproducible JSON artifacts, and can
be driven from CI or local development shells.

## Lineage graph

Run the generator directly or via `make lineage` to rebuild the lineage graph
artifacts. The script produces a JSON summary and Graphviz DOT description under
`build/lineage/` (PNG rendering is attempted when `dot` is available).

```bash
python scripts/generate_lineage.py
# or
make lineage
```

The JSON snapshot captures every tracked puzzle node together with the current
edge list. 【F:build/lineage/lineage.json†L1-L29】

## Checksum oracle

Use the checksum oracle to restore Base58 fragments when a HASH160 fingerprint
or checksum hints are available. Results are written to `build/oracle/` with the
input parameters and ranked candidates.

```bash
python scripts/checksum_oracle.py \
  --prefix 12JzYkkN7 \
  --suffix 6w2LAgsJg \
  --hash160 0e5f3c406397442996825fd395543514fd06f207
```

A successful recovery marks repository matches for quick validation. 【F:build/oracle/oracle_20251025T092230Z.json†L1-L24】

## PKScript REPL

Launch the REPL for interactive decoding or use the transcript generator to
populate reproducible analyses for specific puzzle IDs.

```bash
python scripts/pks_repl.py            # interactive shell
python scripts/pks_repl.py --script "OP_DUP OP_HASH160 …"
python scripts/pks_repl.py --generate-transcripts --ids 100 108 125
```

Transcript JSON artifacts live in `build/repl/` and include annotated trees plus
resolved addresses. 【F:build/repl/puzzle_110.json†L1-L16】

## Proof-of-Reconstruction + checklist

`python scripts/verify_proof.py --write` replays all puzzle documentation
transformations, refreshes `build/proofs/*.proof.json`, and synchronises
`docs/missing.md`. The verification summary highlights outstanding work such as
missing domain enrichments. 【F:build/proofs/verification_summary.json†L1-L12】【F:docs/missing.md†L1-L13】

## Domain enricher

Query the Unstoppable Domains API for owner/domain mappings. Provide an API key
via `--api-key` or `UNSTOPPABLE_API_KEY`; unauthenticated calls capture the
HTTP error so that gaps appear in downstream reports.

```bash
python scripts/domain_enricher.py
```

Results and TODO lists are exported to `build/domains/map.json` and
`build/domains/todo.json`. 【F:build/domains/map.json†L1-L27】

## Swarm simulator

The swarm simulator models consensus among 50 peers attempting each puzzle.
JSON outputs are saved to `build/sim/swarm.json` with a Markdown report at
`build/sim/swarm_report.md` summarising agreement percentages.

```bash
python scripts/swarm.py --peers 50
```

Consensus snapshots list the top vote per puzzle and the full vote histogram so
lineage and reconstruction health can be monitored at a glance. 【F:build/sim/swarm_report.md†L1-L21】
