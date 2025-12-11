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

Use `verify_extended.py` to confirm each address maps to the provided
public key:
- P2PKH base58 (mainnet/testnet)
- P2WPKH bech32 (version 0)
- Taproot bech32m (version 1, x-only pubkey)

```bash
python3 verifier/verify_extended.py path/to/dataset.csv
```

Input: `dataset.csv` lines `address,hex_pubkey` (blank lines / `#`
comments are ignored)

Output: PASS/FAIL counts and line-level reasons; returns non-zero on
any mismatch.

Works offline; does not derive or handle private keys.

## 3) Reproducibility

Pin Python version in requirements.txt if needed (none required here).

Publish the SHA256 of any dataset: `sha256sum dataset.csv > dataset.sha256`

Anyone can recompute and confirm.

*(If you want the `verify_extended.py` again here, say the word and I’ll drop it in.)*
