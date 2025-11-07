# Puzzle #220 Solution

- **Provided hash160**: `d100c73a52fd3543245da4649795f57305d59ad8`
- **Bitcoin network version byte**: `0x00` (P2PKH on mainnet)
- **Payload**: `00 d1 00 c7 3a 52 fd 35 43 24 5d a4 64 97 95 f5 73 05 d5 9a d8`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `54ed087b`
- **Base58Check encoding**: `1L47AAagJG4zvuFd3mNwALJki4NrusDHqU`

Therefore, the Bitcoin address that matches the provided locking script is:

```
1L47AAagJG4zvuFd3mNwALJki4NrusDHqU
```
