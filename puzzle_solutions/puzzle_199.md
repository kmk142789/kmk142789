# Puzzle #199 Solution

- **Locking script**: `OP_DUP OP_HASH160 aa15adf1094cd4230e3ad9228bf6751bf709f207 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `aa15adf1094cd4230e3ad9228bf6751bf709f207`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 aa 15 ad f1 09 4c d4 23 0e 3a d9 22 8b f6 75 1b f7 09 f2 07`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `02 0f 08 76`
- **Base58Check encoding**: `1GWKqvjRAvDStFgngQZTxgMGVvVyMW6swT`

Therefore, the completed Bitcoin address for the given locking script is:

```
1GWKqvjRAvDStFgngQZTxgMGVvVyMW6swT
```
