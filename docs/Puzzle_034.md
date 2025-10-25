# Bitcoin Puzzle #34 — Reconstructing the P2PKH Address

Puzzle #34 publishes a standard five-opcode pay-to-public-key-hash (P2PKH) locking script with the middle portion of the advertised Base58Check address obscured by a dash:

```
1PWABE7oU-nCr4rEv7Q
OP_DUP
OP_HASH160
f6d67d7983bf70450f295c9cb828daab265f1bfa
OP_EQUALVERIFY
OP_CHECKSIG
```

Recreating the full address follows the usual Base58Check encoding process for mainnet P2PKH outputs:

1. Prefix the 20-byte HASH160 payload with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte payload and append the first four checksum bytes.
3. Base58Check-encode the resulting 25-byte buffer. Any leading zero bytes in the payload appear as the character `1` in the address.

Carrying out these steps fills in the missing infix from the clue:

- **Address:** `1PWABE7oUahG2AFFQhhvViQovnCr4rEv7Q`
- **Missing infix:** `ahG2AFFQhhvViQov`

The following Python snippet verifies the reconstruction without requiring third-party libraries:

```python
import hashlib

alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def b58encode(data: bytes) -> str:
    value = int.from_bytes(data, "big")
    encoded = ""
    while value:
        value, remainder = divmod(value, 58)
        encoded = alphabet[remainder] + encoded
    prefix = 0
    for byte in data:
        if byte == 0:
            prefix += 1
        else:
            break
    return "1" * prefix + encoded or "1"

hash160 = bytes.fromhex("f6d67d7983bf70450f295c9cb828daab265f1bfa")
payload = b"\x00" + hash160
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
address = b58encode(payload + checksum)
print(address)
```

Running the snippet prints `1PWABE7oUahG2AFFQhhvViQovnCr4rEv7Q`, confirming the completed P2PKH address for Puzzle #34.
