# Puzzle #149 Solution

- **Locking script**: `OP_DUP OP_HASH160 7e827e3b90da24c2a15f7b67e3bbece39955a5d0 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `7e827e3b90da24c2a15f7b67e3bbece39955a5d0`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 7e 82 7e 3b 90 da 24 c2 a1 5f 7b 67 e3 bb ec e3 99 55 a5 d0`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `39 94 4b ab`
- **Base58Check encoding**: `1CXvTzR6qv8wJ7eprzUKeWxyGcHwDYP1i2`

Therefore, the completed Bitcoin address for the given locking script is:

```
1CXvTzR6qv8wJ7eprzUKeWxyGcHwDYP1i2
```
