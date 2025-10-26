# Puzzle #191 Solution

- **Locking script**: `OP_DUP OP_HASH160 cd4c84cd0cc1697c68ab1cd2ffb538a9a1722cb5 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `cd4c84cd0cc1697c68ab1cd2ffb538a9a1722cb5`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 cd 4c 84 cd 0c c1 69 7c 68 ab 1c d2 ff b5 38 a9 a1 72 2c b5`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `ab 5c fb d1`
- **Base58Check encoding**: `1KiXBwc4eEkJdDJRVpn8FuEMvBbabVqcKJ`

Therefore, the completed Bitcoin address for the given locking script is:

```
1KiXBwc4eEkJdDJRVpn8FuEMvBbabVqcKJ
```
