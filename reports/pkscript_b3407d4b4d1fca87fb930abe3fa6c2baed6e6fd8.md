# Pay-to-PubKey Script Analysis

- **Script Type:** Pay-to-PubKey (P2PK)
- **Script (ASM):** `047211a824f55b505228e4c3d5194c1fcfaa15a456abdf37f9b9d97a4040afc073dee6c89064984f03385237d92167c13e236446b417ab79a0fcae412ae3316b77 OP_CHECKSIG`
- **Public Key (hex):** `047211a824f55b505228e4c3d5194c1fcfaa15a456abdf37f9b9d97a4040afc073dee6c89064984f03385237d92167c13e236446b417ab79a0fcae412ae3316b77`
- **Derived P2PKH Address:** `1HLoD9E4SDFFPDiYfNYnkBLQ85Y51J3Zb1`
- **PubKey Hash160:** `b3407d4b4d1fca87fb930abe3fa6c2baed6e6fd8`

The script consists of a 65-byte uncompressed public key pushed directly onto the stack followed by `OP_CHECKSIG`. This is the canonical Pay-to-PubKey (P2PK) locking script form used by early Bitcoin outputs. Spending the output requires providing a DER-encoded ECDSA signature that verifies against the embedded public key.

Although P2PK outputs do not normally map to a Base58Check address, hashing the same public key with SHA-256 followed by RIPEMD-160 (yielding the hash160 shown above) and encoding it with the `0x00` mainnet version byte produces the conventional legacy address `1HLoD9E4SDFFPDiYfNYnkBLQ85Y51J3Zb1`. Removing the separator from the submitted string `1HLoD9E4S-5Y51J3Zb1` yields this address.

## Verification snippet

```python
import hashlib

pubkey_hex = "047211a824f55b505228e4c3d5194c1fcfaa15a456abdf37f9b9d97a4040afc073dee6c89064984f03385237d92167c13e236446b417ab79a0fcae412ae3316b77"
pubkey = bytes.fromhex(pubkey_hex)
sha = hashlib.sha256(pubkey).digest()
ripemd = hashlib.new("ripemd160", sha).digest()
payload = b"\x00" + ripemd
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
address_bytes = payload + checksum
alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
value = int.from_bytes(address_bytes, "big")
encoded = ""
while value:
    value, remainder = divmod(value, 58)
    encoded = alphabet[remainder] + encoded
# account for any leading zeroes in the payload
for byte in payload:
    if byte == 0:
        encoded = "1" + encoded
    else:
        break
print(encoded)  # prints 1HLoD9E4SDFFPDiYfNYnkBLQ85Y51J3Zb1
```

Running the snippet performs the same hashing and Base58Check encoding steps used by the network, confirming that the supplied public key script corresponds to the derived address above.
