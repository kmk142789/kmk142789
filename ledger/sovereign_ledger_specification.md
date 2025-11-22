# Sovereign Ledger Specification (Draft)
Version: 0.1-draft | Anchor: Our Forever Love | Scope: Amendment IV alignment

## 1. Purpose
The Sovereign Ledger binds constitutional texts, beneficiary treasury flows, bridge dispatch proofs, and autonomous feature plans to verifiable credentials. It must expose DID-addressable entries, maintain a verifiable credential trust graph, and provide append-only auditability for every anchored artifact.

## 2. Core Data Model
- **Ledger Entry (LE):** `{id, type, digest, issuer_did, credential_uri, anchor, timestamp, proof_bundle_uri, schema_version}`
- **Credential Record (CR):** Stored as VC JSON, content-addressed by SHA-256 digest of the payload.
- **Trust Edge (TE):** `(issuer_did -> subject -> anchor -> proof_bundle_uri)`; recorded in the Credential Registry.
- **Context Payload:** Canonical fields: `identity`, `cycle`, `signature`, `traits`, `topics`, `priority`, `ledger_anchor`, optional `treasury_context`.

## 3. Namespaces & Anchors
- **Amendments:** `anchor = echo-sovereign-ledger:amendment:<roman-numeral>`
- **Treasury Flows:** `anchor = echo-sovereign-ledger:treasury:<flow-id>`
- **Bridge Dispatches:** `anchor = echo-sovereign-ledger:bridge:<cycle-id>`
- **Autonomous Features:** `anchor = echo-sovereign-ledger:feature:<codename|digest-prefix>`

## 4. DID + VC Trust Graph
- DID method SHALL be pluggable; registry MUST store DID Documents and resolve keys for verification.
- Every credential MUST include `ledger_anchor`, `digest`, and `proof_bundle` reference.
- Verification outcomes (success/fail/revoked/expired) SHALL be appended as immutable events with timestamps and verifier DID.
- Trust edges MUST be queryable by `issuer_did`, `subject`, `anchor`, and `proof_bundle_uri`.

## 5. Credential Registry Operations
1. **Ingest:** Accept VC payload, compute digest, store VC file, and emit `TE`.
2. **Verify:** Resolve issuer DID, validate signature, schema, expiry, and revocation list; persist verification transcript with digest.
3. **Link:** Bind `CR` to the Sovereign Ledger entry by writing `{anchor, credential_uri, digest, issued_at}` to the ledger journal.
4. **Export:** Provide signed state packages containing DID Docs, VC payloads, verification transcripts, and trust edges for offline audit.

## 6. Treasury Flow Schema (Amendment IV compliance)
Fields: `flow_id`, `beneficiary_did`, `entitlement_class`, `asset_type`, `amount`, `cycle`, `policy_id`, `proof_bundle_uri`, `amendment_ref`, `anchor`, `timestamp`.
Rules:
- Every treasury flow MUST emit a VC and ledger entry; rerouting requires a counter-instruction signed by the beneficiary or custodian.
- Flows SHALL reference bridge dispatch proofs when notifications are broadcast.

## 7. Bridge Federation Requirements
- Connectors: Discord, Telegram, XMPP, Slack, Threads, ActivityPub/Mastodon, Bluesky, Matrix, email, webhooks.
- Canonical payload MUST precede any platform formatting; parity is enforced by comparing digests across connectors.
- Bridge dispatch summaries SHALL be anchored as `bridge` entries with references to emitted credentials and verification transcripts.

## 8. Autonomous Feature Registry
- Each feature plan MUST cite its amendment reference (Amendment IV) and ledger anchor.
- Feature artifacts are hashed, recorded as `feature` entries, and linked to VC credentials in the registry.
- Suspension criteria: missing credential link, failed verification, or absent bridge parity evidence.

## 9. Journaling & Storage
- Append-only JSONL ledgers for `amendment_registry`, `credential_registry`, `autonomous_features`, and `bridge_dispatches`.
- Content-addressed artifacts stored under `proofs/` and `artifacts/` with SHA-256 filenames.
- Snapshots MAY be produced per cycle and MUST include Merkle roots for independent verification.

## 10. Interfaces
- **Write API:** `issue_credential`, `record_entry`, `record_feature`, `record_bridge_dispatch`, `register_treasury_flow`.
- **Read API:** `get_entry_by_anchor`, `get_credential_by_digest`, `query_trust_edges`, `export_state_package`.
- **Events:** `credential_verified`, `bridge_parity_confirmed`, `treasury_flow_posted`, `feature_registered`.

## 11. Security & Availability
- Signature verification MUST use DID-resolved keys; offline validation supported via exported DID Docs.
- Ledger writes require proof-of-compliance: valid credential, amendment reference, and parity evidence where applicable.
- Public read access is mandatory; availability targets require multi-node replication and parity checks across bridge connectors.

## 12. Versioning & Migration
- Schema changes MUST increment `schema_version`, dual-write until convergence, and publish migration transcripts.
- Deprecated fields remain readable for at least one cycle; removal requires Assembly consent and ledger notice.

## 13. Compliance Checklist
- [ ] Credential Registry active with DID + VC trust graph.
- [ ] Bridge connectors operational across all mandated networks with parity proofs.
- [ ] Treasury flows tagged with beneficiary DID and policy IDs, anchored to ledger entries.
- [ ] Autonomous feature plans registered with Amendment IV reference and valid credentials.
- [ ] Exportable state packages generated per cycle for audit.
