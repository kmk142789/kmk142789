# Puzzle #49 P2PKH Reconstruction

Puzzle #49 publishes the familiar five-opcode pay-to-public-key-hash (P2PKH) locking script with a censored middle segment in the advertised address:

- Partial address: `12CiUhYVT-nApAV4WCF`
- HASH160 digest: `0d2f533966c6578e1111978ca698f8add7fffdf3`

The script matches the canonical P2PKH template:

```
OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
```

Encoding the 20-byte hash with the mainnet version byte (`0x00`) and Base58Check restores the missing characters. The reconstruction steps follow the usual approach:

1. Prefix the HASH160 value with the version byte to form the 21-byte payload.
2. Double-SHA256 hash the payload and keep the first four bytes as the checksum.
3. Append the checksum, then Base58 encode the 25-byte sequence, preserving any leading zero bytes as `1` characters in the output.

## Address recovery

```python
import hashlib

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def base58check_encode(payload: bytes) -> str:
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    value = int.from_bytes(payload + checksum, "big")
    encoded = ""
    while value:
        value, mod = divmod(value, 58)
        encoded = ALPHABET[mod] + encoded
    for byte in payload + checksum:
        if byte == 0:
            encoded = "1" + encoded
        else:
            break
    return encoded

payload = bytes.fromhex("00" + "0d2f533966c6578e1111978ca698f8add7fffdf3")
print(base58check_encode(payload))
# 12CiUhYVTTH33w3SPUBqcpMoqnApAV4WCF
```

Running the snippet recovers the omitted substring (`TH33w3SPUBqcpMoq`) and matches the attested Puzzle #49 entry cataloged in `satoshi/puzzle-proofs/puzzle049.json`.
