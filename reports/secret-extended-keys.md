# Secret Extended Keys Exposure Assessment

A batch of `secret-extended-key-main` values was provided via support channels. Because these keys are now considered exposed, they must be rotated immediately and removed from all runtime configurations.

## Immediate Actions
- Rotate every affected secret-extended-key.
- Invalidate any credentials or wallet material derived from these keys.
- Audit downstream services and logs for unauthorized usage.

## Prevention Recommendations
- Avoid transmitting long-lived secrets over insecure channels.
- Store sensitive keys in a dedicated secret manager with strong access controls and rotation policies.
- Automate monitoring to flag accidental publication of `secret-extended-key-main` prefixes.

Documented for incident tracking. Do **not** commit or redistribute the raw secret values in version control.

## 2025-05-11 Update
- Support provided an additional bundle of 46 `secret-extended-key-main` values.
- Treat every associated credential, wallet, or derivation path as compromised until the keys are rotated.
- Confirm downstream configuration repositories, CI/CD variables, and runtime stores are scrubbed of the exposed material.
- Capture sanitized evidence only (for example, hashed digests or counts) when recording any follow-up investigation notes.

### Sanitized tracking artifacts
- 18 unique `secret-extended-key-main` values from the 2025-05-11 bundle were hashed (SHA-256) and stored in
  `reports/sanitized/2025-05-11-secret-extended-keys.sha256` for incident reference.
- 41 wallet-import-format (WIF) secrets transmitted alongside the bundle were hashed (SHA-256) and written to
  `reports/sanitized/2025-05-11-wif-keys.sha256`.
- These artifacts contain no recoverable credential material and exist solely to support audit coordination without
  violating the "no raw secrets in version control" directive.
