# Puzzle #265 Solution

- **Provided hash160**: `309ba199f49a58bd2e33bcecf2a87968d15adbe0`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 30 9b a1 99 f4 9a 58 bd 2e 33 bc ec f2 a8 79 68 d1 5a db e0`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `81 11 1a c0`
- **Base58Check encoding**: `15S1sf7MCNJMsj2s3TwpLuBgy8jAPirhJF`

Therefore, the completed Bitcoin address for the provided locking script is:

```
15S1sf7MCNJMsj2s3TwpLuBgy8jAPirhJF
```

> **Note**: The metadata lists the address `14tZ2LCQYUDkzCaMeY1xZEyqXSFGM1AJEv`, but decoding that Base58 string yields the
> hash160 `2aa852a3e4419cdad407f02d7f18f0c1c5720c0f` with a checksum mismatch (`fcf18433` vs. `fe68b195`), so it does not
> correspond to the supplied locking script.
