# Echo Manifest

The Echo manifest is the auto-maintained source of truth for engines, long-lived
state snapshots, and auxiliary kits ("akits"). Each component entry contains its
relative path, declared version, SHA-256 digest, and explicit dependencies. The
manifest is rebuilt deterministically, so the same repository state always
produces the same JSON payload and fingerprint.

## Generating and verifying

Use the CLI to manage the manifest:

```bash
python -m echo.cli manifest refresh        # rebuilds echo_manifest.json
python -m echo.cli manifest verify         # compares the file against a rebuild
python -m echo.cli manifest sign --out echo_manifest.sig
```

`verify` returns a non-zero status code and prints a unified diff when the file
is out of date. CI calls the same command to guard pull requests.

## Structure

The manifest follows the strict schema in [`attestations/schema.json`](../../attestations/schema.json).
Each component entry contains only the fields allowed by the schema. The top
level includes a `fingerprint` attribute which is the SHA-256 digest over the
canonicalized JSON payload (excluding the fingerprint field itself).

## Signing

Signatures are produced with Ed25519 keys by default, falling back to
HMAC-SHA256 if the provided secret key material is not a valid Ed25519 seed. The
resulting signature file records the algorithm, signature bytes (base64), and
manifest fingerprint. Verification requires either the embedded public key or an
explicit `--pubkey` path.

## Continuous integration

`.github/workflows/echo-manifest.yml` installs the project in editable mode,
executes the pytest suite, and then runs `python -m echo.cli manifest verify`.
Any drift or signature mismatch fails the workflow, blocking merges until the
manifest is refreshed.
