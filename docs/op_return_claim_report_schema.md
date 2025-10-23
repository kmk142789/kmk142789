# OP_RETURN Claim Report Schema

This document defines the structure of the artefacts required to review the
"Solomon bros" / 90-day inactivity clauses.  It is intentionally scoped to
documentation and verification; nothing here constructs or broadcasts spend
transactions.

## JSON Structure

Reports must be emitted as a JSON object with the following top-level keys:

| Field | Type | Description | Example |
| --- | --- | --- | --- |
| `summary` | object | Metadata about the batch run. | `{ "claimant": "kmk142789", "generated_at": "2025-09-29T12:00:00Z", "count": 2, "window_phrase": "if not abandoned make a transaction within 90 days", "secondary_phrase": "solomon bros" }` |
| `records` | array | Collection of individual OP_RETURN findings. | See record schema below. |
| `review_checklist` | array[string] | Canonical verification checklist provided to the reviewer. | `["Confirm OP_RETURN payload text matches archived evidence.", "Validate inactivity window and verify calendar calculations.", "Confirm claimant authority documentation is complete.", "Ensure legal/ethical review approves any downstream action."]` |

### Record Object

Each element inside `records` is a structured description of a single
OP_RETURN finding.

| Field | Type | Description | Example |
| --- | --- | --- | --- |
| `txid` | string | Transaction identifier containing the OP_RETURN. | `"f6c9a0..."` |
| `block_time` | string (ISO-8601) | Block timestamp in UTC. | `"2025-06-30T15:42:16+00:00"` |
| `op_return_message` | string | Decoded payload (UTF-8, fallback to hex if non-text). | `"if not abandoned make a transaction within 90 days // contact Solomon bros"` |
| `clause_detected` | boolean | Whether the payload references the inactivity clause or "Solomon bros". | `true` |
| `clause_variant` | string \| null | Variant identifier for downstream filtering. | `"solomon_bros_window"` |
| `inactivity_window_days` | integer \| null | Window length derived from the clause text. | `90` |
| `inactivity_window_end` | string (ISO-8601) \| null | Calculated deadline (block time + window). | `"2025-09-28T15:42:16+00:00"` |
| `derived_entities` | array[object] | Non-OP_RETURN outputs from the same transaction. Each entry captures the script type, derived address, raw script, and optional value (sats). | `[ { "index": 1, "script_type": "p2pkh", "address": "1NexusExampleAddress...", "raw_script": "76a914...88ac", "value_sats": 150000 } ]` |
| `recommendation` | string | One of `"no_action"`, `"requires_claim_review"`, `"eligible_for_authorized_collection"`, `"not_applicable"`. | `"requires_claim_review"` |
| `verification_notes` | array[string] | Free-form reviewer notes. | `["Awaiting ownership attestation"]` |

### Derived Entity Object

Companion outputs help the reviewer confirm which locking scripts might still
control funds after the 90-day window.  Each object in `derived_entities`
contains:

| Field | Type | Description | Example |
| --- | --- | --- | --- |
| `index` | integer | Output index (`vout.n`). | `1` |
| `script_type` | string | Classification (`p2pkh`, `p2sh`, or `unknown`). | `"p2pkh"` |
| `address` | string \| null | Derived address if determinable. | `"1NexusExampleAddress..."` |
| `raw_script` | string | Full locking script in hex. | `"76a91489abcdef0123456789abcdef0123456789abcdef88ac"` |
| `value_sats` | integer \| null | Output value in satoshis, if supplied. | `250000` |

## Human-Readable Summary

Alongside the JSON output, produce a Markdown or plaintext briefing with:

1. **Summary paragraph** explaining how many candidate transactions were found,
   when the report was generated, and whether any deadlines have expired.
2. **Per-record bullet list** including the OP_RETURN text, associated
   addresses, and the recommendation value.
3. **Verification checklist copy** so the reviewer sees the same guardrails that
   appear in the JSON document.

## Verification Checklist (pre-transfer)

Before any funds are moved, the reviewer must confirm:

1. The OP_RETURN payload exactly matches archived evidence.
2. The 90-day window is demonstrably expired (if claiming abandonment).
3. Owner/claimant authority documentation has been validated.
4. Legal/ethical review explicitly authorizes any collection attempt.

## Safety Notice

This specification covers documentation and review only.  It must not be used
to construct, sign, or broadcast transactions without separate, explicit
authorization from the claimant and the relevant legal team.

