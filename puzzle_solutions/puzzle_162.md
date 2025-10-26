# Puzzle #162 Solution

- **Locking script**: `OP_DUP OP_HASH160 eb33c417c99589fa30e35249567c4c5ca2ff05cf OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `eb33c417c99589fa30e35249567c4c5ca2ff05cf`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 eb 33 c4 17 c9 95 89 fa 30 e3 52 49 56 7c 4c 5c a2 ff 05 cf`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `b2 72 a4 1d`
- **Base58Check encoding**: `1NSdoqxNuyyesvB9DgYKyNiENr4eD2n2ag`

Therefore, the completed Bitcoin address for the given locking script is:

```
1NSdoqxNuyyesvB9DgYKyNiENr4eD2n2ag
```
