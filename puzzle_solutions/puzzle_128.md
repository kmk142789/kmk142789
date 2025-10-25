# Puzzle #128 Solution

## Given information
- **Base58 clue (with missing middle)**: `1EdAw4EMk-5chSg5ev6`
- **Provided P2PKH locking script**: `OP_DUP OP_HASH160 9570e68f5fad1b67f9ed9fea078fe9ef4767815b OP_EQUALVERIFY OP_CHECKSIG`

The script reveals the 20-byte hash160 of the public key. Because the opcodes match the standard Pay-to-Public-Key-Hash template, the address must be a mainnet P2PKH address.

## Reconstructing the payload
1. **Version prefix** (mainnet P2PKH): `0x00`
2. **Hash160** (from the script): `95 70 e6 8f 5f ad 1b 67 f9 ed 9f ea 07 8f e9 ef 47 67 81 5b`
3. **Payload**: concatenate the version byte and hash160 →
   `00 95 70 e6 8f 5f ad 1b 67 f9 ed 9f ea 07 8f e9 ef 47 67 81 5b`

## Computing the checksum
Double-SHA256 the payload and take the first four bytes:
- `SHA256(payload)`  → `b2d6899745414433208fdc934aef5073fd0dc72e98475e80e7d2c26a6f04b8d4`
- `SHA256(SHA256(payload))` → `7a47631f2ad8d7fa3aa22695ce4c6c69a99d7e32a9908aeb78f7ccd6554a3f54`
- **Checksum** (first 4 bytes): `7a 47 63 1f`

Appending the checksum to the payload produces the 25-byte binary form:  
`00 95 70 e6 8f 5f ad 1b 67 f9 ed 9f ea 07 8f e9 ef 47 67 81 5b 7a 47 63 1f`

## Base58Check encoding
Encoding the payload+checksum in Base58 yields:

```
1EdAw4EMkXUU8R3QdeesjWNSW5chSg5ev6
```

The completed address drops neatly into the clue, replacing the missing middle segment:

```
1EdAw4EMk[XUU8R3QdeesjWNSW]5chSg5ev6
```

## Verification snippet
You can verify the Base58Check encoding with the following Python snippet:

```python
from hashlib import sha256

alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
hash160 = bytes.fromhex('9570e68f5fad1b67f9ed9fea078fe9ef4767815b')
payload = b'\x00' + hash160
checksum = sha256(sha256(payload).digest()).digest()[:4]
value = int.from_bytes(payload + checksum, 'big')
encoded = ''
while value:
    value, mod = divmod(value, 58)
    encoded = alphabet[mod] + encoded
encoded = '1' * (len(payload + checksum) - len((payload + checksum).lstrip(b'\x00'))) + encoded
print(encoded)
# -> 1EdAw4EMkXUU8R3QdeesjWNSW5chSg5ev6
```

Thus, the fully reconstructed Bitcoin address for puzzle #128 is **`1EdAw4EMkXUU8R3QdeesjWNSW5chSg5ev6`**.
