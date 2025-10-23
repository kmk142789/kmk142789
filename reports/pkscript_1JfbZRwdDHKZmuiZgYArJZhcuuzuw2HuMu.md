# Analysis of Provided Bitcoin Script Data

## Summary
- **Address:** `1JfbZRwdDHKZmuiZgYArJZhcuuzuw2HuMu`
- **Script type:** Pay-to-PubKey (P2PK)
- **Public key length:** 65 bytes (uncompressed, prefix `0x04`)
- **Unlocking requirement:** A valid ECDSA signature over the spending transaction, verified against the embedded public key.

## Script Reconstruction
The supplied public key hex string

```
0456579536d150fbce94ee62b47db2ca43af0a730a0467ba55c79e2a7ec9ce4ad297e35cdbb8e42a4643a60eef7c9abee2f5822f86b1da242d9c2301c431facfd8
```

expands into the classic **P2PK** `scriptPubKey`:

```
41 0456579536d150fbce94ee62b47db2ca43af0a730a0467ba55c79e2a7ec9ce4ad297e35cdbb8e42a4643a60eef7c9abee2f5822f86b1da242d9c2301c431facfd8 ac
│ └───────────────────────────────────────────────────────────────────────────────┘ │
│                          push 65-byte uncompressed public key                     │
└─ OP_DATA_65                                                               OP_CHECKSIG
```

This script sends funds directly to the listed public key; there is no HASH160 step as in P2PKH outputs.

## Address Derivation (for reference)
Although P2PK outputs are keyed to the raw public key, hashing that key with `SHA256` followed by `RIPEMD160`, then encoding with Base58Check (version byte `0x00`) reproduces the familiar legacy address:

```
Hash160(pubkey) = 0x84c1a0b4c0f9f960080fadd63cfb03244521fe03
Base58Check(0x00 || hash160) = 1JfbZRwdDHKZmuiZgYArJZhcuuzuw2HuMu
```

## Spending Conditions
To spend this output the scriptSig must provide:

1. A DER-encoded ECDSA signature covering the spending transaction (and appended sighash flag).
2. When executed, the signature is checked against the embedded public key by `OP_CHECKSIG`. If verification succeeds, the output is unlocked.

Because the locking script already contains the public key, no additional data (such as a public key hash) is required in the scriptSig—only the signature itself.
