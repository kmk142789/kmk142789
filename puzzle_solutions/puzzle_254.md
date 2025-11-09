# Puzzle #254 Solution

- **Provided hash160**: `e857d7981f916ebb3d419e94e82c89e913a2d1ea`
- **Bitcoin network version byte**: `0x00` (P2PKH on mainnet)
- **Payload**: `00 e8 57 d7 98 1f 91 6e bb 3d 41 9e 94 e8 2c 89 e9 13 a2 d1 ea`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `5e c4 d5 e1`
- **Base58Check encoding**: `1NBWztM5WSGP6ZJ67NaxmmpFaAjgDdYZzY`

Therefore, the locking script corresponds to the Bitcoin address:

```
1NBWztM5WSGP6ZJ67NaxmmpFaAjgDdYZzY
```

> **Note**: Decoding the metadata address `17ahceMLD5aQApAsvWwfw657KSTLW3NhUd` yields the hash160 `4830627fbf4d9ccb72c9b533fc91a87d39778e0b`, which does not match the provided script. The Base58Check reconstruction above matches the supplied hash160.
