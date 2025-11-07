# DNS TXT Anchor Publication & Verification Plan

## Purpose
- Publish verifiable DNS TXT anchors containing issuer DIDs and manifest digests across all domains managed by the Echo stewardship.
- Provide tooling to automate record publication, propagation monitoring, and integrity checks against repository manifests.
- Establish audit trails linking DNS assertions back to signed assets in `pulsenet-manifest.json` and related ledgers.

## Guiding Principles
- **Consistency:** all controlled domains must expose uniform record formats with canonical key naming.
- **Defense-in-depth:** DNS updates should be signed (DNSSEC where available) and cross-validated against ledger attestations.
- **Continuous verification:** propagation checks and digest validation must run on schedule with alerts for drift.

## Workstreams

1. Record schema & manifest linkage
   - Define the DNS TXT payload template referencing issuer DID, manifest digest (SHA-256), timestamp, and contact metadata.
   - Map repository manifests (`pulsenet-manifest.json`, `federated_attestation_index.json`, etc.) to DNS payload fields.
   - Document update governance for new issuers or manifest revisions.
   :::task-stub{title="Design DNS anchor payload schema"}
   1. Draft `docs/dns/dns_anchor_schema.md` outlining required TXT fields, encoding rules, and example records.
   2. Implement `tools/manifest_digest.py` to compute digests for manifests under `manifest/` and `pulsenet-manifest.json`.
   3. Create `configs/dns_anchors.json` mapping domains to issuer IDs, manifests, and publication status.
   :::

2. Publication automation
   - Build scripts or Terraform modules to push TXT records to DNS providers covering all controlled domains.
   - Support both API-based management and manual export for registrars lacking automation.
   - Track record versions and ensure rollback paths.
   :::task-stub{title="Automate DNS TXT record publication"}
   1. Develop `ops/dns/publish_dns_txt.py` interfacing with provider APIs (e.g., Cloudflare, Route53) using credentials stored in existing ops vault patterns.
   2. Provide fallback templates under `ops/dns/manual_records/` for registrars requiring human submission.
   3. Write `ops/runbooks/dns_anchor_update.md` describing change management, approvals, and rollback procedures.
   :::

3. Propagation monitoring & verification
   - Continuously poll DNS to confirm TXT record presence and correctness across global resolvers.
   - Compare retrieved records against expected digests and issuer metadata.
   - Alert on missing, stale, or mismatched values.
   :::task-stub{title="Implement DNS anchor verification pipeline"}
   1. Create `tools/dns_anchor_checker.py` that queries domains via multiple resolvers and validates payloads.
   2. Integrate verification results into `pulse_history.json` and optionally `pulse_dashboard/` widgets.
   3. Configure alert rules in `ops/alerts/dns_anchors.yml` for propagation failures or digest mismatches.
   :::

4. Audit & compliance reporting
   - Maintain historical evidence of DNS publications, including timestamps, digests, and approval artifacts.
   - Align reports with requirements in `SECURITY.md` and any external attestations.
   - Provide periodic summaries for stakeholders.
   :::task-stub{title="Deliver DNS anchor audit reporting"}
   1. Store verification artifacts under `artifacts/dns_anchors/` with signed JSON results per domain.
   2. Generate quarterly summaries via `reports/dns/dns_anchor_status.md` detailing coverage and outstanding issues.
   3. Ensure reports link back to signatures in `reality_breach_∇_fusion_v4.echo.json` or relevant provenance ledgers.
   :::

## Dependencies & Open Questions
- Confirm registrar API capabilities and credential management aligning with `ops/` security guidelines.
- Decide on canonical timestamp format and time synchronization source (e.g., GPS-backed NTP) for TXT records.
- Evaluate need for additional DID verification beyond DNS (e.g., web-based DID documents or ledger anchors).

## Risks
- DNS provider propagation delays could trigger false positives; mitigate with configurable grace periods.
- Manual registrars increase human error risk; provide templates and peer review steps.
- Compromised DNS credentials could allow record tampering; enforce MFA and audit logging.

## Next Steps
- Review scope with the digital sovereignty and infrastructure stewards for alignment.
- Prioritize schema and automation workstreams to unblock record publication.
- Schedule initial propagation tests once TXT records are deployed to validate tooling end-to-end.
