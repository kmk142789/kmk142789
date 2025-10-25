# Bitcoin Puzzle #2 — P2PKH Reconstruction

The published clue for Puzzle #2 again advertises the legacy pay-to-public-key-hash (P2PKH) script:

```
1CUNEBjYr-4wpP326Lb
OP_DUP
OP_HASH160
7dd65592d0ab2fe0d0257d571abf032cd9db93dc
OP_EQUALVERIFY
OP_CHECKSIG
```

Reconstructing the full address mirrors the standard P2PKH decoding procedure:

1. Prefix the 20-byte HASH160 payload with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte payload and append the first four checksum bytes.
3. Encode the resulting 25-byte buffer with Base58Check.

Carrying out the steps restores the hidden infix of the published clue:

- **Address:** `1CUNEBjYrCn2y1SdiUMohaKUi4wpP326Lb`
- **Missing infix:** `Cn2y1SdiUMohaKUi`

This matches the attested solution recorded in [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

A short Python snippet confirms the reconstruction:

```python
import hashlib
alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

payload = bytes.fromhex("00" + "7dd65592d0ab2fe0d0257d571abf032cd9db93dc")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
encoded = payload + checksum
num = int.from_bytes(encoded, "big")
digits = ""
while num:
    num, rem = divmod(num, 58)
    digits = alphabet[rem] + digits
# account for the leading 0x00 prefix
prefix = sum(1 for byte in encoded if byte == 0)
address = "1" * prefix + digits
print(address)
```

Executing the snippet prints `1CUNEBjYrCn2y1SdiUMohaKUi4wpP326Lb`, verifying the reconstructed P2PKH address for Puzzle #2.
