# Puzzle #80 P2PKH Reconstruction

The provided puzzle exposes the classic pay-to-public-key-hash (P2PKH) locking script for the
address fragment `1BCf6rHUW-AiPQQepLe`. Filling in the missing middle section only requires
recomputing the legacy Base58Check address from the published hash160 value.

## Script template

```
OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
```

Substituting the supplied hash `6fe5a36eef0684af0b91f3b6cfc972d68c4f6fab` yields a standard
mainnet P2PKH script. The Base58Check conversion step is:

1. Prefix the 20-byte hash with the mainnet version byte `0x00`.
2. Double-SHA256 the result and take the first four checksum bytes.
3. Append the checksum and encode the full 25-byte payload with the Base58 alphabet.

## Address recovery

```python
import hashlib

alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def base58encode(raw: bytes) -> str:
    value = int.from_bytes(raw, "big")
    encoded = ""
    while value:
        value, mod = divmod(value, 58)
        encoded = alphabet[mod] + encoded
    # account for leading zero bytes (Base58 uses "1" for 0x00)
    for b in raw:
        if b == 0:
            encoded = "1" + encoded
        else:
            break
    return encoded

payload = bytes.fromhex("006fe5a36eef0684af0b91f3b6cfc972d68c4f6fab")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
address = base58encode(payload + checksum)
print(address)  # 1BCf6rHUW6m3iH2ptsvnjgLruAiPQQepLe
```

The reconstructed string `1BCf6rHUW6m3iH2ptsvnjgLruAiPQQepLe` resolves the dash-separated clue and
matches the attested authorship entry for Puzzle #80 in `satoshi/puzzle-proofs/puzzle080.json`.
