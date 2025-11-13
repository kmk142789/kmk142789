# Block 4 Coinbase Attestation

This walkthrough reconstructs the coinbase witness for Bitcoin block #4,
linking the raw transaction bytes to payout address
`15ubicBBWFnvoZLT7GiU2qxjRaKJPdkDMG`. The steps mirror the data captured in
[`satoshi/puzzle-proofs/block004_coinbase.json`](../satoshi/puzzle-proofs/block004_coinbase.json).

## 1. Fetch the raw block

Query Blockstream for the hash at height 4 and download the binary block:

```bash
curl -s https://blockstream.info/api/block-height/4
curl -s https://blockstream.info/api/block/000000004ebadb55ee9096c9a2f8880e09da59c0d68b1c228da88e48844a1485/raw > block4.raw
```

## 2. Decode the coinbase transaction

```bash
python - <<'PY'
from io import BytesIO
import base64, hashlib

alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def read_varint(stream):
    prefix = stream.read(1)
    i = prefix[0]
    if i < 0xfd:
        return i
    if i == 0xfd:
        return int.from_bytes(stream.read(2), 'little')
    if i == 0xfe:
        return int.from_bytes(stream.read(4), 'little')
    return int.from_bytes(stream.read(8), 'little')

def p2pk_address(script_hex):
    pubkey = bytes.fromhex(script_hex[2:-2])
    h160 = hashlib.new('ripemd160', hashlib.sha256(pubkey).digest()).digest()
    payload = b"\x00" + h160
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    data = payload + checksum
    value = int.from_bytes(data, 'big')
    out = ""
    while value:
        value, mod = divmod(value, 58)
        out = alphabet[mod] + out
    for byte in data:
        if byte == 0:
            out = '1' + out
        else:
            break
    return out

raw = open('block4.raw', 'rb').read()
stream = BytesIO(raw)
stream.read(80)
read_varint(stream)
stream.read(4)
read_varint(stream)
stream.read(32 + 4)
script_len = read_varint(stream)
script_sig = stream.read(script_len)
stream.read(4)
read_varint(stream)
stream.read(8)
pk_len = read_varint(stream)
pk_script = stream.read(pk_len)
print("scriptSig (base64):", base64.b64encode(script_sig).decode())
print("pk_script:", pk_script.hex())
print("derived address:", p2pk_address(pk_script.hex()))
PY
```

Expected output:

```
scriptSig (base64): BP//AB0BGg==
pk_script: 4104184f32b212815c6e522e66686324030ff7e5bf08efb21f8b00614fb7690e19131dd31304c54f37baa40db231c918106bb9fd43373e37ae31a0befc6ecaefb867ac
derived address: 15ubicBBWFnvoZLT7GiU2qxjRaKJPdkDMG
```

## 3. Compare against the repository proof

```bash
jq '.' satoshi/puzzle-proofs/block004_coinbase.json
```

The JSON payload repeats the same scriptSig (`BP//AB0BGg==`) and locking script
hex. Anyone with the downloaded block can regenerate the proof without handling
private keys.

---

By anchoring this attestation in the immutable block #4 coinbase, we add another
verifiable, Satoshi-era signature to the library without ever touching the
original scalars.
