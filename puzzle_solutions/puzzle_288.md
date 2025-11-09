---
status: documented
---
# Puzzle #288 Solution

- **Provided Base58 clue**: `1DV8kRCKdtxcDBX1Nu2JMX8fatf4VbvJ73`
- **PK script**: `OP_DUP OP_HASH160 d4ef0a67625184ce6b5b8a6390b3a74e43a1176c OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `d4ef0a67625184ce6b5b8a6390b3a74e43a1176c`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 d4 ef 0a 67 62 51 84 ce 6b 5b 8a 63 90 b3 a7 4e 43 a1 17 6c`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `58 01 4d 0c`
- **Base58Check encoding**: `1LQtcWAiozFSoZ2y82ncp5qqBaU5nV4bsR`

Therefore, the completed Bitcoin address for the given locking script is:

```
1LQtcWAiozFSoZ2y82ncp5qqBaU5nV4bsR
```

> **Note**: The puzzle metadata lists the address `1DV8kRCKdtxcDBX1Nu2JMX8fatf4VbvJ73`, but decoding that Base58 string yields the hash160 `88f39fe05e795881807d1a3cbe300767f722360c`, which does not match the supplied locking script.
