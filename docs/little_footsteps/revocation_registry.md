# Little Footsteps Credential Revocation Registry

The VC issuer now exposes a minimal revocation registry so verifiers can query whether a credential has been revoked and why. The registry is append-only and mirrored to JSONL for independent audit trails.

## API endpoints

- `GET /credentials/:id/status` — returns the current status for the credential ID (revoked flag, timestamps, reason, actor, and originating ledger event if available). Returns `404` when the credential is unknown.
- `POST /credentials/:id/revoke` — marks the credential as revoked. Accepts optional `reason` and `actor` fields in the JSON body and returns the updated status payload.

## Persistence

- Status changes are written to Postgres in the `issued_credentials` table via `revoked_at`, `revocation_reason`, and `revoked_by` columns.
- Every revocation is also appended to `state/little_footsteps/credential_status.jsonl` (override with `CREDENTIAL_STATUS_LOG_PATH`) so the dashboard and auditors have a lightweight feed.

## Usage example

```bash
curl -X POST http://localhost:4000/credentials/vc:donation:123/revoke \
  -H "Content-Type: application/json" \
  -d '{"reason": "issuer request", "actor": "guardian"}'

curl http://localhost:4000/credentials/vc:donation:123/status
```
