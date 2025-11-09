# Puzzle #292 Solution

- **Provided hash160**: `63d0868ad80a1257d1a74188178e43861ce7c2cf`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 63 d0 86 8a d8 0a 12 57 d1 a7 41 88 17 8e 43 86 1c e7 c2 cf`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `71 22 a4 76`
- **Base58Check encoding**: `1A6mhbrGFZffrJXBhTWZbyhE6bXr5ZDBid`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1A6mhbrGFZffrJXBhTWZbyhE6bXr5ZDBid
```

> **Note**: The puzzle metadata lists the address `129mRR7xR9SfuAqTeexxCZZ6TWbfexrv5R`. Decoding that Base58 string corresponds to a different hash160, so it does not match the supplied locking script.
