# Puzzle #10001 Solution

- **Provided hash160**: `aabbccddeeff00112233445566778899aabbccdd`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 aa bb cc dd ee ff 00 11 22 33 44 55 66 77 88 99 aa bb cc dd`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `fa 1d 5e 93`
- **Base58Check encoding**: `1GZkrCiqooNgoRNKCnh7HySMdTwp1sm7zJ`

Therefore, the completed Bitcoin address for the given locking script is:

```
1GZkrCiqooNgoRNKCnh7HySMdTwp1sm7zJ
```
