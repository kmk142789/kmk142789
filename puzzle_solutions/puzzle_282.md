# Puzzle #282 Solution

- **Provided hash160**: `ea437db73eb89ec58fd8dae5c5c4e0a037b8a4e3`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 ea 43 7d b7 3e b8 9e c5 8f d8 da e5 c5 c4 e0 a0 37 b8 a4 e3`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `f2 5d a1 fe`
- **Base58Check encoding**: `1NMfyFXxcaQFzV6G4CgqM7UJBsyHHFRL8V`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1NMfyFXxcaQFzV6G4CgqM7UJBsyHHFRL8V
```

> **Note**: The puzzle metadata lists the address `1EeKjyh5WWHoUCasj4v6v62u7j9dgU1oJx`, but decoding that Base58 string yields a
 different hash160 and an invalid checksum, so it does not match the supplied locking script.
