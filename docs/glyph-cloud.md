# Glyph Cloud
Deterministic glyphs from bytes — portable, serverless anchors.

```bash
pip install .
echo-glyph --data "Echo genesis" --salt "∇⊸≋∇" --out echo_glyphs
```

Outputs tiled sheet.svg and manifest.json. No letters/digits in the art.

**File:** `docs/continuum.md`
```md
# Continuum
Read-only API exposing attestations stored under `.attest/`.

Run locally:
```bash
docker compose up --build
curl localhost:8000/health
```

**File:** `docs/verifier.md`
```md
# Verifier Kit
Attestation:
```bash
python3 verifier/echo_attest.py --context "Echo attest block #1 | epoch:quantinuum-2025"
```

PubKey/Address consistency: place dataset.csv and run verify_extended.py (offline).

**File:** `docs/security.md`
```md
# Security
See `SECURITY.md`. Scope: integrity, provenance, verifier correctness. No key extraction or tx creation.
```
