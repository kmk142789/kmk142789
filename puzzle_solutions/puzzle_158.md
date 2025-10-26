# Puzzle #158 Solution

- **Locking script**: `OP_DUP OP_HASH160 628dacebb0faa7f81670e174ca4c8a95a7e37029 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `628dacebb0faa7f81670e174ca4c8a95a7e37029`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 62 8d ac eb b0 fa a7 f8 16 70 e1 74 ca 4c 8a 95 a7 e3 70 29`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `0c 5e 85 b3`
- **Base58Check encoding**: `19z6waranEf8CcP8FqNgdwUe1QRxvUNKBG`

Therefore, the completed Bitcoin address for the given locking script is:

```
19z6waranEf8CcP8FqNgdwUe1QRxvUNKBG
```
