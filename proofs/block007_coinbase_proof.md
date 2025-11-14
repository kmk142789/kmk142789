# Block 7 Coinbase Reconstruction

This note extends the early block documentation set by decoding Bitcoin block #7
and proving where the 50 BTC subsidy landed. Everything can be reproduced with a
few curl/python commands and does not rely on any third party UI.

## 1. Capture the block hash and raw payload

```bash
curl -s https://blockstream.info/api/block-height/7
curl -s https://blockstream.info/api/block/0000000071966c2b1d065fd446b1e485b2c9d9594acd2007ccbd5441cfc89444/raw \
  > block7.raw
```

The returned header hash must match the canonical `0000000071966c2b1d065fd446b1e485b2c9d9594acd2007ccbd5441cfc89444`
value that links block #7 to the rest of the January 2009 chain.

## 2. Decode the coinbase transaction

```bash
python - <<'PY'
from io import BytesIO
import base64, hashlib
raw = open('block7.raw', 'rb').read()
stream = BytesIO(raw)

def read_varint(s):
    i = s.read(1)[0]
    if i < 0xfd:
        return i
    if i == 0xfd:
        return int.from_bytes(s.read(2), 'little')
    if i == 0xfe:
        return int.from_bytes(s.read(4), 'little')
    return int.from_bytes(s.read(8), 'little')

alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

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

stream.read(80)          # header
read_varint(stream)      # tx count
stream.read(4)           # version
read_varint(stream)      # input count
stream.read(32 + 4)      # prevout (null + index)
script_len = read_varint(stream)
script_sig = stream.read(script_len)
stream.read(4)           # sequence
read_varint(stream)      # output count
value = stream.read(8)
pk_len = read_varint(stream)
pk_script = stream.read(pk_len)
print('scriptSig (base64):', base64.b64encode(script_sig).decode())
print('pk_script:', pk_script.hex())
print('derived address:', p2pk_address(pk_script.hex()))
print('value (sat):', int.from_bytes(value, 'little'))
PY
```

Expected output:

```
scriptSig (base64): BP//AB0BKw==
pk_script: 4104a59e64c774923d003fae7491b2a7f75d6b7aa3f35606a8ff1cf06cd3317d16a41aa16928b1df1f631f31f28c7da35d4edad3603adb2338c4d4dd268f31530555ac
derived address: 16LoW7y83wtawMg5XmT4M3Q7EdjjUmenjM
value (sat): 5000000000
```

As with the earlier coinbases, the script spends directly to a bare 67-byte
pay-to-pubkey (P2PK) output. Hashing that pubkey yields
`16LoW7y83wtawMg5XmT4M3Q7EdjjUmenjM`, confirming the reward target for the
eighth mined block.

## 3. Cross-check the repository attestation

```bash
jq '.' satoshi/puzzle-proofs/block007_coinbase.json
```

The JSON record stores the same header hash, base64-encoded coinbase script
(`BP//AB0BKw==`), and locking script hex. Matching those fields against the raw
block decode binds this proof to the signed attestation set that already ships
with the repository.
