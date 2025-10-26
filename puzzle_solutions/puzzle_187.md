# Puzzle #187 Solution

- **Locking script**: `OP_DUP OP_HASH160 484a3b85778637341c8632b27929cb20cb201e7b OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `484a3b85778637341c8632b27929cb20cb201e7b`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 48 4a 3b 85 77 86 37 34 1c 86 32 b2 79 29 cb 20 cb 20 1e 7b`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `ae 7a d5 4e`
- **Base58Check encoding**: `17bEaaSx8E6Z1ZGZnWBMpX415RcMNX9Sgu`

Therefore, the completed Bitcoin address for the given locking script is:

```
17bEaaSx8E6Z1ZGZnWBMpX415RcMNX9Sgu
```
