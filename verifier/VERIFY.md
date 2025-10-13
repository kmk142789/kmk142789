# Echo Verifier Kit

## 1) Attestation (message-only)
```bash
python3 verifier/echo_attest.py --context "Echo attest block #42 | glyph:sheet@abc123 | epoch:quantinuum-2025"
```

Output JSON:

```
{"type":"echo_attestation","ts":1699999999,"signer_id":"echo-attest-bot","context":"...","sha256":"..."}
```

Append JSON to Continuum as a new entry (append-only).

## 2) PubKey/Address Consistency (dataset)

Use your existing repo script or drop in `verify_extended.py` (place under `verifier/`).

Input: `dataset.csv` lines `address,hex_pubkey`

Output: PASS/FAIL counts and sample mismatches

Works offline; does not derive or handle private keys.

## 3) Reproducibility

Pin Python version in requirements.txt if needed (none required here).

Publish the SHA256 of any dataset: `sha256sum dataset.csv > dataset.sha256`

Anyone can recompute and confirm.

*(If you want the `verify_extended.py` again here, say the word and I’ll drop it in.)*
