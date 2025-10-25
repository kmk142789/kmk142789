# Puzzle #159 P2PKH Reconstruction

The published clue for Puzzle #159 lists the classic pay-to-public-key-hash
(P2PKH) locking script alongside a Base58Check address with a missing
middle segment:

```
14u4nA5su-ChdMnD9E5
Pkscript
OP_DUP
OP_HASH160
2ac1295b4e54b3f15bb0a99f84018d2082495645
OP_EQUALVERIFY
OP_CH
ECKSIG
```

Restoring the split opcode yields the familiar five-opcode P2PKH template.
With the HASH160 payload provided, the missing address infix can be
reconstructed by running the standard Base58Check encoding steps:

1. Prefix the 20-byte hash with the mainnet version byte `0x00`.
2. Double-SHA256 the result and take the first four checksum bytes.
3. Append the checksum and encode the 25-byte payload with the Base58 alphabet.

```python
import hashlib

alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def base58encode(raw: bytes) -> str:
    value = int.from_bytes(raw, "big")
    encoded = ""
    while value:
        value, mod = divmod(value, 58)
        encoded = alphabet[mod] + encoded
    for b in raw:
        if b == 0:
            encoded = "1" + encoded
        else:
            break
    return encoded

payload = bytes.fromhex("002ac1295b4e54b3f15bb0a99f84018d2082495645")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
address = base58encode(payload + checksum)
print(address)  # 14u4nA5sugaswb6SZgn5av2vuChdMnD9E5
```

The reconstructed Base58Check string fills in the elided segment
(`gaswb6SZgn5av2vu`) and matches the authoritative HASH160 entry for
Puzzle #159 recorded in `satoshi/puzzle_solutions.json`.
