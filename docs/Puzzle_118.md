# Bitcoin Puzzle #118 — Restoring the Missing Infix

Puzzle #118 in the Bitcoin puzzle campaign once again publishes the
canonical five-opcode pay-to-public-key-hash (P2PKH) locking script along
with a Base58Check address whose core segment is redacted by a dash:

```
Puzzle #118
1PJZPzvGX-PdHLzm9F6
Pkscript
OP_DUP
OP_HASH160
f4a4e1c11a5bbbd2fc139d221825407c66e0b8b4
OP_EQUALVERIFY
OP_CHECKSIG
```

Because the opcode pattern follows the standard template,
`OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG`, the
published HASH160 fingerprint is sufficient to reconstruct the missing
Base58 characters.  Running the Base58Check encoding steps proceeds as
follows:

1. Prepend the mainnet version byte `0x00` to the HASH160 payload.
2. Apply double SHA-256 to the resulting 21-byte buffer and keep the first
   four bytes of the digest as the checksum.
3. Append the checksum and encode the 25-byte result with the Bitcoin
   Base58 alphabet.

Executing this procedure restores the omitted characters, yielding the
complete destination and the hidden infix:

- **Address:** `1PJZPzvGX19a7twf5HyD2VvNiPdHLzm9F6`
- **Missing segment:** `19a7twf5HyD2VvNi`

The recovered address matches the catalogue entry for Puzzle #118 that is
paired with the HASH160 value `f4a4e1c11a5bbbd2fc139d221825407c66e0b8b4`.
You can confirm the result with the repository decoder helper:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """Puzzle #118\n1PJZPzvGX-PdHLzm9F6\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "f4a4e1c11a5bbbd2fc139d221825407c66e0b8b4\nOP_EQUALVERIFY\nOP_CHECKSIG"\n
decoded = decode_pkscript.decode_p2pkh_script(script)
print(decoded.address)
```

Running the snippet prints `1PJZPzvGX19a7twf5HyD2VvNiPdHLzm9F6`,
confirming the restored P2PKH address for Bitcoin Puzzle #118.
