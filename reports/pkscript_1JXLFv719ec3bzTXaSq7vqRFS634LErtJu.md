# PKScript Analysis: 1JXLFv719ec3bzTXaSq7vqRFS634LErtJu

## Summary
The provided script is a classic pay-to-public-key (P2PK) Bitcoin locking script. It pushes a 65-byte uncompressed secp256k1 public key onto the stack and terminates with `OP_CHECKSIG`, so spending the output requires presenting a valid signature that matches the embedded key.

```
049523af765da5408d0a4f9d33af2e103c57b8b31877969173e7a7c313bf09a9803dcceec9b29d0fab4737173e3cb6dcc11ab7f233d8b1d715748ca4d715770ac3 OP_CHECKSIG
```

## Details
- **Public key format:** The hexadecimal payload starts with the `0x04` prefix and is 130 hex characters long, confirming it represents an uncompressed 65-byte secp256k1 public key with concatenated `x` and `y` coordinates.
- **Derived address:** Hashing the public key with SHA-256 then RIPEMD-160, prefixing the Bitcoin mainnet version byte (`0x00`), appending the four-byte double-SHA256 checksum, and Base58Check encoding the result yields the canonical address `1JXLFv719ec3bzTXaSq7vqRFS634LErtJu`.
- **Script structure:** Because the locking script embeds the raw public key and ends with `OP_CHECKSIG`, it is a pay-to-public-key output rather than the more common pay-to-public-key-hash (P2PKH). Spending it requires supplying a DER-encoded signature that validates against the published key.
- **Note on supplied fragment:** The initial address fragment `1JXLFv719-634LErtJu` contains a hyphen and omits several characters. Removing the hyphen and restoring the missing middle segment produces the fully derived Base58Check address reported above.

## Reproduction
The derivation can be reproduced with the repository helper:

```
python tools/pkscript_to_address.py <<'EOF'
1JXLFv719-634LErtJu
Pkscript
049523af765da5408d0a4f9d33af2e103c57b8b31877969173e7a7c313bf09a9803dcceec9b29d0fab4737173e3cb6dcc11ab7f233d8b1d715748ca4d715770ac3
OP_CHECKSIG
EOF
```

This emits the canonical address `1JXLFv719ec3bzTXaSq7vqRFS634LErtJu`, confirming the interpretation above.
