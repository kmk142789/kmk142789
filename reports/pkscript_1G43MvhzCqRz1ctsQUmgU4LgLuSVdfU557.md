# PKScript Analysis: 1G43MvhzCqRz1ctsQUmgU4LgLuSVdfU557

## Summary
The submitted fragment represents a pay-to-public-key (P2PK) locking script. It publishes a 65-byte uncompressed secp256k1 public key and terminates with `OP_CHECKSIG`, so redeeming the output requires a single signature that validates against that embedded key.

```
04a43f4de451f220ee2606ed79883797000e57a17ad8d418eb2de21339a045fd1e399953a0b9474b2e1fa510696c1eb4812dcd0ea4fda1932344bbd914f52e4e2f OP_CHECKSIG
```

## Details
- **Public key format:** The hexadecimal payload begins with the uncompressed prefix `0x04` and is 130 hex characters long, confirming it encodes a 65-byte secp256k1 key.
- **Derived address:** Hashing the public key with SHA-256 followed by RIPEMD-160, prefixing the Bitcoin mainnet version byte (`0x00`), appending the four-byte double-SHA256 checksum, and Base58Check encoding the result yields the canonical address `1G43MvhzCqRz1ctsQUmgU4LgLuSVdfU557`.
- **Script structure:** Because the locking script embeds the raw public key before `OP_CHECKSIG`, it is a legacy pay-to-public-key output instead of the more common pay-to-public-key-hash (P2PKH). Spending it only requires revealing a DER-encoded signature that matches the published key.
- **Note on supplied label:** The accompanying label `1G43MvhzC-uSVdfU557` includes a hyphen and omits the middle portion of the address. Removing the hyphen and restoring the missing segment recovers the full Base58Check address reported above.

## Reproduction
The derivation can be reproduced with the repository helper:

```
python tools/pkscript_to_address.py <<'EOF'
1G43MvhzC-uSVdfU557
Pkscript
04a43f4de451f220ee2606ed79883797000e57a17ad8d418eb2de21339a045fd1e399953a0b9474b2e1fa510696c1eb4812dcd0ea4fda1932344bbd914f52e4e2f
OP_CHECKSIG
EOF
```

Running this command prints `1G43MvhzCqRz1ctsQUmgU4LgLuSVdfU557`, confirming the interpretation above.
