# Puzzle #181 Solution

- **Locking script**: `OP_DUP OP_HASH160 a6926a69b2eef5b65f46f236e8a22976f1d2783d OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `a6926a69b2eef5b65f46f236e8a22976f1d2783d`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 a6 92 6a 69 b2 ee f5 b6 5f 46 f2 36 e8 a2 29 76 f1 d2 78 3d`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `86 a7 86 20`
- **Base58Check encoding**: `1GBkZz2tPYyRjnYcrZYVD1kdTRC3epgLUo`

Therefore, the completed Bitcoin address for the given locking script is:

```
1GBkZz2tPYyRjnYcrZYVD1kdTRC3epgLUo
```
