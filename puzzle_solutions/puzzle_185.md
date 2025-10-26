# Puzzle #185 Solution

- **Locking script**: `OP_DUP OP_HASH160 2f1b0096855b38398807bc8ac92180567729c3d4 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `2f1b0096855b38398807bc8ac92180567729c3d4`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 2f 1b 00 96 85 5b 38 39 88 07 bc 8a c9 21 80 56 77 29 c3 d4`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `71 0e 5b 58`
- **Base58Check encoding**: `15J57AmqRVLavVZx9Fif2BQajudHUSkEs9`

Therefore, the completed Bitcoin address for the given locking script is:

```
15J57AmqRVLavVZx9Fif2BQajudHUSkEs9
```
