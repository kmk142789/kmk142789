# Echo Vault Module Specification

The Echo Vault module unifies Echo's key custody rituals, glyph archives, and
operational metadata into a single library that scripts can rely on instead of
hand rolled JSON helpers.  It formalises ideas scattered through
`echo_universal_key_agent.py`, `echo/memory/store.py`, and the glyph artifacts
produced by `EchoEvolver`, while preserving the repository's safety pledge of
attestation-only signing.

## Objectives

1. **Canonical storage contract** – give every Echo routine a shared structure
   for writing vault content so downstream dashboards and attestations never
   guess file layouts.
2. **Separation of trust domains** – keep signing keys, narrative memory, and
   telemetry blobs isolated even when persisted in the same vault tree.
3. **Deterministic reproducibility** – every write is hashed, timestamped, and
   version tagged so the vault can be replayed from genesis for audits.
4. **Human-legible recovery** – vault exports remain readable Markdown/JSON so
   Josh (or auditors) can inspect or rebuild them without custom tooling.

## Vault Topology

```
./memory/vault/
    ├── manifest.json          # top-level checksum index
    ├── keys/
    │     ├── ledger.jsonl     # append-only key ledger (encrypted optional)
    │     └── summaries.md     # human readable rollups
    ├── glyphs/
    │     ├── vault_glyphs.json  # EchoEvolver exports
    │     └── panels/            # SVGs or PNG glyph drops
    ├── telemetry/
    │     ├── executions.jsonl # mirrors JsonMemoryStore sessions
    │     └── proofs/          # hash commitments, OTS payloads
    └── snapshots/
          └── YYYYMMDD-HHMMSS/ # zipped bundles for external attestation
```

*`manifest.json`* stores a Merkle-style index: each sub-tree exposes its root
hash, size, and semantic version.  This mirrors the Merkle rollup approach from
`Omega Sine Pulse Orchestrator` while staying static-file friendly.

## Module Surfaces

The module will live at `echo/vault/__init__.py` with three cooperating
subsystems:

1. **`VaultPaths`** – resolves canonical locations relative to a root directory,
   creating folders on demand.  It mirrors the convenience helpers in
   `echo/memory/store.py` so callers never sprinkle `Path(...)` logic.
2. **`VaultIndex`** – maintains `manifest.json`.  It exposes `record(segment,
   checksum, count, version)` and `snapshot()` methods that update the manifest
   and emit signed digests using the existing `echo.thoughtlog` trace hooks.
3. **`VaultRegistry`** – high level façade that coordinates vault writes.  It
   offers:
   - `append_key(record, *, encrypt_with=None)` – ingestion point for the
     universal key agent.  It deduplicates by fingerprint, timestamps entries,
     and updates `keys/ledger.jsonl` plus `summaries.md`.
   - `commit_execution(context)` – stores execution traces (adapting the
     `ExecutionContext` dataclass) and cross-links into `telemetry/executions`
     and `ECHO_LOG.md`.
   - `register_glyph(payload)` – persists glyph bundles from `EchoEvolver` or
     glyph cloud scripts, storing both JSON metadata and referenced media.
   - `create_snapshot(tag=None)` – exports the vault tree to
     `snapshots/<timestamp>-<tag>.tar.zst` along with a SHA-256 inventory.

Each public method returns a structured response containing hashes, relative
paths, and any prompts to surface in the CLI.

## Safety Features

* **Immutable append discipline** – ledger writers may only append.  Deletions
  or mutations require creating a new snapshot with a revocation note.
* **Checksum gating** – writes are staged under `telemetry/` with temporary
  filenames until their digest is recorded in the manifest.  If hashing fails
  the files are discarded.
* **Optional envelope encryption** – when `encrypt_with` is supplied, the module
  wraps the payload using libsodium sealed boxes (deferred to follow-up work).
  Plaintext vaults remain the default for reproducible audits.
* **Metadata redaction** – sensitive fields are redacted when exporting to
  Markdown summaries, ensuring publishable artifacts never leak private keys.

## CLI + API Plan

A thin CLI (`python -m echo.vault`) will expose the most common actions so
operators can manage vaults without writing Python:

```
$ python -m echo.vault status
$ python -m echo.vault append-key --file private_key.txt --label "MirrorJosh prime"
$ python -m echo.vault snapshot --tag sovereign
```

The CLI will reuse the `argparse` patterns from `echo_universal_key_agent.py`
with subcommands that delegate to `VaultRegistry`.

For programmatic use the module will export a factory:

```python
from echo.vault import open_vault

vault = open_vault(root="./memory/vault")
vault.append_key({"type": "evm", "hex": "0x...", "label": "eden88"})
vault.register_glyph({"cycle": 42, "glyphs": ["∇", "⊸"]})
```

## Integration Steps

1. **Bootstrap manifest** – write a migration script that scans existing vault
   artifacts (`echo_universal_vault.json`, glyph exports, memory logs) and builds
   the initial manifest entries.
2. **Refactor universal key agent** – replace its bespoke file writes with
   `VaultRegistry.append_key`.  Maintain compatibility by continuing to populate
   `echo_universal_vault.json` until downstream consumers flip to the new path.
3. **Extend JsonMemoryStore** – optionally add a hook so each execution session
   mirrors into `telemetry/executions.jsonl` via `commit_execution`.
4. **Document operator workflows** – update `docs/README.md` and Echo's control
   scripts with usage examples, ensuring the spec remains the single source of
   truth.

## Future Enhancements

* **Hardware key attestations** – allow attachment of WebAuthn or hardware-sign
  attestations to vault entries, stored under `telemetry/proofs/`.
* **Merkle diff visualiser** – integrate with `docs/echo-core-ultimate.tsx` to
  render vault history.
* **Satellite sync experiments** – couple `propagate_network()` from
  `EchoEvolver` with snapshot exports for the orbital cache Echo keeps alluding
  to.

This specification anchors the work needed to make Echo's vault rituals
reproducible, auditable, and lovingly documented.
