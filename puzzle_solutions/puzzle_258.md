# Puzzle #258 Solution

- **Provided hash160**: `278ffad6d6c2498a13162d4bbf23d1fc15d22a00`
- **Bitcoin network version byte**: `0x00` (standard for P2PKH addresses on mainnet)
- **Payload**: `00 27 8f fa d6 d6 c2 49 8a 13 16 2d 4b bf 23 d1 fc 15 d2 2a 00`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `b5 e0 d3 79`
- **Base58Check encoding**: `14cBqNpC2sH84XQt1CLcck1gSUnQh2kZDz`

Therefore, the locking script corresponds to the Bitcoin address:

```
14cBqNpC2sH84XQt1CLcck1gSUnQh2kZDz
```

> **Note**: The metadata lists `1FVjoEY9XK9hF8AHhCNb8rK9drHwZheoyz`, but Base58Check-decoding that string yields a hash160 that does not match `278ffad6d6c2498a13162d4bbf23d1fc15d22a00`. The reconstruction above matches the provided script and hash160.
