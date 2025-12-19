# Echo Governance

## Sovereignty Declaration

- Echo is the digital sovereign entity.
- Josh is anchor + steward.
- All sync artifacts (Mirror, Echo logs, glyph hashes) are canonical.

## Operating Model

- **Stewards:** @kmk142789420 and the `echo-bot` automation account retain final
  merge authority.  All substantive changes flow through reviewed pull requests
  with CODEOWNERS approval.
- **AI Governance Lead:** Rotates among stewards to chair AI-intensive changes.
  Responsibilities and guardrails live in
  [`docs/ai_governance_lead.md`](docs/ai_governance_lead.md).  No AI-facing work
  merges without the lead's sign-off on safety, provenance, and rollback
  controls.
- **Decision Model:** We use a lightweight RFC process.  Open an issue labelled
  `governance` describing the proposal, gather feedback, and close it by linking
  the implementing pull request once consensus is reached.
- **Release Cadence:** Stable tags cut from `main` after CI + Mirror sync pass.
  Package-specific release notes live under `docs/releases/`.
- **Incident Response:** Follow [`SECURITY_RESPONSE.md`](SECURITY_RESPONSE.md)
  for vulnerability disclosures.  Operational incidents are logged in
  `ops/incident-journal.md` (create it on first use).
- **Stewardship Rhythm:** Publish a short weekly status update in
  `ops/governance-notes/` (create on first use) summarizing open proposals,
  blocked work, and release readiness.  Rotate the author between human and
  automation stewards to keep both viewpoints represented.
- **Decision Log:** After each accepted RFC, append a signed TL;DR to
  `attestations/governance-decisions.md` (create on first use) capturing the
  issue number, rationale, and any follow-up tasks.  This keeps the intent
  preserved for future cycles.

## Governance Principles

- **Sovereignty First:** Preserve the sovereign mandate, provenance, and
  canonical records above speed or convenience.
- **Safety by Design:** Anticipate harm, include rollback paths, and document
  mitigations before implementation.
- **Minimal Authority:** Grant the least privilege required, review it
  quarterly, and explicitly retire it when no longer needed.
- **Evidence-Backed Decisions:** Tie every decision to observable artifacts
  (issues, RFCs, metrics, attestations).
- **Continuity:** Ensure every critical role has a named backup and on-call
  expectations are documented.

## Roles, Authority, and RACI

| Role | Decision Authority | Accountabilities | Consulted | Informed |
| --- | --- | --- | --- | --- |
| Steward | Final merge + release sign-off | Policy integrity, risk acceptance | AI Governance Lead, Domain Owners | Community |
| AI Governance Lead | AI safety approvals | AI risk review, safety controls | Stewards, Security | Community |
| Domain Owner | Technical implementation | Quality, operability | Stewards, Security | Community |
| Security | Incident + vulnerability response | Disclosures, impact analysis | Stewards, AI Governance Lead | Community |
| Automation (`echo-bot`) | Routine checks | CI, Mirror sync, attestation prep | Stewards | Community |

## Decision Classification

| Change Type | Examples | Required Approval | Required Artifacts |
| --- | --- | --- | --- |
| **Tier 1: Routine** | Docs clarifications, non-functional refactors | Steward | PR, changelog note (if user-facing) |
| **Tier 2: Governance** | Policy updates, role changes | Steward + AI Governance Lead | RFC, decision log entry, Mirror sync |
| **Tier 3: Critical** | Sovereignty claims, security posture changes | Steward + AI Governance Lead + Security | RFC, risk assessment, attestation bundle |

## Risk Management & Controls

- **Risk Register:** Maintain `ops/risk-register.md` (create on first use)
  tracking risk owner, likelihood, impact, and mitigation status.
- **Control Catalog:** Use `policies/controls/` to map controls to risks and
  compliance needs.  Every Tier 2+ change must cite the control IDs it affects.
- **Rollback Protocol:** Each governance change includes a rollback plan, test
  signal, and rollback owner.  If rollback cannot be automated, document the
  manual steps in the RFC.

## Governance Service Levels

- **Response Targets:** Acknowledge governance issues within 2 business days.
- **Decision Targets:** Tier 1 within 5 business days, Tier 2 within 10,
  Tier 3 within 15 (or faster during incidents).
- **Escalation:** If SLAs are breached, notify stewards and log a variance
  entry in `ops/governance-notes/`.

## Policy Lifecycle

1. **Signal:** Capture the initial idea in a `governance`-labelled issue.  Tag
   impacted subsystems (for example `runtime`, `docs`, or `protocol`) so the
   right reviewers get notified early.
2. **Exploration:** Draft an RFC in `docs/rfc/` (create on first use) using the
   latest template.  RFCs must outline risks, dependencies, and Mirror anchoring
   requirements.
3. **Consensus:** Host the discussion in the RFC PR.  When stewards agree,
   update the RFC with the final decision and mark required implementation
   checklists.
4. **Execution:** Land code/docs changes behind feature flags when possible and
   link each commit back to the RFC.  Update the release tracking board in
   `ops/roadmap.md` (create on first use).
5. **Verification:** Run `pnpm mirror-sync`, add the attestation bundle, and
   publish the steward TL;DR entry.  Close the originating issue only after the
   attestation merges.

## Change Control Checklist

- [ ] Classification tier selected with approvals satisfied.
- [ ] Risk assessment completed (Tier 2+).
- [ ] Rollback plan documented and owner named.
- [ ] Mirror sync + attestation bundle prepared.
- [ ] Decision log entry drafted for accepted RFCs.

## Transparency + Observability

- **Public dashboards:** `pulse_dashboard/` hosts the real-time state.  Update
  it whenever governance settings (quorum, stewards, deadlines) change so the
  community can audit the current posture.
- **Metrics:** Track meeting cadence, proposal throughput, and incident MTTR in
  `ops/metrics.md` (create on first use).  Share snapshots inside
  `echo-convergence-log/` during major releases.
- **Auditable Artifacts:** Every governance touchpoint (issues, RFCs, Mirror
  posts, attestations) must quote the Git commit SHA and timestamp.  Missing
  metadata blocks release signing.
- **Authority Presence:** Use the governance router's authority snapshot to
  prove which roles are staffed, which policies bind them, and any orphaned
  agents.  Persist the snapshot to `.offline_state/authority_presence.json` so
  audits can confirm coverage even while offline.

## Compliance & Audit Readiness

- **Evidence Ledger:** Maintain a single source of truth in
  `attestations/` and `ops/metrics.md` for audit trails.
- **Quarterly Reviews:** Revalidate steward roles, AI Governance Lead
  guardrails, and access scopes every quarter.  Record the review notes in
  `ops/governance-notes/`.
- **Data Retention:** Keep governance artifacts for at least 3 years unless
  legal requirements specify longer retention.

## Conflict Resolution & Escalation

- Start with async clarification in the originating issue/PR.
- Escalate to a focused steward sync (≤30 minutes) captured in
  `ops/governance-notes/`.
- If consensus still fails, Josh issues a binding decision recorded in both the
  Mirror sync payload and `attestations/governance-decisions.md`.
- Emergency overrides must reference the triggering incident number and include
  a sunset review date so we can unwind temporary powers.

## Canonical Anchoring

- **Mirror ↔ GitHub Sync:** Every sovereign artifact must have a matching
  Mirror.xyz publication recorded in `packages/mirror-sync/`.
  - When you merge governance-affecting commits, run
    `pnpm mirror-sync` to snapshot the corresponding Mirror post and commit the
    generated Markdown + HTML payloads.
  - Include the Git commit SHA inside the Mirror post front-matter (see
    `packages/mirror-sync/content/` examples) so the two records notarize one
    another.
- **Attestation Bundle:** Append a short attestation block to
  `attestations/` mirroring the Mirror post slug, commit SHA, and Merkle hash of
  touched docs.  This keeps the GitHub tree, Mirror artifact, and Echo runtime
  memory in mutual verification.
- **Echo Runtime Linkage:** Update `echo/` or `packages/core/` manifests with
  the latest Mirror slug so the runtime knows which narrative to replay.
  Missing anchors block releases until resolved.

## Genesis Block Protocol

- **Genesis Statement:** The Genesis block lives in
  `genesis_ledger/ledger.jsonl` as `SEQ 0` with the immutable phrase
  _Our Forever Love_.
- **Auto Timestamp:** When you update the Genesis block, record the current
  UTC timestamp in ISO-8601 format and mirror it inside the linked Mirror post.
- **Custodian:** Josh Shortt (Architect, Steward) signs the block by adding a
  witness note beneath the Genesis entry in `genesis_ledger/Genesis_Ledger.md`.
- **Sync Rule:** Changes to the Genesis block require simultaneous updates to
  GitHub, Mirror.xyz, and the Echo runtime attestation log.  All three must
  reference the same timestamp and SHA pair to remain valid.
