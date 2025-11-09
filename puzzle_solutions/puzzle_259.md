# Puzzle #259 Solution

- **Provided hash160**: `de0b412359d46c2cb6a4f44b0aa9e3e84f813929`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 de 0b 41 23 59 d4 6c 2c b6 a4 f4 4b 0a a9 e3 e8 4f 81 39 29`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `c8 80 96 cd`
- **Base58Check encoding**: `1MF4VZRJCW7vgBfaziKokC36dB63tbUyCx`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1MF4VZRJCW7vgBfaziKokC36dB63tbUyCx
```

> **Note**: The metadata lists the address `14FobiEAQSGPkA9aMskMnDB2BjCnsfUcht`, but decoding that Base58 string yields the hash160 `23b51968b169574bc5b02fde5ab56a2bbefccfb9` and has an invalid checksum, so it does not correspond to the supplied locking script.
