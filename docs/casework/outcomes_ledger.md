# Outcomes Ledger

The case outcomes ledger is an append-only JSONL file that captures decisions, closures, and other material outcomes.

- **Path**: `ledger/case_outcomes.jsonl`
- **Schema**: `schemas/case_outcome.schema.json`

## Entry requirements

Each line in the ledger MUST be a single JSON object that includes:

- `entry_id`
- `case_id`
- `timestamp`
- `stage`
- `outcome_type`
- `summary`
- `owner`

Optional fields: `artifacts`, `metrics`, `notes`.

## When to write entries

- Decision issued
- Settlement reached
- Escalation approved
- Closure completed
- Handoff executed

## Validation

Continuous integration validates the JSONL entries against the schema to ensure each outcome is traceable and consistent.
