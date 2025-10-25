# Bitcoin Puzzle #32 — P2PKH Reconstruction

Puzzle #32 publishes the familiar five-opcode pay-to-public-key-hash (P2PKH) locking script with a censored middle segment in the advertised address:

```
1FRoHA9xe-r8gHRqEvR
OP_DUP
OP_HASH160
9e42601eeaedc244e15f17375adb0e2cd08efdc9
OP_EQUALVERIFY
OP_CHECKSIG
```

Restoring the address follows the standard Base58Check workflow for a mainnet P2PKH output:

1. Prefix the 20-byte HASH160 payload with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte payload and append the first four checksum bytes.
3. Base58Check-encode the resulting 25-byte buffer. Leading zero bytes in the payload encode as the character `1`.

The procedure reconstructs the missing infix from the published clue:

- **Address:** `1FRoHA9xewq7DjrZ1psWJVeTer8gHRqEvR`
- **Missing infix:** `wq7DjrZ1psWJVeTe`

A concise Python snippet verifies the reconstruction:

```python
import hashlib

alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
hash160 = "9e42601eeaedc244e15f17375adb0e2cd08efdc9"
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

Executing the snippet prints `1FRoHA9xewq7DjrZ1psWJVeTer8gHRqEvR`, confirming the reconstructed P2PKH address for Puzzle #32.
