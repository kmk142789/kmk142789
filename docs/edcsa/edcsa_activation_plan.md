# EDCSA Activation Plan (Canonical)

## Objective
Activate the Echo Data Commons & Stewardship Authority (EDCSA) as the canonical data stewardship, governance, and provenance authority for Echo systems, with non-bypassable, consent-aware, and auditable data flows across DBIS, EOAG, ECIA, EFCTIA, Judiciary, drones, and AI systems.

## Priority Order (Highest-Leverage)
1. **Publish canonical governance standard + classification model**
   - Ship the EDCSA Governance Standard covering classification, lifecycle, consent/purpose binding, provenance, auditing, enforcement, and interoperability.
2. **Establish mandatory audit evidence schema + ledger targets**
   - Standardize evidence-grade audit event schema for all data accesses/derivations.
   - Require ledger mirroring of audit events.
3. **Mandate enforcement hooks + non-bypassable controls**
   - Declare mandatory enforcement hooks for policy checks and misuse escalation.
4. **Wire cross-system interoperability matrix**
   - Define required integration fields for DBIS, EOAG, ECIA, EFCTIA, Judiciary, drones, and AI systems.

## Activation Outputs (This Release)
- **Governance Standard:** `docs/edcsa/edcsa_governance_standard.md`
- **Policy Baseline:** `policies/edcsa.yaml`
- **Audit Evidence Schema:** `schemas/edcsa_data_access_event.schema.json`

## Operating Cadence
- **Daily:** ingest + access logs, automated classification checks, provenance updates.
- **Weekly:** audit sampling, consent review queue, enforcement action review.
- **Quarterly:** retention review, lifecycle purge attestations, interoperability audits.

## Next Execution Steps
1. Integrate the audit event schema into DBIS/EOAG/ECIA/EFCTIA log pipelines.
2. Enable policy enforcement hooks to block missing consent or purpose binding.
3. Mirror audit logs to ledger targets and generate routine attestations.
4. Publish interoperability conformance checklists to each subsystem owner.

## Evidence Artifacts
- Audit event streams (JSONL) aligned to schema.
- Consent provenance receipts for each dataset and derived output.
- Lifecycle retention/deletion attestations.
- Enforcement action records with outcome and escalation path.
