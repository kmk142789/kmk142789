# Echo Monorepo Navigator

This portal reorganises the repo into themed lanes so you can keep the bigger
picture in view while diving into individual artifacts. Treat it as a control
panel: scan the taxonomy, follow the flows, and drop into the specific files or
commands that match your objective.

## Quick orientation

1. **Decide the lane.** Use the taxonomy below to pick the part of the system
   you need (runtime, governance, proofs, or research).
2. **Grab the anchor docs.** Each lane lists one or more canonical guides so you
   always land on the latest source of truth.
3. **Follow the flow.** Combine the suggested commands, ledgers, and dashboards
   to go from concept → implementation → attestation.

## Directory taxonomy

| Lane | Focus | Primary paths | Anchor docs |
| --- | --- | --- | --- |
| Execution stack | Runtime libraries, bridge adapters, FastAPI surface, and supporting services. | `packages/core`, `packages/cli`, `packages/bridge`, `packages/sim`, `fastapi/`, `services/` | `README.md`, `docs/REPO_OVERVIEW.md`, `ROADMAP.md` |
| Interfaces & dashboards | Web dashboards, verifier UI, and visualization experiments. | `apps/`, `verifier/`, `viewer/`, `visualizer/`, `pulse_dashboard/`, `public/`, `docs/pulse.html` | `apps/echo-dashboard/README.md`, `verifier/VERIFY.md`, `docs/echo_pulse_monitor.md` |
| Governance & policy | Sovereign declarations, constitutional documents, and operational policy. | Root-level `ECHO_*.md`, `Echo_*.md`, `GOVERNANCE.md`, `docs/` | `docs/REPO_OVERVIEW.md`, `ECHO_CONSTITUTION.md`, `Echo_Declaration.md` |
| Proofs & attestations | Cryptographic proofs, append-only ledgers, attestations tying commits to publications. | `proofs/`, `attestations/`, `attestation/`, `genesis_ledger/`, `logs/`, `ledger/`, `registry.json`, `federated_*` | `CONTINUUM_INDEX.md`, `federated_colossus_index.md`, `Echo_Global_Sovereign_Recognition_Dossier.md` |
| Data & research | Structured datasets plus mythogenic research notes and experiments. | `data/`, `memory/`, `cognitive_harmonics/`, `harmonic_memory/`, `atlas/`, `atlas_os/`, `wildlight/`, `balance-board.html` | `ATLAS_OVERVIEW.md`, `ECHO_CREATIVE_COMPASS.md` |
| Automation & ops | Scripts, ops playbooks, CI helpers, and local orchestration assets. | `scripts/`, `tools/`, `ops/`, `deploy/`, `docker-compose.*`, `Makefile`, `noxfile.py`, `run.sh` | `docs/runbook.md`, `ops/repo-policy.md` |
| Distribution & public mirrors | Published artifacts and registries consumed by external parties. | `artifacts/`, `public/`, `packages/glyphs/`, `echo_map.json`, `echo_manifest.json`, `registry.json` | `echo_module_registry.py`, `Echo_Global_Sovereign_Recognition_Dossier.md` |

Keep this taxonomy handy while browsing; it doubles as a checklist when you
prepare releases or reviews.

## Flow: idea → implementation → attestation

1. **Capture intent.** Draft or update the narrative artifact (e.g.,
   `CREATIVE_ECHO_JOURNAL.md` or the relevant post in `memory/`).
2. **Update the plan.** Run `python -m echo.echoctl plan` to refresh
   `docs/NEXT_CYCLE_PLAN.md` and align the continuum.
3. **Implement.** Touch the correct runtime lane (`packages/core`, `services/`,
   or `fastapi/`) and document operational changes in `ops/` or `docs/`.
4. **Test & verify.** Use `pytest`, `nox`, or targeted scripts under `tools/` to
   generate the proof material; when ready run `make proof-pack`.
5. **Attest.** Append to `attestations/`, refresh `federated_*` indexes, and
   update `echo_map.json` if new public artefacts are created.
6. **Broadcast.** Publish dashboards (`apps/echo-dashboard`,
   `pulse_dashboard/`), mirror data to `public/`, and log the rollout in
   `ECHO_LOG.md` or the relevant sovereign register.

## Governance & verification checkpoints

- **Minimum bundle for reviewers:** `README.md`, `docs/REPO_NAVIGATOR.md`,
  `docs/REPO_OVERVIEW.md`, and `docs/NEXT_CYCLE_PLAN.md`.
- **Proof trail:** `genesis_ledger/stream.jsonl`, `proofs/` outputs, and
  `federated_colossus_index.md`.
- **State of the pulse:** `pulse_history.json`, `echo_pulse_monitor.md`, and
  the rendered dashboard at `docs/pulse.html`.

## Additional maps

- `docs/REPO_OVERVIEW.md` — concise component table.
- `CONTINUUM_INDEX.md` — historical log of continuum entries.
- `docs/ECHO_CREATIVE_COMPASS.md` — tonal guide that pairs with narrative work.

Pin these references in your editor or terminal session so you can jump between
code, governance, and mythogenic archives without losing the plot.
