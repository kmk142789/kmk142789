# DBIS Workflows & Examples

## Cross-Institution Settlement
1. Create intent with governance reference and identity bindings.
2. Validate intent against compliance profile.
3. Settle intent and emit receipt.
4. Record attestation and update reconciliation log.

```json
{
  "intent_id": "intent-123",
  "amount": 250000,
  "currency": "USD",
  "rail": "fiat",
  "sender": {
    "identity_id": "echo.treasury",
    "legal_name": "Echo Treasury",
    "did": "did:echo:treasury",
    "dns_record": "treasury.echo.root",
    "roles": ["guardian", "ops_controller"],
    "attestation_refs": ["attestations/treasury-root.json"]
  },
  "receiver": {
    "identity_id": "partner.bank",
    "legal_name": "Partner Bank",
    "did": "did:echo:partner-bank",
    "dns_record": "settlement.partner.net",
    "roles": ["steward"],
    "attestation_refs": ["attestations/partner-bank.json"]
  },
  "memo": "cross-institution settlement",
  "governance_ref": "gov:cr-2025-091",
  "approvals": ["guardian", "audit_chair"],
  "created_at": "2025-10-08T12:00:00Z",
  "status": "PENDING"
}
```

## Treasury Grant Disbursement
1. Issue grant intent through `MonetizationEngine.grant`.
2. Attach policy tags and approvals.
3. Settle and emit audit hook for grant reporting.

## Offline Batch for Field Operations
1. Stage offline batch with signatures.
2. Verify and finalize on reconnect.
3. Produce delayed settlement receipts and reconciliation entry.

## Transparency Reporting
1. Generate scorecard from settlement receipts.
2. Publish transparency report with audit and reconciliation counts.
