# Puzzle #37 P2PKH Reconstruction

Puzzle #37 publishes the standard legacy pay-to-public-key-hash (P2PKH) locking script with the
HASH160 payload `28c30fb9118ed1da72e7c4f89c0164756e8a021d`. Only the outer fragments of the
Base58Check address accompany the script, leaving the middle section redacted as
`14iXhn8bG-ntcpL4dex`.

## Script template

```
OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
```

Replacing `<pubKeyHash>` with the broadcast hash produces the canonical Bitcoin mainnet script. The
missing infix drops out when the Base58Check address is rebuilt from the HASH160 payload.

## Address recovery

```python
import hashlib

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

hash160 = "28c30fb9118ed1da72e7c4f89c0164756e8a021d"
payload = bytes.fromhex("00" + hash160)
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
value = int.from_bytes(payload + checksum, "big")
address = ""
while value:
    value, mod = divmod(value, 58)
    address = ALPHABET[mod] + address
# Preserve leading zero bytes as "1" characters
for byte in payload + checksum:
    if byte == 0:
        address = "1" + address
    else:
        break
print(address)  # 14iXhn8bGajVWegZHJ18vJLHhntcpL4dex
```

Executing the snippet reconstructs the full address `14iXhn8bGajVWegZHJ18vJLHhntcpL4dex`, revealing
the missing infix `ajVWegZHJ18vJLHhn` and matching the attested entry for Bitcoin Puzzle #37 in
`satoshi/puzzle_solutions.json`.
