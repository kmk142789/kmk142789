# Puzzle #171 Solution

- **Locking script**: `OP_DUP OP_HASH160 0f69a670aff33b5ff97dfb29bf70d477e3cbb140 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `0f69a670aff33b5ff97dfb29bf70d477e3cbb140`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 0f 69 a6 70 af f3 3b 5f f9 7d fb 29 bf 70 d4 77 e3 cb b1 40`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `c1 a8 21 e4`
- **Base58Check encoding**: `12QVhaawMU5xFizEkdG5XgahDUNUq4HQtj`

Therefore, the completed Bitcoin address for the given locking script is:

```
12QVhaawMU5xFizEkdG5XgahDUNUq4HQtj
```
