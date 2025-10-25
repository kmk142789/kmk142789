# Puzzle #103 P2PKH Reconstruction

Puzzle #103 in the Bitcoin puzzle series again presents the canonical five-opcode pay-to-public-key-hash (P2PKH) locking script.
The published clue censors the middle of the broadcast address — `1AcAmB6jm-VPsj9DULf` — while supplying the HASH160 digest
`695fd6dcf33f47166b25de968b2932b351b0afc4` for the corresponding public key.

## Script template

```
OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
```

Substituting the provided digest yields the standard mainnet P2PKH assembly.  Recovering the full address simply requires
re-encoding the hash with Bitcoin's Base58Check format.

1. Prefix the HASH160 with the mainnet version byte `0x00`.
2. Double-SHA256 the 21-byte payload and keep the first four checksum bytes.
3. Append the checksum, then encode the 25-byte result with the Base58 alphabet, restoring the missing characters.

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
    for b in raw:
        if b == 0:
            encoded = "1" + encoded
        else:
            break
    return encoded

payload = bytes.fromhex("00695fd6dcf33f47166b25de968b2932b351b0afc4")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
address = base58encode(payload + checksum)
print(address)  # 1AcAmB6jmtU6AiEcXkmiNE9TNVPsj9DULf
```

Executing the snippet restores the omitted infix (`tU6AiEcXkmiNE9TN`) and matches the canonical dataset entry recorded in
`satoshi/puzzle_solutions.json`, confirming the standard P2PKH output for Puzzle #103.
