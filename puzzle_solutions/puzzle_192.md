# Puzzle #192 Solution

- **Locking script**: `OP_DUP OP_HASH160 cecbf2330a8f059d1f652e651331cfb2a0c2adb6 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `cecbf2330a8f059d1f652e651331cfb2a0c2adb6`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 ce cb f2 33 0a 8f 05 9d 1f 65 2e 65 13 31 cf b2 a0 c2 ad b6`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `79 60 08 d1`
- **Base58Check encoding**: `1EQusAkuZz9R75xpGyALxtmV9soEWDP4xz`

Therefore, the completed Bitcoin address for the given locking script is:

```
1EQusAkuZz9R75xpGyALxtmV9soEWDP4xz
```
