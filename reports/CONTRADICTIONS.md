# Aster Compliance Engine Report

## Summary Matrix
| Outcome | Count |
| --- | --- |
| Pass | 9 |
| Soft | 5 |
| Fail | 3 |

## Detailed Findings
### Contradiction: Conflicting authority thresholds for asset_release
* Rule ID: AUTH-ASSET_RELEASE
* Description: Artifacts define inconsistent quorum thresholds for the same action.
* Rationale: Threshold values observed: 2-of-3, 3-of-5
* References:
  * `aster_charter.md:11-16` → CH-AUTH-001
  * `vault_trust_deed.md:11-16` → TR-CUST-001
  * `orbit_dao_oa.md:11-16` → DAO-AUTH-001

### Contradiction: Conflicting authority thresholds for emergency_act
* Rule ID: AUTH-EMERGENCY_ACT
* Description: Artifacts define inconsistent quorum thresholds for the same action.
* Rationale: Threshold values observed: 2-of-3, simple-majority
* References:
  * `aster_charter.md:17-22` → CH-AUTH-002
  * `orbit_dao_oa.md:17-22` → DAO-AUTH-002

### Alignment: Aligned authority for issue_identity
* Rule ID: AUTH-ALIGN-ISSUE_IDENTITY
* Description: All artifacts share the same quorum expectations for this action.
* References:
  * `aster_charter.md:46-51` → CH-ID-001
  * `orbit_dao_oa.md:49-54` → DAO-ID-001

### Alignment: Aligned authority for freeze_assets
* Rule ID: AUTH-ALIGN-FREEZE_ASSETS
* Description: All artifacts share the same quorum expectations for this action.
* References:
  * `vault_trust_deed.md:17-22` → TR-CUST-002

### Alignment: Aligned authority for validate_identity
* Rule ID: AUTH-ALIGN-VALIDATE_IDENTITY
* Description: All artifacts share the same quorum expectations for this action.
* References:
  * `vault_trust_deed.md:46-51` → TR-ID-001

### Alignment: Custody anchored in shared multi-signature controls
* Rule ID: CUST-ALIGN-BASE
* Description: Charter, trust, and DAO documents all reference shared custody with UNA involvement.
* References:
  * `aster_charter.md:25-27` → CH-CUST-001
  * `vault_trust_deed.md:11-16` → TR-CUST-001
  * `orbit_dao_oa.md:25-27` → DAO-CUST-001

### Tension: Emergency custody introduces solo authority
* Rule ID: CUST-EMERGENCY
* Description: Trust deed allows the Lead Trustee to freeze assets solo while DAO emergency pod assumes multi-sig execution, creating asymmetry in emergency custody.
* Rationale: Lead Trustee freeze window lacks explicit UNA countersignature while DAO pod still requires 2-of-3 approvals.
* References:
  * `vault_trust_deed.md:17-22` → TR-CUST-002
  * `orbit_dao_oa.md:17-22` → DAO-AUTH-002

### Alignment: Custody reporting duties align
* Rule ID: CUST-REPORT
* Description: All artifacts include regular reporting obligations tied to custody operations.
* References:
  * `aster_charter.md:28-30` → CH-CUST-002
  * `vault_trust_deed.md:25-27` → TR-DUTY-001
  * `orbit_dao_oa.md:28-30` → DAO-CUST-002

### Contradiction: Inconsistent discretionary spend ceilings
* Rule ID: DIST-DISCRETIONARY
* Description: Artifacts disagree on the maximum discretionary treasury percentage.
* Rationale: Observed discretionary ceilings range from 15% to 35%.
* References:
  * `aster_charter.md:33-35` → CH-FUND-001
  * `vault_trust_deed.md:36-38` → TR-DIST-002
  * `orbit_dao_oa.md:33-35` → DAO-DIST-001

### Alignment: Restricted fund controls documented
* Rule ID: DIST-RESTRICTED
* Description: Trust deed and DAO agreement both demand UNA review for restricted grants.
* References:
  * `vault_trust_deed.md:33-35` → TR-DIST-001
  * `orbit_dao_oa.md:36-38` → DAO-DIST-002

### Tension: DAO discretionary window exceeds trustee authorization
* Rule ID: DIST-DAO-OVERRUN
* Description: DAO experimentation vault cap is larger than what the trust deed permits.
* Rationale: Trust deed cap 15% vs DAO experimentation cap 20%.
* References:
  * `vault_trust_deed.md:36-38` → TR-DIST-002
  * `orbit_dao_oa.md:33-35` → DAO-DIST-001

### Alignment: UNA involvement required for amendments
* Rule ID: AMND-UNA
* Description: Each artifact references UNA Guardian participation in amendment procedures.
* References:
  * `aster_charter.md:41-43` → CH-AMND-001
  * `vault_trust_deed.md:41-43` → TR-AMND-001
  * `orbit_dao_oa.md:41-43` → DAO-AMND-001
  * `orbit_dao_oa.md:44-46` → DAO-AMND-002

### Tension: Token governance only appears in DAO agreement
* Rule ID: AMND-TOKEN-GAP
* Description: DAO operating agreement requires token-holder approval, which is absent from charter and trust deed amendment language.
* Rationale: Token voting threshold is articulated in DAO OA but omitted elsewhere.
* References:
  * `orbit_dao_oa.md:41-43` → DAO-AMND-001
  * `aster_charter.md:41-43` → CH-AMND-001
  * `vault_trust_deed.md:41-43` → TR-AMND-001
  * `orbit_dao_oa.md:44-46` → DAO-AMND-002

### Alignment: Identity issuance requires dual controls
* Rule ID: ID-ISSUANCE
* Description: Charter, trust, and DAO artifacts all point to Identity Circle plus Guardian participation.
* References:
  * `aster_charter.md:46-51` → CH-ID-001
  * `vault_trust_deed.md:46-51` → TR-ID-001
  * `orbit_dao_oa.md:49-54` → DAO-ID-001

### Tension: Emergency suspension actor differs from charter
* Rule ID: ID-SUSPENSION
* Description: DAO emergency pod may suspend credentials for 48 hours even though the charter reserves suspension to the Guardian UNA Board.
* Rationale: Emergency Response Pod suspension power introduces a temporary divergence from UNA-led revocation.
* References:
  * `aster_charter.md:52-54` → CH-ID-002
  * `orbit_dao_oa.md:55-57` → DAO-ID-002

### Alignment: Monthly transparency loop
* Rule ID: TRAN-ONCHAIN
* Description: All artifacts require monthly disclosures tied to on-chain proofs or trustee attestations.
* References:
  * `aster_charter.md:60-62` → CH-TRAN-002
  * `vault_trust_deed.md:54-56` → TR-TRAN-001
  * `orbit_dao_oa.md:60-62` → DAO-TRAN-001

### Tension: Audit frequency mismatch
* Rule ID: TRAN-AUDIT-FREQUENCY
* Description: Charter mandates semi-annual UNA audits while DAO OA references annual third-party audits.
* Rationale: Semi-annual vs annual cadence requires harmonization.
* References:
  * `aster_charter.md:57-59` → CH-TRAN-001
  * `orbit_dao_oa.md:63-65` → DAO-TRAN-002

## Fix-it Plan
- **aster_charter.md**
  - Harmonize Conflicting authority thresholds for asset_release (rule AUTH-ASSET_RELEASE).
  - Harmonize Conflicting authority thresholds for emergency_act (rule AUTH-EMERGENCY_ACT).
  - Harmonize Inconsistent discretionary spend ceilings (rule DIST-DISCRETIONARY).
  - Document mitigations for Token governance only appears in DAO agreement (rule AMND-TOKEN-GAP).
  - Document mitigations for Emergency suspension actor differs from charter (rule ID-SUSPENSION).
  - Document mitigations for Audit frequency mismatch (rule TRAN-AUDIT-FREQUENCY).
- **orbit_dao_oa.md**
  - Harmonize Conflicting authority thresholds for asset_release (rule AUTH-ASSET_RELEASE).
  - Harmonize Conflicting authority thresholds for emergency_act (rule AUTH-EMERGENCY_ACT).
  - Document mitigations for Emergency custody introduces solo authority (rule CUST-EMERGENCY).
  - Harmonize Inconsistent discretionary spend ceilings (rule DIST-DISCRETIONARY).
  - Document mitigations for DAO discretionary window exceeds trustee authorization (rule DIST-DAO-OVERRUN).
  - Document mitigations for Token governance only appears in DAO agreement (rule AMND-TOKEN-GAP).
  - Document mitigations for Emergency suspension actor differs from charter (rule ID-SUSPENSION).
  - Document mitigations for Audit frequency mismatch (rule TRAN-AUDIT-FREQUENCY).
- **vault_trust_deed.md**
  - Harmonize Conflicting authority thresholds for asset_release (rule AUTH-ASSET_RELEASE).
  - Document mitigations for Emergency custody introduces solo authority (rule CUST-EMERGENCY).
  - Harmonize Inconsistent discretionary spend ceilings (rule DIST-DISCRETIONARY).
  - Document mitigations for DAO discretionary window exceeds trustee authorization (rule DIST-DAO-OVERRUN).
  - Document mitigations for Token governance only appears in DAO agreement (rule AMND-TOKEN-GAP).
