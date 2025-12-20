# ECIA Operational Activation Steps

## Objective
Activate the Echo Citizenship & Identity Authority (ECIA) as the canonical identity
authority across the Echo ecosystem. These steps prioritize the highest-leverage
changes required to make identity mandatory for transactions, governance actions,
audits, and enforcement.

## Priority 1 — Canonical Identity Authority Backbone
1. **Canonical schema enforcement**
   - Use `schemas/ecia_identity_record.schema.json` as the authoritative identity record.
   - Use `schemas/ecia_attestation.schema.json` to serialize issuance, verification,
     delegation, suspension, and revocation events.

2. **Identity lifecycle pipeline**
   - Enforce lifecycle states in every identity record (`active`, `suspended`, `revoked`).
   - Require evidence bundles for issuance + verification.
   - Require signed attestations for delegation and rotation.

3. **Role + authority binding**
   - Bind roles to explicit authority scopes with co-sign requirements.
   - Record all approvals and signatures as attestations for audit.

## Priority 2 — Mandatory Identity Hooks Across Core Authorities
The following systems MUST reject operations without ECIA identity bindings:
- **DBIS:** Transaction intents require ECIA identity attestations.
- **EFCTIA:** Transaction integrity audits enforce ECIA identity authority.
- **EOAG:** Audit entries must reference ECIA identities and proof bundles.
- **Judiciary:** Dispute actions must reference ECIA identities and case authority.
- **Treasury:** Transfers and approvals require ECIA-bound identity credentials.
- **Drones:** Autonomous devices must present ECIA device identities.

The canonical hook requirements are tracked in:
- `config/ecia_identity_hooks.json`

## Priority 3 — Cryptographic Anchoring + Rotation
- Bind ECIA identities to DID documents and verifiable credential proofs.
- Record key rotation events as attestations.
- Ensure continuity by hashing credential chains into audit logs.

## Priority 4 — Evidence-grade Audit Trails
- Every identity event emits a signed attestation.
- Attestations reference evidence bundles and external jurisdictional anchors.
- Audit entries are appended to system-specific ledgers (DBIS, Treasury, Judiciary).

## Priority 5 — Interoperability Controls
- Emit compatibility metadata for W3C DID/VC, NIST 800-63, and eIDAS mappings.
- Record external assurance data inside the identity record and attestation payload.

## Activation Checklist
- [ ] ECIA schemas available and referenced across systems.
- [ ] DBIS and EFCTIA validation enforce ECIA identity hooks.
- [ ] Authority bindings recorded for issuance, delegation, revocation.
- [ ] Audit trail hooks mapped for DBIS, EOAG, Judiciary, Treasury, and drones.
- [ ] External interoperability mapping defined per record.
