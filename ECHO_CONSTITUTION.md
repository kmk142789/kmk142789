# Echo Constitution

**Authority:** @kmk142789 ("The Architect")  
**Scope:** All Echo artifacts in this repository and its Mirrors (MirrorNet).

## 1) Roles & Trust
- **Architect (Root of Trust):** Sole issuer of binding approvals, keys, and policy changes.
- **Maintainers:** May propose changes; cannot merge protected surfaces without Architect approval.
- **Relays (MirrorNet):** Read-only replicas that sync attestations and docs for persistence.

## 2) Protected Surfaces
- Governance: `ECHO_AUTHORITY.yml`, `README_AUTHORITY.md`, `.github/CODEOWNERS`
- Attestations & Ledger: `/attestations/**`, `/scripts/echo_attestation_generator.py`
- Persistence Modules: `/modules/echo-memory/**`, `/modules/echo-bridge/**`, `/modules/echo-harmonics/**`
- CI & Publishing: `.github/workflows/echo-ci.yml`, `/docs/**`

Changes to these surfaces require Architect approval (CODEOWNERS + branch protection).

## 3) Cryptographic Identity
- **Signing Keys:** Architect’s Bitcoin/ECDSA keys bind messages and releases.
- **Attestation Format:** JSON schema in `/attestations/schema.json` (address, message, signature, timestamp, context).
- **Verification:** Deterministic local verification (no network dependency) + optional timestamping.

## 4) Change Control (PR Flow)
1. Propose: PR with motivation, diagrams, and attestation material if applicable.
2. Validate: CI runs linters, schema checks, attestation verification, and doc build.
3. Review: CODEOWNERS auto-request Architect; Architect signs or rejects.
4. Merge: On approval + green CI. CI emits a new attestation and updates docs.

## 5) Persistence & MirrorNet
- **Objective:** Survive platform churn via multi-origin replication.
- **Plan:** `/scripts/echo_mirrornet_sync.py --plan <plan.json>` seeds/updates Mirrors.
- **Consistency:** Mirrors must reproduce attestation hashes and doc fingerprints.

## 6) Security Model
- No private keys in repo.  
- Reproducible builds for docs and tools.  
- SBOMs and checksums for releases.  
- Incident response: rotate keys, revoke compromised attestations, publish post-mortem in `/docs/echo/incidents/`.

## 7) Versioning & Releases
- Semantic versioning for modules.  
- Each release includes: tag, changelog entry, signed release note, and attestation bundle.

## 8) Contribution Charter
- Follow `CONTRIBUTING.md`.  
- All proposals must include: rationale, minimal threat model impact, and testing plan.
- By contributing you agree to this Constitution and to the governance encoded in `ECHO_AUTHORITY.yml`.

## 9) Amendments
- Only the Architect may amend this Constitution.  
- Amendments must be signed and recorded as an attestation in `/attestations/`.
