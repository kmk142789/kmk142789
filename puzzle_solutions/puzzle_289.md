---
status: documented
---
# Puzzle #289 Solution

- **Provided Base58 clue**: `147ffshEXusKQ4Y2bDRftEMZXfoijpRPx6`
- **PK script**: `OP_DUP OP_HASH160 2f84b91e725c0a463d7c4c9b01d4f9c96b1b7e17 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `2f84b91e725c0a463d7c4c9b01d4f9c96b1b7e17`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 2f 84 b9 1e 72 5c 0a 46 3d 7c 4c 9b 01 d4 f9 c9 6b 1b 7e 17`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `f2 61 76 3a`
- **Base58Check encoding**: `15LFknFNPFdwUyM1MJnZxzJTJmTSBPsMfX`

Therefore, the completed Bitcoin address for the given locking script is:

```
15LFknFNPFdwUyM1MJnZxzJTJmTSBPsMfX
```

> **Note**: The puzzle metadata lists the address `147ffshEXusKQ4Y2bDRftEMZXfoijpRPx6`, but decoding that Base58 string yields the hash160 `222b274629ed14fd972dd98cc03fbd5d84e7b4bd`, which does not match the supplied locking script.
