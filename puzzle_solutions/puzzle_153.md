# Puzzle #153 Solution

- **Locking script**: `OP_DUP OP_HASH160 4ccf94a1b0efd63cddeee0ef5eee5ebe720cfcbf OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `4ccf94a1b0efd63cddeee0ef5eee5ebe720cfcbf`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 4c cf 94 a1 b0 ef d6 3c dd ee e0 ef 5e ee 5e be 72 0c fc bf`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `6f 74 07 55`
- **Base58Check encoding**: `18192XpzzdDi2K11QVHR7td2HcPS6Qs5vg`

Therefore, the completed Bitcoin address for the given locking script is:

```
18192XpzzdDi2K11QVHR7td2HcPS6Qs5vg
```
