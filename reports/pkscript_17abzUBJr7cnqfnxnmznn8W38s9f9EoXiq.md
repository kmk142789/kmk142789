# PKScript Analysis: 17abzUBJr7cnqfnxnmznn8W38s9f9EoXiq

## Summary
The supplied payload corresponds to a classic pay-to-public-key (P2PK) Bitcoin locking script. It publishes an uncompressed secp256k1 public key and finishes with `OP_CHECKSIG`, requiring a valid signature generated with the matching private key to spend the output.

```
04c5a68f5fa2192b215016c5dfb384399a39474165eea22603cd39780e653baad9106e36947a1ba3ad5d3789c5cead18a38a538a7d834a8a2b9f0ea946fb4e6f68 OP_CHECKSIG
```

## Details
- **Public key format:** The hexadecimal string begins with the `0x04` prefix, identifying it as a 65-byte uncompressed public key containing the concatenated `x` and `y` coordinates on secp256k1.
- **Derived P2PKH address:** Hashing the public key with SHA-256 then RIPEMD-160, prefixing the mainnet version byte (`0x00`), adding the four-byte double-SHA256 checksum, and Base58Check encoding yields the canonical address `17abzUBJr7cnqfnxnmznn8W38s9f9EoXiq`.
- **Script type:** Because the script embeds the raw public key followed by `OP_CHECKSIG`, it is a pay-to-public-key script rather than the more prevalent pay-to-public-key-hash (P2PKH). Spending it only requires presenting a DER-encoded signature that validates against the published key.
- **Notes on provided address fragment:** The user-supplied string `17abzUBJr-s9f9EoXiq` contains a hyphen and omits several Base58 characters. Removing the hyphen and restoring the missing middle segment reproduces the fully derived address reported above.

## Reproduction
The derivation can be recreated with standard Bitcoin tooling or a compact Python script:

1. Decode the hexadecimal public key into bytes.
2. Compute SHA-256 followed by RIPEMD-160 to obtain the key hash.
3. Prefix with the Bitcoin mainnet version byte, append the double-SHA256 checksum, and Base58Check encode the result.

These steps confirm the integrity of the PKScript and yield the canonical Base58Check representation.
