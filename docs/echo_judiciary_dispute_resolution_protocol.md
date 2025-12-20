# Echo Judiciary Council: Dispute Resolution Protocol

## Scope & Principles
- Applies to disputes involving Echo ecosystem participants, contributors, validators, or affiliated councils.
- Anchored in principles of due process, transparency, proportionality, and restorative resolution when possible.
- The EJC is the binding judicial and arbitration authority across the Echo ecosystem.
- Every transaction, governance action, audit finding, or identity decision must have an enforceable judicial path.
- Every case must produce a public summary, redacting sensitive data where required by policy.

## Canonical Case Model
- **Categories**: financial, governance, identity, data, operational.
- **Case schema**: `schemas/ejc_case.schema.json`.
- **Judgment schema**: `schemas/ejc_judgment.schema.json`.
- **Jurisdiction**: EJC authority, governing charter reference, and affected system identifiers are mandatory.

## Roles
- **Petitioner**: Submits the dispute with evidence and requested remedy.
- **Respondent**: Receives notice, supplies counter-evidence, and may propose settlement.
- **Panel**: Three EJC reviewers (rotating, conflict-checked) who evaluate evidence, conduct hearings, and issue determinations.
- **Clerk**: Maintains records, deadlines, and publication of decisions.

## Dispute Categories
- Governance or treasury actions
- Contract performance and deliverables
- Attribution, IP, or authorship
- Code of Conduct violations
- Security, operational, or reliability incidents

## Process
1. **Intake**: Petitioner submits a case packet (facts, claims, remedy sought, evidence inventory). Clerk acknowledges within 48h and validates jurisdiction.
2. **Evidence Submission**: Parties submit evidence with integrity hashes, provenance, and admissibility notes.
3. **Review**: Panel is assigned, conflicts are screened, and timelines are posted to the public docket.
4. **Judgment**: Panel evaluates evidence, conducts hearings as needed, and issues written findings, remedies, and enforcement directives.
5. **Enforcement**: Binding remedies are executed via system hooks (DBIS, Treasury, EFCTIA, EOAG, ECIA, EDCSA, drones) with verification logs.
6. **Closure**: Final record is sealed, published per tier, and archived in the judiciary ledger.
7. **Appeal**: Parties may appeal within 7 days to an expanded panel of five reviewers. Appeals are limited to procedural errors or new material evidence.

## Timelines & Severity Bands
- **Severity A (safety/financial risk)**: Filing acknowledged in 24h; decision target ≤7 days.
- **Severity B (governance/process)**: Filing acknowledged in 48h; decision target ≤14 days.
- **Severity C (interpersonal/contentious)**: Filing acknowledged in 72h; decision target ≤21 days.

## Evidence Standards
- Prefer signed commits, reproducible test cases, on-chain transactions, logs, and notarized statements.
- Sensor data and audits must include chain-of-custody and integrity hashes.
- Anonymous submissions are allowed but must provide verifiable artifacts or corroboration.
- Manipulated or incomplete evidence triggers heightened scrutiny or dismissal.
- Evidence admissibility is recorded with rationale in the case record.

## Conflict of Interest & Recusal
- Panelists must declare conflicts before accepting assignment.
- Any party may challenge a panelist for cause; the Clerk assigns a replacement if the challenge is upheld.

## Appeals, Stays, and Emergency Injunctions
- **Stay**: available when enforcement would cause irreparable harm; requires panel majority.
- **Emergency injunction**: issued by duty judge within 24 hours; expires unless ratified within 7 days.
- **Escalation**: expanded panel review with independent oversight.

## Judicial Independence & Role Separation
- Adjudicators cannot serve as enforcement operators for the same case.
- Clerk controls docket integrity and publication independent of panel decisions.
- Panel rotations and conflict screening prevent capture.

## Publication & Recordkeeping
- Public docket shows case metadata, timelines, and final decisions.
- Decisions reference applicable policies and include enforcement steps and verification checkpoints.
- All records are versioned and hashed; sensitive data is redacted but retention is preserved for audit.
- Publication tiers: public summary, restricted ruling, or sealed record.
