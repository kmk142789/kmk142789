# Puzzle #172 Solution

- **Locking script**: `OP_DUP OP_HASH160 12a3917216177c6e5fab452d77057a9e0f62e5c3 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `12a3917216177c6e5fab452d77057a9e0f62e5c3`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 12 a3 91 72 16 17 7c 6e 5f ab 45 2d 77 05 7a 9e 0f 62 e5 c3`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `e8 a9 09 cf`
- **Base58Check encoding**: `12hZ7NHk83CiT3MPJGVuT3HKhKotx7Hbgr`

Therefore, the completed Bitcoin address for the given locking script is:

```
12hZ7NHk83CiT3MPJGVuT3HKhKotx7Hbgr
```
