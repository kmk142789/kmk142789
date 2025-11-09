# Puzzle #261 Solution

- **Provided hash160**: `5af4167e1a01aad95dd829806e6ac86ad64915bd`
- **Bitcoin network version byte**: `0x00` (mainnet P2PKH address)
- **Payload**: `00 5a f4 16 7e 1a 01 aa d9 5d d8 29 80 6e 6a c8 6a d6 49 15 bd`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `6d 5c a1 f2`
- **Base58Check encoding**: `19HvDndQuP2BJrCEuvqMLxaErDLdiWTmtu`

Therefore, the completed Bitcoin address for the provided locking script is:

```
19HvDndQuP2BJrCEuvqMLxaErDLdiWTmtu
```

> **Note**: The metadata lists the address `18kfHKYd2sRkRmRCCjJKsxS5vfuCse4TwY`, but decoding that string yields the hash160 `550ab8f774bd1b1c2d61a53aa27fcbb0b5656bd9` with checksum `ecb163cb`. The correct checksum for that payload would be `41d42e41`, so the published address does not match the supplied locking script and is invalid.
