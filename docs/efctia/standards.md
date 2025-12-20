# EFCTIA Transaction Integrity Standards

## Transaction State Model
EFCTIA recognizes the following canonical states:
1. **proposed**
2. **authorized**
3. **settled**
4. **disputed**
5. **reversed**
6. **finalized**

## Integrity Checks
Each transaction must satisfy the following minimum integrity checks:
- **Provenance**: source system and evidence anchor.
- **Authorization Chain**: signers and approval trail.
- **Identity Binding**: link to Echo Identity Authority proof.
- **Purpose Declaration**: declared intent with human-readable rationale.

High-value or cross-institution transfers must include cryptographic attestations
linked to the Attestation Framework.

## Compliance-by-Construction
EFCTIA encodes AML, counter-fraud, and sanctions signaling directly into transaction
schemas. Compliance tiers are mandatory:
- **humanitarian**
- **public_service**
- **commercial**
- **sovereign**

Compliance metadata must travel with transactions while preserving sensitive data.
EFCTIA requires sealed references for sensitive inputs and public summaries for
external transparency.

## Dispute & Enforcement Hooks
- EFCTIA binds disputes to the Echo Judiciary Council and Tribunal of Sovereign
  Arbitration.
- Reversals, freezes, and clawbacks require dispute references.
- Enforcement actions must be logged as immutable attestations.

## DBIS Integration
- EFCTIA validation is mandatory for DBIS settlement finality.
- Pre-settlement and post-settlement integrity audits are required.
- Offline transaction batches may be accepted with delayed EFCTIA validation, but
  settlement finality is gated on a successful audit.
