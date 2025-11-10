# Puzzle #9996 Solution

- **Provided hash160**: `def7667ca8cd5dc81fa7fcd6471df6782216e134`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 de f7 66 7c a8 cd 5d c8 1f a7 fc d6 47 1d f6 78 22 16 e1 34`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `f3 e5 ec c8`
- **Base58Check encoding**: `1MKwPGGmSDxDajFfC2hPyDkvhFkfFSujLb`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1MKwPGGmSDxDajFfC2hPyDkvhFkfFSujLb
```

> **Note**: The puzzle metadata lists the address `1AVriWNznPPbV7JNFyBgtkaK92E7fQUErB`, but decoding that Base58 string yields a
> different payload and checksum, so it does not correspond to the supplied hash160.
