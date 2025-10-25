# Puzzle #143 Solution

- **Locking script**: `OP_DUP OP_HASH160 19ed3e03d19ddcedd5fa86543be820b3a7951650 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `19ed3e03d19ddcedd5fa86543be820b3a7951650`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 19 ed 3e 03 d1 9d dc ed d5 fa 86 54 3b e8 20 b3 a7 95 16 50`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `c0 83 69 5d`
- **Base58Check encoding**: `13N66gCzWWHEZBxhVxG18P8wyjEWF9Yoi1`

Therefore, the completed Bitcoin address for the given locking script is:

```
13N66gCzWWHEZBxhVxG18P8wyjEWF9Yoi1
```
