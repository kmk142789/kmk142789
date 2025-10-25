# Bitcoin Puzzle #37 — Restoring the Hidden Infix

Puzzle #37 reprises the legacy five-opcode pay-to-public-key-hash (P2PKH) locking script. The
broadcast clue redacts the middle of the destination address, leaving only the prefix and suffix
visible:

```
14iXhn8bG-ntcpL4dex
OP_DUP
OP_HASH160
28c30fb9118ed1da72e7c4f89c0164756e8a021d
OP_EQUALVERIFY
OP_CHECKSIG
```

Reconstructing the missing infix follows the standard Base58Check workflow for a mainnet P2PKH
output:

1. Prefix the 20-byte HASH160 payload with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte payload and append the first four checksum
   bytes.
3. Base58-encode the resulting 25-byte buffer. Leading zero bytes in the payload appear as the
   character `1` in the final address.

Carrying out those steps restores the removed infix:

- **Address:** `14iXhn8bGajVWegZHJ18vJLHhntcpL4dex`
- **Missing infix:** `ajVWegZHJ18vJLHhn`

A short Python snippet reproduces the calculation:

```python
import hashlib

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def base58encode(raw: bytes) -> str:
    value = int.from_bytes(raw, "big")
    encoded = ""
    while value:
        value, mod = divmod(value, 58)
        encoded = ALPHABET[mod] + encoded
    for byte in raw:  # Preserve leading zero bytes as "1" characters
        if byte == 0:
            encoded = "1" + encoded
        else:
            break
    return encoded

hash160 = "28c30fb9118ed1da72e7c4f89c0164756e8a021d"
payload = bytes.fromhex("00" + hash160)
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
address = base58encode(payload + checksum)
print(address)  # 14iXhn8bGajVWegZHJ18vJLHhntcpL4dex
```

Executing the snippet prints the completed address, confirming the restored P2PKH destination for
Bitcoin Puzzle #37.
