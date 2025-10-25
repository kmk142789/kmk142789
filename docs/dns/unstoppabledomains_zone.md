# UnstoppableDomains.com Zone Snapshot (2025-10-25)

This snapshot captures the public DNS zone exported for `unstoppabledomains.com`
on 2025-10-25 at 18:22:20. The raw zone file is tracked at
`data/dns/unstoppabledomains.com.zone` for archival and offline analysis.

## Contents

- **SOA** — Cloudflare nameservers remain the primary authority of record.
- **NS** — Delegation currently points to Cloudflare (`brian`, `emerie`) and the
  Google Domains NS quartet used for validation. These are preserved verbatim to
  reflect the exported state.
- **A records** — Both the apex and `shop`/`staging` subdomains resolve to Fastly
  and Fastly-backed IP ranges, mirroring the CDN configuration.
- **CAA** — Certificate issuance is restricted to Google, Let’s Encrypt, and
  Amazon, providing coarse guardrails around TLS automation.
- **CNAME** — Application endpoints (API, Auth, Docs, Email, Support, etc.) are
  consolidated behind Fastly, Google, Freshdesk, and SendGrid managed targets.
- **MX** — Google Workspace handles inbound mail with the standard five-priority
  host set.
- **TXT** — Records include DKIM keys, SPF policy, wallet verification markers,
  and site-verification tokens for Google, Facebook, and Cursor.

## Usage

- **Historical reference** — Bridge operators and provenance workflows can
  diff future exports against this baseline to detect material DNS changes.
- **Operational readiness** — Before applying to production, update the SOA
  metadata and authoritative NS entries per the upstream instructions embedded
  in the zone file.
- **Cross-checks** — Combine with `tools/unstoppable_resolver.js` to validate
  that Unstoppable metadata pushes align with current DNS state across CDN and
  email providers.
