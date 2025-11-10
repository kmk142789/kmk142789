# Puzzle #9995 Solution

- **Provided hash160**: `bff5575fa18fb3a7418d8d31fb2c36ca286e098d`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 bf f5 57 5f a1 8f b3 a7 41 8d 8d 31 fb 2c 36 ca 28 6e 09 8d`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `7d 48 ad 0a`
- **Base58Check encoding**: `1JVyyFdMmyYGbhJgPm13YztLfyg4zwM7yb`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1JVyyFdMmyYGbhJgPm13YztLfyg4zwM7yb
```

> **Note**: The puzzle metadata lists the address `18gmhQJo4Y9i3rd1mNfeTGc9tdvfK9brnp`, but decoding that Base58 string yields a
> different payload and checksum, so it does not correspond to the supplied hash160.
