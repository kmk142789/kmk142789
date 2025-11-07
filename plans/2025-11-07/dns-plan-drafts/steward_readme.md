# Steward Review Summary – DNS Plan Drafts

## Decision Needed
Approve the proposed DNS change plans for echo.example, status.echo.example, and kenya.echo.example so administrators can schedule execution.

## Highlights
- Plans include DID TXT record, DMARC enforcement, CA restriction, CDN alignment for status lists, and Kenya-specific verification TXT/A records.
- Pre-change snapshots stored in `artifacts/prechange_records/` for rapid rollback.
- Validation and rollback steps detailed within each YAML plan.

## Outstanding Checks
- Confirm IP ownership of 196.201.45.18 aligns with Kenyan hosting agreement.
- Validate CDN certificate coverage before CNAME change.
- Ensure registrar contact authorizations current (<12 months).

## Approvals Requested
- ✅ Consent to publish DID and DMARC records.
- ✅ Authorize CDN CNAME swap for status lists.
- ✅ Approve Kenya API endpoint exposure and verification TXT value.

## Risks & Mitigations
- Misconfiguration risk mitigated via prechange snapshots and TTL adjustments.
- Regulatory risk mitigated by including jurisdictional TXT metadata.
- Execution requires steward sign-off before DNS administrators act; no changes applied yet.

## Next Steps after Approval
1. Schedule maintenance window and execute per plan order.
2. Capture dig/curl outputs and attach to `attestations.jsonl` as proof of completion.
3. Monitor email deliverability and API health dashboards for 48 hours post-change.
