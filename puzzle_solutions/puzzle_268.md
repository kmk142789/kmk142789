# Puzzle #268 Solution

- **Provided hash160**: `2e060aa604b06608f67943bbd18871406860ce06`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 2e 06 0a a6 04 b0 66 08 f6 79 43 bb d1 88 71 40 68 60 ce 06`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `21 7f 58 a1`
- **Base58Check encoding**: `15CMKbttK5Er22zcTFqXkpJfoWT6R8rjFv`

Therefore, the completed Bitcoin address for the provided locking script is:

```
15CMKbttK5Er22zcTFqXkpJfoWT6R8rjFv
```

> **Note**: The puzzle metadata lists the address `14KNiHJ9x95Bk5BtiejTxvJVnrm4ADrNq3`. Decoding that Base58 string corresponds to a different hash160, so it does not match the supplied locking script.
