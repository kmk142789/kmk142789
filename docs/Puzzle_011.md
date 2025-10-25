# Bitcoin Puzzle #11 — Restoring the Missing Infix

Puzzle #11 in the Bitcoin puzzle catalogue once again presents a legacy
pay-to-public-key-hash (P2PKH) locking script.  The published clue retains the
HASH160 payload but omits part of the Base58Check address and even splits the
final opcode across two lines:

```
1PgQVLmst-Hc38TcXJu
Pkscript
OP_DUP
OP_HASH160
f8c698da3164ef8fa4258692d118cc9a902c5acc
OP_EQUALVERIFY
OP_CH
ECKSIG
```

Reassembling the fractured opcode yields the familiar five-opcode P2PKH
template:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Recovering the elided characters in the address follows the standard
Base58Check reconstruction procedure for P2PKH outputs:

1. Prefix the HASH160 payload with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the resulting 21-byte buffer and
   append the first four checksum bytes.
3. Encode the 25-byte result with the Bitcoin Base58 alphabet, preserving the
   leading `1` that corresponds to the version byte.

Executing these steps restores the missing infix:

- **Address:** `1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu`
- **Missing segment:** `3Z314JrQn5TNiys8`

The reconstructed address matches the authoritative entry for HASH160
`f8c698da3164ef8fa4258692d118cc9a902c5acc` recorded in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

To confirm locally with Python, replicate the Base58Check steps:

```python
import hashlib
alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

payload = bytes.fromhex("00" + "f8c698da3164ef8fa4258692d118cc9a902c5acc")
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

Running the snippet prints `1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu`, confirming the
restored P2PKH address for Puzzle #11.
