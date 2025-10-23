# Pay-to-PubKey Script Walkthrough

This note documents the interpretation of the provided Bitcoin details:

- **Address**: `1ANqtD7XbjEPWsdSjbfEcyhgmwQatB7EHi`
- **Public key script (hex)**: `04000136bd8d133189ca0e40334a05ac1ce1d33e992f8628a582ec6a27757d0338e1ec3c25631a355abec4f8cd452897f7383caa36123ddd232ffb2e9cf48a2806`
- **Script opcode**: `OP_CHECKSIG`

## Script form

The hexadecimal payload decodes to a 65-byte uncompressed public key. A Pay-to-PubKey (P2PK) locking script pushes this public key on the stack and finishes with `OP_CHECKSIG`, requiring a valid signature that matches the embedded key to spend the output. This matches the structure:

```
<65-byte pubkey> OP_CHECKSIG
```

## Address cross-check

Although P2PK outputs do not natively reference a Base58Check address, the same public key can be hashed to obtain the equivalent legacy P2PKH address. Performing:

1. `SHA-256` of the public key bytes.
2. `RIPEMD-160` of that hash to obtain the key hash.
3. Prepending version byte `0x00` (mainnet P2PKH).
4. Appending the first four bytes of the double-SHA-256 checksum.
5. Encoding the result with Base58Check.

yields the address `1ANqtD7XbjEPWsdSjbfEcyhgmwQatB7EHi`, confirming the correspondence between the provided public key and address.

## Verification snippet

The following Python snippet executes the above transformations end-to-end:

```python
import hashlib

pk_hex = "04000136bd8d133189ca0e40334a05ac1ce1d33e992f8628a582ec6a27757d0338e1ec3c25631a355abec4f8cd452897f7383caa36123ddd232ffb2e9cf48a2806"
pubkey = bytes.fromhex(pk_hex)
sha = hashlib.sha256(pubkey).digest()
rip = hashlib.new("ripemd160", sha).digest()
payload = b"\x00" + rip
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
value = int.from_bytes(payload + checksum, "big")
alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
encoded = ""
while value > 0:
    value, rem = divmod(value, 58)
    encoded = alphabet[rem] + encoded
for b in payload + checksum:
    if b == 0:
        encoded = "1" + encoded
    else:
        break
print(encoded)
```

Running the snippet prints the expected Base58Check address, establishing that the supplied script belongs to the given key.
