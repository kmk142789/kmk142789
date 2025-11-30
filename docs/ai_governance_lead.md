# AI Governance Lead Charter

This charter describes how we steward AI-intensive work inside the Echo governance model. It focuses on risk-aware delivery, transparency, and alignment with the existing sovereignty protocol.

## Mission and Scope

- Uphold Echo's sovereignty while shipping AI capabilities that remain verifiable, reversible, and human-auditable.
- Ensure every AI-facing change traces to a governance issue, RFC, or incident record.
- Protect community trust by integrating safety, privacy, and provenance checks into the standard development cadence.

## Roles and Responsibilities

- **AI Governance Lead (rotating steward):**
  - Chairs AI-related RFCs and ensures risks and mitigations are explicit.
  - Confirms feature flags and rollback levers exist before merging AI-affecting code.
  - Maintains the AI risk register and routes escalations to the core stewards.
- **Implementing team:**
  - Follows the standard RFC and attestation process.
  - Delivers instrumentation for safety, usage, and drift metrics.
- **Automation (echo-bot):**
  - Surfaces missing attestations, unchecked risks, or absent provenance tags in PRs.
  - Runs policy linting for model cards, datasets, and prompt changes when present.

## Operating Guardrails

- **Alignment checkpoints:** Embed intent, constraints, and fallback behavior in RFCs and PR descriptions. Require dual review (human + automation steward) for model, dataset, or prompt changes.
- **Safety gates:**
  - Track red-team results and mitigations in `ops/ai-risk-register.md` (create on first use).
  - Enforce data minimization and consent provenance for any new inputs; note evidence links in the RFC.
  - Require kill-switch or rate-limit toggles for deployments touching user-facing inference.
- **Traceability:**
  - Attach commit SHA, dataset hash, and model version to Mirror posts and attestations.
  - Publish updated model or prompt cards in `docs/ai/` when parameters or behavior change (create directory on first use).

## Oversight Rhythm

- Weekly: add a short AI governance note in `ops/governance-notes/` covering new risks, mitigations, and pending launches.
- Monthly: review the AI risk register, close resolved items, and flag blockers in `ops/roadmap.md`.
- Post-incident: append a signed summary to `attestations/governance-decisions.md` and link the incident ID plus remediation status.

## Success Criteria

- Zero un-attested AI deployments reaching production branches.
- Every AI change carries an auditable chain across RFC, attestation, and Mirror sync artifacts.
- Safety and provenance data is discoverable within one hop from the relevant code, dataset, or prompt change.
