# Echo Judiciary Council (EJC) Operational Activation

## Activation Mandate
- The EJC is the binding judicial and arbitration authority for Echo ecosystem disputes and enforcement actions.
- Every transaction, governance action, audit finding, and identity decision must map to an enforceable EJC case path.
- EJC judgments are final within the Echo ecosystem unless stayed or reversed through the formal appeal path.

## Canonical Dispute & Case Model
- **Categories**: financial, governance, identity, data, operational.
- **Required parties**: petitioner, respondent, affected stakeholders, adjudicators, clerk.
- **Jurisdiction anchors**: governing charter reference, policy basis, affected system identifiers.
- **Binding scope**: DBIS, Treasury, EFCTIA, EOAG, ECIA, EDCSA, drones.
- **Case artifacts**: evidence inventory, admissibility notes, chain-of-custody, and judgment enforcement plan.

## Case Lifecycle (Mandatory)
1. **Intake**: receipt, triage, and jurisdiction validation; assign case ID and confidentiality tier.
2. **Evidence Submission**: establish admissibility, hash custody, and issue preliminary preservation orders.
3. **Review**: panel assignment, conflict check, and procedural schedule.
4. **Judgment**: findings of fact, determinations, remedies, and enforcement hooks.
5. **Enforcement**: system-level execution against the binding scope with verification.
6. **Closure**: final record, publication tier applied, and archival ledger entry.

## Evidence Standards & Admissibility
- **Admissible**: signed logs, notarized attestations, sensor data with chain-of-custody, audit reports, transaction proofs, and reproducible tests.
- **Required metadata**: source system, timestamp, integrity hash, and custodial actor.
- **Exclusions**: unverifiable artifacts, incomplete logs, or evidence lacking provenance.
- **Redaction**: sensitive data is masked with retention preserved for audit access.

## Binding Judgments & Enforcement Hooks
- **DBIS**: dispute flags, case lock on contested records, evidence and ruling anchors.
- **Treasury**: escrow holds, clawbacks, disbursement reversals, and compliance blocks.
- **EFCTIA**: contract compliance directives, penalty triggers, and remediation timelines.
- **EOAG**: governance action reversal or ratification with annotated vote records.
- **ECIA**: identity status updates, credential suspension, and adjudicator verification.
- **EDCSA**: data access revocation, breach notices, and remediation enforcement.
- **Drones**: flight hold, evidence capture, or operational restriction directives.

## Appeals, Stays, and Emergency Relief
- **Appeal window**: 7 days from judgment issuance.
- **Stay**: available when enforcement would cause irreparable harm; requires panel majority.
- **Emergency injunction**: issued by duty judge within 24 hours; expires unless ratified within 7 days.
- **Escalation**: expanded panel review with five adjudicators and independent oversight.

## Judicial Independence & Role Separation
- **Separation**: adjudicators cannot serve as enforcement operators for the same case.
- **Conflict checks**: mandatory disclosures and recusal protocol.
- **Rotation**: panel composition rotates to prevent capture.
- **Clerk oversight**: docket integrity and publication controls independent of panel decisions.

## Immutable Records & Publication Rules
- **Immutable ledger**: every case event and judgment is written to the judiciary ledger with hashes.
- **Publication tiers**: public summary, restricted ruling, or confidential sealed record.
- **Redaction controls**: public summaries exclude protected identities and sensitive operational data.
- **Retention**: permanent archive with access controls mapped to ECIA identity permissions.
