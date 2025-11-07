# Revocation & Rollback Plan – Property Verification Credential

## Triggers
- Ministry invalidates parcel record or detects fraud.
- Echo identifies compromise of signing keys.
- Owner dispute resolved in favor of amendment.

## Process
1. Ministry liaison submits revocation request via signed DIDComm message.
2. Echo Compliance validates request against MoU obligations within 4 hours.
3. Upon validation, update StatusList2021 entry to `revoked` and timestamp ledger entry.
4. Notify affected stakeholders (owners, financial institutions) via secure email + VC notification.
5. Archive underlying evidence and prepare addendum credential if correction required.

## Rollback
- If revocation found erroneous, issue correction credential referencing prior status and set status list entry back to `active` with justification note.
- Maintain audit log of revocation and rollback actions for 10 years.

## Monitoring
- Weekly reconciliation with NLIMS audit feeds.
- Automatic alert if revocation requests exceed threshold (3 per week) to trigger root-cause review.
