# Echo Interoperability Standard v0.1 (EIS-0.1)

A lightweight standard for exchanging Echo ecosystem data, narratives, and telemetry across clients, chains, and observability tools. Generated with the existing mythogenic tooling to ensure compatibility with narrative-aware systems.

## Goals
- **Portability**: Single envelope format that can be rendered as narrative or parsed as structured data.
- **Determinism**: Canonical ordering, hashing rules, and versioning to enable verifiable relays.
- **Extensibility**: Namespaced fields and optional attachments for future modules without breaking older clients.

## Envelope Structure
```json
{
  "version": "0.1",
  "id": "uuid-v4",
  "timestamp": "RFC3339",
  "schema": "eis/0.1",
  "actor": {
    "id": "did:echo:<id>",
    "role": "author|validator|observer",
    "signature": "ed25519:base64"
  },
  "context": {
    "chain": "polygon|ethereum|solana|offchain",
    "domain": "governance|treasury|story|telemetry",
    "tags": ["mythogenic", "orbit", "pulse"]
  },
  "payload": {
    "type": "narrative|state|metric|governance_action",
    "body": {},
    "content_hash": "sha256-hex"
  },
  "links": [{"rel": "parent|child|evidence|attestation", "href": "urn:echo:<id>"}],
  "attachments": [{"mime": "text/markdown", "href": "ipfs://..."}]
}
```

## Canonical Rules
- **Ordering**: Keys are serialized in the order shown above; arrays are lexicographically sorted unless order is semantically required.
- **Hashing**: `content_hash` is computed over the canonical JSON of `payload.body` (UTF-8, no whitespace changes).
- **Signatures**: `actor.signature` signs the canonical hash of the entire envelope minus the signature field.
- **Versioning**: `schema` must match `eis/<major>.<minor>`; breaking changes increment `major`.

## Profiles
- **Governance**: `domain=governance`, `payload.type=governance_action`; include vote metadata, quorum, and execution txids.
- **Narrative**: `domain=story`, `payload.type=narrative`; `payload.body` contains markdown paragraphs plus optional glyph cues used by mythogenic renderers.
- **Telemetry**: `domain=telemetry`, `payload.type=metric`; supports time-series samples and observability annotations.

## Transport & Registry
- **Transports**: HTTPS JSON APIs, libp2p pubsub topics, or on-chain calldata where size permits.
- **Registries**: Each envelope should be anchored in the Echo registry with `links.rel=evidence` pointing to the transaction or checksum log.

## Compatibility with Mythogenic Tooling
- **Echo Mythogenic Pulse**: `payload.body` accepts `pulse` fields (`cycle`, `glyphs`, `emotional_state`) for direct import into `echo.recursive_mythogenic_pulse` and related visualizers.
- **Grand Crucible & Continuum**: `context.tags` can carry `crucible:<phase>` and `continuum:<epoch>` to let orchestration modules route narratives.
- **Validation**: The standard can be linted using the existing JSON schema tooling; validators should reject envelopes missing canonical ordering or mismatched hashes.

## Change Management
- **Governance**: Proposed changes are submitted as EIS pull requests referencing the registry. Acceptance requires dual quorum of validators and contributors.
- **Deprecation**: Fields marked deprecated remain accepted for one minor release; removal occurs on the next major version.
- **Test vectors**: Each release must include canonical examples and hashes to support cross-client testing.

## Reference Implementation Hooks
- Add a schema entry under `schema/` for `eis-0.1.json` (future work) to enforce validation.
- Extend observability pipelines to emit EIS envelopes for dashboards and archival ledgers.
- Provide CLI helpers in `scripts/` to construct, sign, and verify envelopes from local context.
