# PKScript Analysis: 1PYELM7jX Hy5HhatbXGXfRpGrgMMxmpobu

## Summary
The provided data corresponds to a classical pay-to-public-key (P2PK) Bitcoin locking script. The script publishes an uncompressed public key and concludes with `OP_CHECKSIG`, requiring a matching signature created with the corresponding private key.

```
0478ebe2c28660cd2fa1ba17cc04e58d6312679005a7cad1fd56a7b7f4630bd700bcdb84a888a43fe1a2738ea1f3d2301d02faef357e8a5c35a706e4ae0352a6ad OP_CHECKSIG
```

## Details
- **Public key format:** The hexadecimal string begins with the `0x04` prefix, signalling an uncompressed 65-byte secp256k1 public key (`x` and `y` coordinates concatenated).
- **Derived P2PKH address:** Hashing this public key with SHA-256 followed by RIPEMD-160, prefixing the mainnet version byte (`0x00`), and appending a four-byte checksum produces the Base58Check address `1PYELM7jXHy5HhatbXGXfRpGrgMMxmpobu`.
- **Script type:** Because the script directly embeds the public key and ends with `OP_CHECKSIG`, it is a pay-to-public-key script rather than the more common pay-to-public-key-hash (P2PKH). Spending from this script requires providing a DER-encoded signature that validates against the listed public key.
- **Notes on supplied address string:** The user-supplied string `1PYELM7jX-gMMxmpobu` contains a hyphen and is shorter than a valid Base58Check encoding. The fully derived address above clarifies the intended recipient identifier without the hyphen.

## Reproduction
The address derivation steps can be repeated with any Bitcoin tooling capable of Base58Check encoding. A minimal Python implementation would:

1. Decode the hexadecimal public key to bytes.
2. Compute `SHA256` then `RIPEMD160` of the key bytes to produce the key-hash.
3. Prefix `0x00` (Bitcoin mainnet), append the four-byte double-SHA256 checksum, and Base58 encode the result.

This workflow confirms the integrity of the provided PKScript and yields the canonical Base58Check address.
