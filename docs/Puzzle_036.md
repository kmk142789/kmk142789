# Bitcoin Puzzle #36 — P2PKH Reconstruction

Puzzle #36 advertises the canonical five-opcode pay-to-public-key-hash (P2PKH) locking script alongside the payout address with its middle segment removed:

```
1Be2UF9NL-9N1Kduci1
OP_DUP
OP_HASH160
74b1e012be1521e5d8d75e745a26ced845ea3d37
OP_EQUALVERIFY
OP_CHECKSIG
```

Reconstructing the address follows the standard Base58Check procedure for a mainnet P2PKH output:

1. Prefix the 20-byte HASH160 payload with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the resulting 21-byte payload and append the first four checksum bytes.
3. Base58Check-encode the 25-byte buffer. Any leading zero bytes in the payload become the character `1` in the final string.

Applying the workflow restores the hidden infix from the published clue:

- **Address:** `1Be2UF9NLfyLFbtm3TCbmuocc9N1Kduci1`
- **Missing infix:** `fyLFbtm3TCbmuocc`

The short Python snippet below re-encodes the HASH160 into the P2PKH address and verifies the reconstruction:

```python
import hashlib

alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
hash160 = "74b1e012be1521e5d8d75e745a26ced845ea3d37"
payload = bytes.fromhex("00" + hash160)
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
encoded = payload + checksum
num = int.from_bytes(encoded, "big")
digits = ""
while num:
    num, rem = divmod(num, 58)
    digits = alphabet[rem] + digits
prefix = sum(1 for byte in encoded if byte == 0)
address = "1" * prefix + digits
print(address)
```

Executing the script prints `1Be2UF9NLfyLFbtm3TCbmuocc9N1Kduci1`, confirming the restored P2PKH output for Bitcoin Puzzle #36.
