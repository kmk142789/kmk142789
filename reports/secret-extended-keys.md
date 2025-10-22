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
