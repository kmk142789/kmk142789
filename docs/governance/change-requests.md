# Change Requests

Change Requests (CRs) describe proposed governance actions and are validated through a strict YAML schema plus higher-level integrity checks.

## Schema
- Location: `echo-os-prime/schemas/change-request.schema.yaml`
- Required fields: `id`, `title`, `description`, `proposedBy`, `signers`, and `uql`.
- Optional fields: `quorum` (defaults to 2), `metadata`, and `ledgerAttestation` for traceability.

## Validation Flow
1. **Structural Integrity**: AJV validates CRs against the YAML schema.
2. **UQL Consistency**: The UQL statement must reference the declared target, omit semicolons, and be longer than 5 characters.
3. **Ledger Attestation**: When provided, the attestation must include a source, non-negative cursor, and hex hash.
4. **Quorum Check**: At least two unique signers are required by default; duplicates cause rejection.

## CLI Submission
Run the CLI from the repo root:

```bash
pnpm governance:cr submit path/to/change-request.yaml
```

The command loads YAML, validates it, and prints a human-readable decision (`accepted`, `rejected`, or `needs_more_signers`).

## Governance Kernel Integration
`GovernanceKernel.submit` wraps the validator, logs `CR_ACCEPTED` events on success, and updates the SCI score based on ledger history. Missing quorum moves the kernel into a `DEGRADED` phase until additional signers arrive.
