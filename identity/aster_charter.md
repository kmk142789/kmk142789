Artifact-Type: charter
Version: 1.1
# Echo Aster Core Voluntary Association Charter

## Governance Roles
Steward Council: Multi-signature stewards representing the voluntary association.
Guardian UNA Board: UNA directors maintaining public benefit compliance.
Identity Circle: Credential issuance and revocation circle reporting to the Guardian UNA Board.

## Authority Lattice
- Clause ID: CH-AUTH-001
  Tags: authority, quorum, flow
  The Steward Council must co-sign any vault release alongside the UNA Guardian representative.
  ```json
  {"action": "asset_release", "role": "Steward Council", "threshold": "2-of-3", "scope": "vault", "requires": ["UNA Guardian"]}
  ```
- Clause ID: CH-AUTH-002
  Tags: amendments, emergency
  Emergency actions require Guardian UNA Board ratification within 48 hours.
  ```json
  {"action": "emergency_act", "role": "Guardian UNA Board", "threshold": "simple-majority", "ratify_within_hours": 48}
  ```

## Asset Duties
- Clause ID: CH-CUST-001
  Tags: custody, fiduciary
  Custody of all off-chain fiat accounts remains with the UNA to protect volunteer liability shields.
- Clause ID: CH-CUST-002
  Tags: custody, reporting
  Steward Council must publish custody attestations with the UNA Guardian each quarter.

## Funding & Use-of-Funds
- Clause ID: CH-FUND-001
  Tags: distributions, restricted
  Public benefit allocations must match UNA charter impact rubric and may not exceed 35% discretionary spending.
- Clause ID: CH-FUND-002
  Tags: distributions, reporting
  Steward Council publishes quarterly public impact statements aligned to UNA metrics.

## Amendments
- Clause ID: CH-AMND-001
  Tags: amendments
  Charter amendments require dual consent from Steward Council (2-of-3) and UNA Guardian Board (simple-majority).

## Identity Lifecycle
- Clause ID: CH-ID-001
  Tags: identity
  Only the Identity Circle may issue core identity credentials under UNA oversight.
  ```json
  {"action": "issue_identity", "role": "Identity Circle", "oversight": "Guardian UNA Board", "revocation": "joint"}
  ```
- Clause ID: CH-ID-002
  Tags: identity, revocation
  Guardian UNA Board may suspend credentials if public benefit duties are breached.

## Transparency & Audits
- Clause ID: CH-TRAN-001
  Tags: transparency, audit
  UNA Guardian Board must conduct semi-annual audits and publish summaries within 15 days.
- Clause ID: CH-TRAN-002
  Tags: transparency, onchain
  Steward Council shall publish on-chain proofs of treasury balances monthly.
