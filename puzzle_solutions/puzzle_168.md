# Puzzle #168 Solution

- **Locking script**: `OP_DUP OP_HASH160 f1af490147e2af33d2428f85e76850ba31f6c258 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `f1af490147e2af33d2428f85e76850ba31f6c258`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 f1 af 49 01 47 e2 af 33 d2 42 8f 85 e7 68 50 ba 31 f6 c2 58`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `b9 54 0a 78`
- **Base58Check encoding**: `1DMG8sCPuZiA5oh2WgHtiJ65Gm1gkqUofZ`

Therefore, the completed Bitcoin address for the given locking script is:

```
1DMG8sCPuZiA5oh2WgHtiJ65Gm1gkqUofZ
```
