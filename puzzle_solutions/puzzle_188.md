# Puzzle #188 Solution

- **Locking script**: `OP_DUP OP_HASH160 343675311ef49547bd6abf5255fcb89262759b59 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `343675311ef49547bd6abf5255fcb89262759b59`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 34 36 75 31 1e f4 95 47 bd 6a bf 52 55 fc b8 92 62 75 9b 59`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `2f 84 87 7d`
- **Base58Check encoding**: `15m5NmYyJTAx7TEN4QbRpF9qPBrxqZLUGL`

Therefore, the completed Bitcoin address for the given locking script is:

```
15m5NmYyJTAx7TEN4QbRpF9qPBrxqZLUGL
```
