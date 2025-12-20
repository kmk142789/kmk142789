# EFCTIA Schemas

EFCTIA schemas are canonical, versioned definitions for transaction integrity and
financial conduct attestations. They bind to Echo identity, DNS substrate, governance
kernel, and attestation frameworks.

## Transaction Schema
- File: `schemas/efctia_transaction.schema.json`
- Purpose: Defines transaction integrity payloads, compliance metadata, and
  settlement references.
- Required bindings: `identity_binding`, `dns_substrate_ref`,
  `governance_kernel_ref`.

## Financial Conduct Attestation Schema
- File: `schemas/efctia_attestation.schema.json`
- Purpose: Defines immutable attestations for compliance actions, enforcement
  decisions, and audit outcomes.
- Required bindings: `attestation_id`, `authority`, `event_type`,
  `transaction_reference`, `governance_kernel_ref`.

## Schema Distribution
Schemas are distributed alongside Echo Records & Archives Authority artifacts and are
consumed by DBIS settlement workflows, Treasury Authority audit processes, and
Judiciary Council enforcement pipelines.
