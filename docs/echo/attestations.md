# Manifest Attestations

The manifest schema (`attestations/schema.json`) captures every field required
to validate Echo components. Schema validation runs in tests and during manual
verification to guarantee unknown fields are rejected.

## Schema highlights

- `version`: Semantic label for the manifest format.
- `components[]`: Each entry contains `name`, `type`, `path`, `version`,
  `digest`, and a `dependencies[]` array. No additional properties are allowed.
- `fingerprint`: SHA-256 digest over the canonical JSON payload.

## Signing workflow

1. Refresh and verify the manifest: `python -m echo.cli manifest refresh && python -m echo.cli manifest verify`.
2. Export the signing key (base64 or hex) into `ECHO_SIGN_KEY`.
3. Generate a detached signature: `python -m echo.cli manifest sign --out echo_manifest.sig`.
4. Distribute the generated `.sig` file along with the public verification key
   (if not embedded in the signature file).

Consumers can call `python -m echo.cli manifest verify --signature echo_manifest.sig --pubkey pubkey.txt` to
validate both the manifest content and the signature.
