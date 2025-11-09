# Puzzle #285 Solution

- **Provided hash160**: `363f915a72aa2246186bb948020aeec9852bc772`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 36 3f 91 5a 72 aa 22 46 18 6b b9 48 02 0a ee c9 85 2b c7 72`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `89 df a5 71`
- **Base58Check encoding**: `15wqe8K6zqMHCvh67x7aS6UXy71GNFgcdt`

Therefore, the completed Bitcoin address for the provided locking script is:

```
15wqe8K6zqMHCvh67x7aS6UXy71GNFgcdt
```

> **Note**: The puzzle metadata lists the address `1GcBWqUiDXJ7TGUEyhAC132c7f2dGAD4zs`, but decoding that Base58 string yields a
> different hash160 and checksum, so it does not match the supplied locking script.
