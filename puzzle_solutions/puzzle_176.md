# Puzzle #176 Solution

- **Locking script**: `OP_DUP OP_HASH160 0896c7b1509914e6dfeffa95cb77d7d7e351c366 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `0896c7b1509914e6dfeffa95cb77d7d7e351c366`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 08 96 c7 b1 50 99 14 e6 df ef fa 95 cb 77 d7 d7 e3 51 c3 66`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `15 04 85 90`
- **Base58Check encoding**: `1nR2v8tALBrwipsKs3wDXnRSCRZVVugfR`

Therefore, the completed Bitcoin address for the given locking script is:

```
1nR2v8tALBrwipsKs3wDXnRSCRZVVugfR
```
