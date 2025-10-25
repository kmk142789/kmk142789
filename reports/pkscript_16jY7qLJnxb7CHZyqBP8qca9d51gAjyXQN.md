# Puzzle #64 — P2PKH Reconstruction

Puzzle #64 in the Bitcoin series advertises the legacy pay-to-public-key-hash
(P2PKH) locking script along with a Base58Check address whose middle section was
replaced by a dash: `16jY7qLJn-51gAjyXQN`.  The HASH160 fingerprint
published with the puzzle lets us restore the missing infix and confirm the
standard script template.

## Published locking script

```
OP_DUP
OP_HASH160
3ee4133d991f52fdf6a25c9834e0745ac74248a4
OP_EQUALVERIFY
OP_CHECKSIG
```

The HASH160 payload matches the `address` entry recorded in the authoritative
attestation for Puzzle #64.  Substituting it into the standard five-opcode
P2PKH template reproduces the advertised script.  Turning the same 20-byte
value back into its Base58Check form restores the missing portion of the
address.

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

hash160 = bytes.fromhex("3ee4133d991f52fdf6a25c9834e0745ac74248a4")
address = base58check(b"\x00" + hash160)
print(address)  # 16jY7qLJnxb7CHZyqBP8qca9d51gAjyXQN
```

Executing the snippet reconstructs the missing substring
(`xb7CHZyqBP8qca9d`) and matches the attested Puzzle #64 record in
`satoshi/puzzle-proofs/puzzle064.json`, confirming the canonical P2PKH output.
