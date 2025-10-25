# Requested WIF Validation (2025-05-11)

This document records validation results for the 59 Wallet Import Format (WIF) private keys supplied on 2025-05-11.  Validation was performed with [`code/wif_validator.py`](../code/wif_validator.py), which implements Base58Check decoding and ensures that each payload has the expected Bitcoin mainnet prefix, checksum, and compression flag.

## Summary

- **Total keys provided:** 59
- **Networks detected:** All 59 keys decode to Bitcoin mainnet (0x80 prefix)
- **Compression flag:** Every key includes the compressed key suffix byte (0x01)
- **Checksum status:** All Base58Check checksums matched

The full machine-readable output is stored alongside this file at [`requested_wifs_report.json`](requested_wifs_report.json).  Each entry contains the normalized private key (hex), inferred network, compression state, and payload length for reproducibility.

## Reproducing the validation

```bash
python code/wif_validator.py --json -f proofs/requested_wifs.txt > proofs/requested_wifs_report.json
```

The input list is saved in [`requested_wifs.txt`](requested_wifs.txt).  Blank lines and comments in that file are ignored by the validator, so additional metadata can be appended as needed without affecting the results.
