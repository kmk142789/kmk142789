# Puzzle #250 Solution

- **Provided hash160**: `c8091f2091e3be1bdfef86248ba3bdda0eba4b24`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 c8 09 1f 20 91 e3 be 1b df ef 86 24 8b a3 bd da 0e ba 4b 24`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `65 ed 68 84`
- **Base58Check encoding**: `1KEh59RrPavuLFbHvE1JAk6n8PXuYSDQGK`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1KEh59RrPavuLFbHvE1JAk6n8PXuYSDQGK
```

> **Note**: The supplied metadata address `1GTGue5H59bsZrtQxqCr7ELRG3NA2tJ263` decodes to the hash160 `a981fb1182d43e860820d02b83f737fa61405d46`, which does not match the locking script. The Base58Check reconstruction above corresponds to the provided hash160 and script.
