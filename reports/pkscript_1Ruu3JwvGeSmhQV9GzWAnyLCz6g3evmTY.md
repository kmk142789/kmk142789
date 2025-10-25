# Puzzle #250 P2PKH Reconstruction

Puzzle #250 again presents the canonical five-opcode pay-to-public-key-hash (P2PKH) locking script.  The clue publishes the Base58Check address with the core section censored — `1Ruu3JwvG-z6g3evmTY` — alongside the HASH160 digest `04b623b48cc42741d0c9ec3b1fa297664bcec49b`.

## Script template

```
OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
```

Filling in the supplied hash yields the standard mainnet P2PKH script.  Recovering the complete address requires re-encoding the digest with Bitcoin's Base58Check algorithm.

1. Prefix the 20-byte hash with the mainnet version byte `0x00` to form the payload.
2. Double-SHA256 the payload and keep the first four checksum bytes.
3. Append the checksum and encode the 25-byte result with the Base58 alphabet.  The process restores the omitted middle substring.

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
    for b in raw:
        if b == 0:
            encoded = "1" + encoded
        else:
            break
    return encoded

payload = bytes.fromhex("0004b623b48cc42741d0c9ec3b1fa297664bcec49b")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
address = base58encode(payload + checksum)
print(address)  # 1Ruu3JwvGeSmhQV9GzWAnyLCz6g3evmTY
```

Running the snippet reconstructs the missing segment (`eSmhQV9GzWAnyLC`) and confirms the expected P2PKH destination for Puzzle #250.
