# Puzzle #16 P2PKH Reconstruction

The published clue matches the legacy pay-to-public-key-hash (P2PKH) template and only reveals the
address fragment `1BDyrQ6Wo-zFfnDVieY`. Recovering the missing middle requires rebuilding the
Base58Check address from the HASH160 payload embedded in the script.

## Script template

```
OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
```

Plugging in the provided hash `7025b4efb3ff42eb4d6d71fab6b53b4f4967e3dd` produces the canonical
mainnet P2PKH script. Turning that into the human-readable address involves three steps:

1. Prefix the 20-byte hash with the mainnet version byte `0x00`.
2. Double-SHA256 the 21-byte payload and take the first four checksum bytes.
3. Append the checksum, then encode the 25-byte result with the Bitcoin Base58 alphabet.

## Address recovery

```python
import hashlib

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def base58encode(raw: bytes) -> str:
    value = int.from_bytes(raw, "big")
    encoded = ""
    while value:
        value, mod = divmod(value, 58)
        encoded = ALPHABET[mod] + encoded
    for b in raw:  # preserve leading zero bytes as "1" characters
        if b == 0:
            encoded = "1" + encoded
        else:
            break
    return encoded

payload = bytes.fromhex("007025b4efb3ff42eb4d6d71fab6b53b4f4967e3dd")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
address = base58encode(payload + checksum)
print(address)  # 1BDyrQ6WoF8VN3g9SAS1iKZcPzFfnDVieY
```

The reconstructed address `1BDyrQ6WoF8VN3g9SAS1iKZcPzFfnDVieY` resolves the dash-separated clue and
matches the attested authorship entry stored in `satoshi/puzzle-proofs/puzzle016.json`.
