# Puzzle #174 Solution

- **Locking script**: `OP_DUP OP_HASH160 635aac7eb6888d902caa992f63b7c545994cfd02 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `635aac7eb6888d902caa992f63b7c545994cfd02`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 63 5a ac 7e b6 88 8d 90 2c aa 99 2f 63 b7 c5 45 99 4c fd 02`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `c3 f0 30 6d`
- **Base58Check encoding**: `1Po5YoVD4uFkLBfnnX6kbtMAY1CRuUABhs`

Therefore, the completed Bitcoin address for the given locking script is:

```
1Po5YoVD4uFkLBfnnX6kbtMAY1CRuUABhs
```
