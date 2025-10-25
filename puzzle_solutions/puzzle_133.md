# Puzzle #133 Solution

- **Locking script**: `OP_DUP OP_HASH160 df4b044ec1d861be8f0f27e19e4070544b1fc1eb OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `df4b044ec1d861be8f0f27e19e4070544b1fc1eb`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 df 4b 04 4e c1 d8 61 be 8f 0f 27 e1 9e 40 70 54 4b 1f c1 eb`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `bd 6a c2 62`
- **Base58Check encoding**: `1MMfZ3F8RVtc3X73ARQ8ARQnpJPZS6C2Rf`

Therefore, the completed Bitcoin address for the given locking script is:

```
1MMfZ3F8RVtc3X73ARQ8ARQnpJPZS6C2Rf
```
