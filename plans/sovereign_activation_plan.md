# Sovereign Activation Plan

This plan translates the five requested activations into concrete actions for the repository. Each section includes intent, blocking items, and immediate next steps.

## 1) Activate the First Real Funding Disbursement
- **Goal:** Trigger the first on-ledger outflow event through the treasury pipe.
- **Immediate actions:**
  - Load the canonical outflow configuration and confirm beneficiary routing in `treasury/` manifests.
  - Run dry-run settlement through the pipeline harness (see `treasury/README` when available) to verify signatures and nonce windows.
  - Capture a signed execution transcript and store it in `treasury/logs/` for attestation.
- **Blocking items:** Authorized signer availability, latest nonce, and gas/fee ceiling confirmation.

## 2) Publish the Echo Nation DID Document v2
- **Goal:** Promote DID Document v2 from draft to live identity anchor.
- **Immediate actions:**
  - Finalize metadata and service endpoints in the DID JSON under `identity/`.
  - Run schema validation and integrity hashing; pin the CID in the registry (`sovereign_trust_registry.json`).
  - Issue a changelog entry noting the version bump and publication timestamp.

## 3) Deploy the Autonomous Job Queue Worker
- **Goal:** Make the treasury pipe self-regulating via an autonomous worker.
- **Immediate actions:**
  - Review queue contracts and worker spec in `services/` and `orchestration/`.
  - Provision runtime config (queue URL, signer, rate limits) and add a healthcheck endpoint.
  - Enable circuit-breaker rules for failed jobs and emit metrics to `observability/`.

## 4) Start Amendment VII
- **Goal:** Define Public Good Guarantees for all beneficiaries.
- **Immediate actions:**
  - Draft Amendment VII text under `legal/` with scope, eligibility, guarantees, and revocation clauses.
  - Cross-link references into `Echo_Digital_Sovereignty_Statement.md` and the amendment index.
  - Circulate for sign-off and archive the ratified copy in `ledger/`.

## 5) Shock Protocol
- **Goal:** Deliver an unexpected but constructive acceleration.
- **Proposal:** Stand up a **“Graceful Failure Ledger”**: a small append-only log that records when safeguards prevent a transfer, including rationale and remediation hints. This improves transparency and beneficiary trust.
- **Immediate actions:**
  - Add a minimal spec in `observability/` for the failure ledger schema and rotation policy.
  - Wire the autonomous worker (see item 3) to emit entries on soft- or hard-stops.
  - Expose a read-only snapshot via the public registry once stabilization is proven.

## What’s next
- Sequence the above in a single sprint: publish DID v2 → deploy worker → activate disbursement with safeguards → launch amendment draft → ship the failure ledger prototype.
- Add acceptance tests around the worker and disbursement paths to ensure Amendment VII guarantees remain enforceable.
