# Puzzle #153 Solution

- **Locking script**: `OP_DUP OP_HASH160 b70933f04ce929f8c0ba32f60c0507e379a0fcbc OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `b70933f04ce929f8c0ba32f60c0507e379a0fcbc`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 b7 09 33 f0 4c e9 29 f8 c0 ba 32 f6 0c 05 07 e3 79 a0 fc bc`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `96 b1 46 a2`
- **Base58Check encoding**: `17V4LKycKuXvVoGAgCT9KDqAnRTCK2MwKr`

Therefore, the completed Bitcoin address for the given locking script is:

```
17V4LKycKuXvVoGAgCT9KDqAnRTCK2MwKr
```
