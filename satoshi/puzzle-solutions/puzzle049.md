# Puzzle #49 Solution

- **Given partial address:** `12CiUhYVT-nApAV4WCF`
- **Provided P2PKH script:** `OP_DUP OP_HASH160 0d2f533966c6578e1111978ca698f8add7fffdf3 OP_EQUALVERIFY OP_CHECKSIG`

Base58Check encoding of the HASH160 (with the standard mainnet version byte) restores the full Bitcoin address:

```
12CiUhYVTTH33w3SPUBqcpMoqnApAV4WCF
```

This fills in the missing middle segment `TH33w3SPUBqcpMoq`, confirming the complete destination for Puzzle #49.
