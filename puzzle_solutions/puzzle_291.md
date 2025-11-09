# Puzzle #291 Solution

- **Provided hash160**: `eed2c3f48d42e585d44a9a41e486c60ac478e08b`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 ee d2 c3 f4 8d 42 e5 85 d4 4a 9a 41 e4 86 c6 0a c4 78 e0 8b`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `74 58 12 56`
- **Base58Check encoding**: `1NmnJtxfk3FXtg4fyiKaNQGoZmbQ3pCqkq`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1NmnJtxfk3FXtg4fyiKaNQGoZmbQ3pCqkq
```

> **Note**: The puzzle metadata lists the address `13GasGrjMSzHzc5HzThSE6MpGzbCDpxqhZ`. Decoding that Base58 string corresponds
to a different hash160, so it does not match the supplied locking script.
