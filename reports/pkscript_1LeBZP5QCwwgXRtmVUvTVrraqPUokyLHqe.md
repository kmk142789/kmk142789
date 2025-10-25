# Puzzle #10 P2PKH Reconstruction

Puzzle #10 publishes a legacy pay-to-public-key-hash (P2PKH) locking script alongside an address with a missing section:

- Partial address: `1LeBZP5QC-PUokyLHqe`
- HASH160 digest: `d7729816650e581d7462d52ad6f732da0e2ec93b`

The script template matches the standard five-opcode pattern:

```
OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
```

Encoding the provided hash with the mainnet version byte (`0x00`) and Base58Check completes the address.  The steps are identical
 to other P2PKH reconstructions:

1. Prefix the 20-byte HASH160 value with the version byte to form the payload.
2. Derive the four-byte checksum by double-SHA256 hashing the payload.
3. Append the checksum and encode the 25-byte result with the Base58 alphabet, preserving any leading zeros as `1` characters.

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

payload = bytes.fromhex("00d7729816650e581d7462d52ad6f732da0e2ec93b")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
address = base58encode(payload + checksum)
print(address)  # 1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe
```

Running the snippet restores the missing middle section (`wwgXRtmVUvTVrraqP`) and matches the attested entry for Puzzle #10 in
`satoshi/puzzle_solutions.json`, confirming the canonical P2PKH output.
