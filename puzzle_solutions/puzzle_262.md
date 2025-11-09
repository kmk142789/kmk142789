# Puzzle #262 Solution

- **Provided hash160**: `402806cb3bb0cde0a33c72714e3fe015c97ab1d9`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 40 28 06 cb 3b b0 cd e0 a3 3c 72 71 4e 3f e0 15 c9 7a b1 d9`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `2c 1d 2a 49`
- **Base58Check encoding**: `16rECNT2DALVNjBHrryoHAy7CRiEKpEu9r`

Therefore, the completed Bitcoin address for the provided locking script is:

```
16rECNT2DALVNjBHrryoHAy7CRiEKpEu9r
```

> **Note**: The metadata lists the address `15d4GZKNWci13YhaJKWw66pCjNVv42bXku`, but decoding that Base58 string yields the hash160 `32b234b85f7fdc2a855d835283f3f6fbeeae4b42` with a checksum mismatch (`0e26b9aa` vs. `4c87ca21`), so it does not correspond to the supplied locking script.
