# Puzzle #175 Solution

- **Locking script**: `OP_DUP OP_HASH160 e9400c677918e303bf46e97b10323d62604c6ff1 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `e9400c677918e303bf46e97b10323d62604c6ff1`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 e9 40 0c 67 79 18 e3 03 bf 46 e9 7b 10 32 3d 62 60 4c 6f f1`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `3e 39 6b cf`
- **Base58Check encoding**: `1NGKArwfwsDGhjauNgSU8MB6szM5stEWri`

Therefore, the completed Bitcoin address for the given locking script is:

```
1NGKArwfwsDGhjauNgSU8MB6szM5stEWri
```
