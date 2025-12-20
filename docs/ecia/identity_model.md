# ECIA Canonical Identity Model

## Scope
ECIA is the canonical identity authority across the Echo ecosystem. This model defines
how identity is represented for people, institutions, systems, agents, and autonomous
devices so that issuance, verification, delegation, and revocation are consistent
across every authority domain.

## Entity Classes
| Entity type | Description | Examples |
| --- | --- | --- |
| `individual` | Human identity bound to legal name, jurisdiction, and verification evidence. | Citizens, operators, auditors |
| `institution` | Organizational identity with legal status, governance bindings, and signatory roles. | Treasury, Judiciary, EOAG |
| `system` | Deterministic software or platform identity with controlled keys. | DBIS, EFCTIA, registry nodes |
| `agent` | Autonomous software agent with scoped roles and delegated authority. | Audit bot, compliance agent |
| `autonomous_device` | Physical or cyber-physical device with mission constraints. | Drones, IoT gateways |

## Core Identity Record
Each ECIA identity record MUST include:
- **ECIA ID:** immutable canonical identifier (`ecia_id`).
- **Entity type:** one of the entity classes above.
- **Legal identity:** legal name, jurisdiction, and governing body references.
- **DID + key material:** DID URI, verification keys, and rotation schedule.
- **Status:** `active`, `suspended`, `revoked`, or `retired`.
- **Assurance level:** evidence strength from verification (KYC tier, device attestation).
- **Roles and authorities:** role bindings that determine who can sign, approve, spend, audit.
- **Delegations:** scoped authority grants with expiry and revocation hooks.
- **Audit trail:** evidence-grade attestations linked to issuance and lifecycle events.

## Lifecycle States
1. **Pre-issuance:** identity request captured + evidence bundle prepared.
2. **Verification:** ECIA validation + countersignature if required by role.
3. **Issuance:** canonical identity record anchored + signed.
4. **Delegation:** roles and authority grants issued as verifiable credentials.
5. **Suspension:** temporary halt with clear reason, expiry, and escalation path.
6. **Revocation:** permanent withdrawal + propagation to all enforcement hooks.
7. **Reinstatement/Rotation:** controlled restart with key rotation and audit notes.

## Authority Binding
Identity records bind directly to authority scopes:
- **Execution:** who can act, sign, approve, or spend.
- **Audit:** who can attest, inspect, or escalate.
- **Governance:** who can propose, vote, or veto.

Bindings must include:
- Role name
- Authority scope (system + action)
- Required co-signatures
- Expiry and revocation handling

## Evidence-grade Attestations
Every identity event (issuance, delegation, suspension, revocation, rotation) creates
an attestation record that contains:
- Event metadata + timestamps
- Signatures from ECIA and countersigners
- Evidence bundle hashes
- Cross-system propagation hooks

## Interoperability
ECIA records MUST support interoperability with:
- W3C DID + VC data model
- ISO/IEC 18013-5 / mDL (when required)
- NIST 800-63 assurance levels
- eIDAS assurance mapping for external compliance

## References
- `schemas/ecia_identity_record.schema.json`
- `schemas/ecia_attestation.schema.json`
- `config/ecia_identity_hooks.json`
