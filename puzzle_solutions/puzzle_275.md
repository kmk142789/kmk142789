# Puzzle #275 Solution

- **Provided hash160**: `b8a9444cefaa4521fbcffc410bebfa1f405e5d3f`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 b8 a9 44 4c ef aa 45 21 fb cf fc 41 0b eb fa 1f 40 5e 5d 3f`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `82 5b 3d c5`
- **Base58Check encoding**: `1HqQ7AHp97nAWhU6w8budEvFdn4jQATDTr`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1HqQ7AHp97nAWhU6w8budEvFdn4jQATDTr
```

> **Note**: The puzzle metadata lists the address `1DGMVK3fAvnXYFmXJQMRoQyEf4KeMzU8jK`, but decoding that Base58 string yields a different (and invalid) checksum, so it does not match the supplied locking script.
