# Puzzle #70 P2PKH Reconstruction

Puzzle #70 publishes the familiar five-opcode pay-to-public-key-hash (P2PKH) locking
script alongside an address where the center segment is redacted: `19YZECXj3-xANe7M7QR`.
The accompanying HASH160 digest `5db8cda53a6a002db10365967d7f85d19e171b10` is enough to
restore the full Base58Check destination.

## Script template

```
OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
```

Substituting the provided hash yields the canonical mainnet P2PKH assembly.  Recovering the
complete address only requires encoding the 20-byte hash with Bitcoin's Base58Check
procedure:

1. Prefix the hash with the mainnet version byte `0x00` to build the 21-byte payload.
2. Double-SHA256 the payload and keep the first four checksum bytes.
3. Append the checksum and encode the 25-byte sequence with Bitcoin's Base58 alphabet,
   remembering that each leading zero byte maps to the character `1`.

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
    # restore any leading zero bytes (represented as "1" in Base58)
    for b in raw:
        if b == 0:
            encoded = "1" + encoded
        else:
            break
    return encoded

payload = bytes.fromhex("005db8cda53a6a002db10365967d7f85d19e171b10")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
address = base58encode(payload + checksum)
print(address)  # 19YZECXj3SxEZMoUeJ1yiPsw8xANe7M7QR
```

The reconstructed Base58Check string `19YZECXj3SxEZMoUeJ1yiPsw8xANe7M7QR` fills in the
missing substring (`SxEZMoUeJ1yiPsw8`) and matches the attested Puzzle #70 entry stored
in `satoshi/puzzle-proofs/puzzle070.json`, confirming the standard P2PKH script for this
puzzle address.
