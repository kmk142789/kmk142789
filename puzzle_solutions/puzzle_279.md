# Puzzle #279 Solution

- **Provided hash160**: `95088d5e7e550aae6fc6e8655879ff8ffb0da087`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 95 08 8d 5e 7e 55 0a ae 6f c6 e8 65 58 79 ff 8f fb 0d a0 87`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `87 fe 2c 8f`
- **Base58Check encoding**: `1Eb1voVcz3vFP5AWPQX4JWdTGVoRgJ85Li`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1Eb1voVcz3vFP5AWPQX4JWdTGVoRgJ85Li
```

> **Note**: The puzzle metadata lists the address `12E5thw9BhdfDADCBbF4h1X5CkL9PVwTLV`. Decoding that Base58 string corresponds
> to a different hash160, so it does not match the supplied locking script.
