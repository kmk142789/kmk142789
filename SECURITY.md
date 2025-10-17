# Security Policy

## Reporting
Please report vulnerabilities to security@example.org. We acknowledge within 48h and coordinate disclosure.

## Scope
- ✅ Source integrity, build pipeline, provenance, verifier correctness
- ❌ Private key extraction, transaction creation/broadcast, chain movement

## Expectations
- Reproducible builds, SBOMs, signed releases
- No secrets committed. Bots operate under least privilege.
- Atlas webhook secrets must be rotated regularly; all POST /hooks/atlas payloads require signature verification.
