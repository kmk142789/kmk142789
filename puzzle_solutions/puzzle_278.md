# Puzzle #278 Solution

- **Provided hash160**: `358f3b93a0d7bab6f366bd55fc3a4ba489d8377b`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 35 8f 3b 93 a0 d7 ba b6 f3 66 bd 55 fc 3a 4b a4 89 d8 37 7b`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `6e fa 30 79`
- **Base58Check encoding**: `15tCQ9kqpY8L4mWxGF4646zUVutKgmLxoz`

Therefore, the completed Bitcoin address for the provided locking script is:

```
15tCQ9kqpY8L4mWxGF4646zUVutKgmLxoz
```

> **Note**: The puzzle metadata lists the address `1ALApMBXPYRKvSCBUpEsJpE2HwaX6DrYEC`, but encoding the supplied hash160 yields the Base58Check address shown above.
