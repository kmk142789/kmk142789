# Puzzle #146 Solution

- **Locking script**: `OP_DUP OP_HASH160 dca7ebfb78ce21884300f133d89244bc4b1b756f OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `dca7ebfb78ce21884300f133d89244bc4b1b756f`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 dc a7 eb fb 78 ce 21 88 43 00 f1 33 d8 92 44 bc 4b 1b 75 6f`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `8a 33 b1 92`
- **Base58Check encoding**: `1M7ipcdYHey2Y5RZM34MBbpugghmjaV89P`

Therefore, the completed Bitcoin address for the given locking script is:

```
1M7ipcdYHey2Y5RZM34MBbpugghmjaV89P
```
