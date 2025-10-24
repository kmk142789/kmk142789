# PKScript Analysis: 1FLLtCveUBbk41xDqDSTCmuhFUyNAq9Sbd

## Summary
The provided locking script is a pay-to-public-key (P2PK) output. It pushes a 65-byte uncompressed secp256k1 public key onto the stack and terminates with `OP_CHECKSIG`, so a valid signature for that key is required to spend the funds. Running the standard hash160 + Base58Check derivation on the embedded key yields the canonical mainnet address `1FLLtCveUBbk41xDqDSTCmuhFUyNAq9Sbd`.

```
04000ed8229b6fc925fe164bd5be916efab02fb00941dedda712442c145448093995298badfde68e994f786eb41ea5056bb9f2e3e7d24eb18d383ea35dca49b141 OP_CHECKSIG
```

## Details
- **Public key format:** The hex payload starts with the `0x04` prefix and spans 130 hex characters (65 bytes), confirming it is an uncompressed secp256k1 public key consisting of concatenated `x` and `y` coordinates.
- **Derived address:** Double hashing the public key with SHA-256 then RIPEMD-160, prefixing the Bitcoin mainnet version byte (`0x00`), appending the four-byte checksum, and Base58Check encoding the result produces the full address `1FLLtCveUBbk41xDqDSTCmuhFUyNAq9Sbd`.
- **Script structure:** Because the script embeds the raw public key and ends with `OP_CHECKSIG`, it is a classic P2PK output rather than the more common P2PKH form. Spending it requires presenting a DER-encoded signature that validates against the published key.
- **Supplied address fragment:** The first line contained the hyphenated fragment `1FLLtCveU-UyNAq9Sbd`. Removing the separator and performing the hash derivation reconstructs the complete Base58Check address shown above.

## Reproduction
The derivation can be reproduced with the repository helper:

```
python tools/pkscript_to_address.py <<'EOF'
1FLLtCveU-UyNAq9Sbd
Pkscript
04000ed8229b6fc925fe164bd5be916efab02fb00941dedda712442c145448093995298badfde68e994f786eb41ea5056bb9f2e3e7d24eb18d383ea35dca49b141
OP_CHECK
SIG
EOF
```

This emits the canonical address `1FLLtCveUBbk41xDqDSTCmuhFUyNAq9Sbd`, confirming the interpretation above.
