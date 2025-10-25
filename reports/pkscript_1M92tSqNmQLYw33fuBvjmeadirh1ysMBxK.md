# Puzzle #8 — P2PKH Locking Script Recovery

The eighth wallet in the Bitcoin puzzle series publishes a legacy
pay-to-public-key-hash (P2PKH) script for the address fragment
`1M92tSqNm-rh1ysMBxK`.  The missing centre segment is reconstructed by
turning the HASH160 fingerprint found in `satoshi/puzzle_solutions.json`
into its Base58Check representation.

## Published locking script

```
OP_DUP
OP_HASH160
dce76b2613052ea012204404a97b3c25eac31715
OP_EQUALVERIFY
OP_CHECKSIG
```

The hash payload matches the `hash160_compressed` field recorded for the
Puzzle #8 entry.  Substituting it into the standard P2PKH template yields
the canonical five-opcode script shown above.

## Address derivation walkthrough

```python
import hashlib

alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def base58check(payload: bytes) -> str:
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    num = int.from_bytes(payload + checksum, "big")
    encoded = ""
    while num:
        num, mod = divmod(num, 58)
        encoded = alphabet[mod] + encoded
    # account for the leading 0x00 version byte
    for byte in payload:
        if byte:
            break
        encoded = "1" + encoded
    return encoded

hash160 = bytes.fromhex("dce76b2613052ea012204404a97b3c25eac31715")
address = base58check(b"\x00" + hash160)
print(address)  # 1M92tSqNmQLYw33fuBvjmeadirh1ysMBxK
```

Running the snippet reassembles the full Base58Check address, confirming
that the provided script corresponds to Puzzle #8 and matches the attested
record in `satoshi/puzzle-proofs/puzzle008.json`.
