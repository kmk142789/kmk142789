# Verification Playbook – Research Credentials

## Purpose
Ensure third parties can verify that Echo-issued research credentials reference valid IRB approvals and active FWA status.

## Credential Profile
- Type: `ResearchAuthorizationCredential`
- Schema: `https://echo.example/schemas/research/authorization-v1`
- Status: `https://status.echo.example/lists/research.json#list`

## Verification Steps
1. **Decode Credential:** Use `didkit vc-verify` or equivalent to inspect proof and issuer DID.
2. **Check Status List:**
   ```bash
   curl https://status.echo.example/lists/research.json | jq '.credentialStatus[] | select(.id=="<credentialStatus.id>")'
   ```
   Ensure `status` = `active`.
3. **Validate IRB Reference:** Confirm `credentialSubject.irbRegistration` matches the reliance agreement (e.g., `IRB00011223`).
4. **Confirm FWA Active:** Query OHRP database for `FWA00040012` and confirm expiration > current date.
5. **Audit Trail:** Retrieve hash from `attestations/decisions` ledger entry referenced in the credential `evidence` section.

## Revocation Triggers
- IRB approval lapse.
- Non-compliance finding by OHRP.
- Investigator training expiration.

## Contact
For verification issues email `research-compliance@echo.example` with credential hash and verification logs.
