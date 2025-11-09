# Puzzle #270 Solution

- **Provided hash160**: `6cf727926c3546de6ca88580b3430b6a9ab0c7df`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 6c f7 27 92 6c 35 46 de 6c a8 85 80 b3 43 0b 6a 9a b0 c7 df`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `eb ea b3 1f`
- **Base58Check encoding**: `1AwA4KVWWXm8JyYa69Fv2xHz1UADkdhjLA`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1AwA4KVWWXm8JyYa69Fv2xHz1UADkdhjLA
```

> **Note**: The puzzle metadata lists the address `194dsW1UW8M8r9ewqZdbgJ9MJi1US9ENQd`. Decoding that Base58 string corresponds to a different hash160, so it does not match the supplied locking script.
