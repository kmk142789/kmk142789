# Pay-to-Public-Key-Hash Script for 18cBEMRxXHqzWWCxZNtU91F5sbUNKhL5PX

This note documents the disassembly of the provided locking script (scriptPubKey) and ties it back to the familiar Pay-to-Public-Key-Hash (P2PKH) template used on Bitcoin mainnet.

```
OP_DUP
OP_HASH160
536ffa992491508dca0354e52f32a3a7a679a53a
OP_EQUALVERIFY
OP_CHECKSIG
```

## Interpretation

1. `OP_DUP` duplicates the top stack item (the spender's public key) so it can be used both for hashing and later signature verification.
2. `OP_HASH160` performs SHA-256 followed by RIPEMD-160 on the duplicated public key, producing a 20-byte hash.
3. `536ffa992491508dca0354e52f32a3a7a679a53a` is the hash160 value that must match the hashed public key provided by the spender.
4. `OP_EQUALVERIFY` checks that the supplied public key hash matches the constant pushed in step 3 and fails the script if not.
5. `OP_CHECKSIG` validates the provided signature against the public key and transaction data.

Because this follows the standard P2PKH pattern, the corresponding Base58Check-encoded address is **18cBEMRxXHqzWWCxZNtU91F5sbUNKhL5PX**.

## Notes

- The Base58Check address is derived by prefixing the hash160 with the mainnet version byte `0x00`, computing a double-SHA-256 checksum, and encoding the result.
- Any transaction attempting to spend the output locked by this script must present a public key whose hash160 is `536ffa992491508dca0354e52f32a3a7a679a53a` along with a valid ECDSA signature over the spending transaction.
