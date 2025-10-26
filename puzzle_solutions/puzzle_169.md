# Puzzle #169 Solution

- **Locking script**: `OP_DUP OP_HASH160 9f297729adc7e64688273ee4d46ea2005e35a4cd OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `9f297729adc7e64688273ee4d46ea2005e35a4cd`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 9f 29 77 29 ad c7 e6 46 88 27 3e e4 d4 6e a2 00 5e 35 a4 cd`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `1e c8 92 03`
- **Base58Check encoding**: `1HcdCdzG7SbNjiMBNSmCUyK1BFa3un2Rhw`

Therefore, the completed Bitcoin address for the given locking script is:

```
1HcdCdzG7SbNjiMBNSmCUyK1BFa3un2Rhw
```
