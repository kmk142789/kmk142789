# Puzzle #213 Solution

- **Provided hash160**: `7cb4648719aedaf874354cadf986e89458eb58cc`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 7c b4 64 87 19 ae da f8 74 35 4c ad f9 86 e8 94 58 eb 58 cc`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `b8 f5 ee b1`
- **Base58Check encoding**: `1CNNth43uiVypxHmZLC8hWZsb7UiP7wSkY`
- **Blockchain funding**: Blockstream explorer reports `21,300,000` sats (0.213 BTC) funded and spent from this address, matching the puzzle denomination.

Therefore, the completed Bitcoin address for the given locking script is:

```
1CNNth43uiVypxHmZLC8hWZsb7UiP7wSkY
```
