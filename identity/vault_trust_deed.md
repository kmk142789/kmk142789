Artifact-Type: trust
Version: 2.0
# Echo Vault Star Programmable Trust Deed

## Trustees
Lead Trustee: Echo Vault Foundation corporate trustee with key shard A.
Guardian UNA Board: Oversight signatory with key shard B.
Emergency Custodian: Programmatic circuit breaker activated by Guardian UNA Board.

## Custody Matrix
- Clause ID: TR-CUST-001
  Tags: custody, fiduciary
  The Lead Trustee shall co-custody digital assets with the Steward Council multi-sig under a 2-of-3 threshold.
  ```json
  {"action": "asset_release", "role": "Lead Trustee", "threshold": "2-of-3", "shared_with": ["Steward Council", "Guardian UNA Board"]}
  ```
- Clause ID: TR-CUST-002
  Tags: custody, emergency
  During confirmed system compromise, the Lead Trustee may freeze assets with solo authority for 24 hours.
  ```json
  {"action": "freeze_assets", "role": "Lead Trustee", "threshold": "1-of-1", "duration_hours": 24, "requires_notice": true}
  ```

## Fiduciary Duties
- Clause ID: TR-DUTY-001
  Tags: fiduciary, reporting
  Trustee files quarterly fiduciary certifications to UNA Guardian Board.
- Clause ID: TR-DUTY-002
  Tags: fiduciary, disclosure
  Trustee discloses any conflicts of interest within 5 days.

## Distributions
- Clause ID: TR-DIST-001
  Tags: distributions, restricted
  Grants above 5,000 credits must include UNA public benefit review minutes.
- Clause ID: TR-DIST-002
  Tags: distributions, discretionary
  Up to 15% of annual inflows may be deployed at DAO discretion for experimentation.

## Amendments
- Clause ID: TR-AMND-001
  Tags: amendments
  Amendments require joint execution by Lead Trustee and Guardian UNA Board; emergency freeze clauses require Steward Council consent post-event.

## Identity Hooks
- Clause ID: TR-ID-001
  Tags: identity
  Trustee shall only honor identity lists signed by the Identity Circle + Guardian UNA Board multi-sig.
  ```json
  {"action": "validate_identity", "role": "Lead Trustee", "threshold": "2-of-2", "participants": ["Identity Circle", "Guardian UNA Board"]}
  ```

## Transparency
- Clause ID: TR-TRAN-001
  Tags: transparency, audit
  Trustee publishes monthly NAV attestations with Merkle proofs to the UNA Guardian Board.
