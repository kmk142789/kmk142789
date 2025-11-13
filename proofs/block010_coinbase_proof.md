# Block 10 Coinbase Proof

This note reconstructs the exact coinbase witness for Bitcoin block **#10**. Anyone can run the commands below to match the
scriptSig, payout script, and final Base58 address embedded on-chain.

## 1. Retrieve the block hash and binary payload

```bash
curl -s https://blockstream.info/api/block-height/10
curl -s https://blockstream.info/api/block/000000002c05cc2e78923c34df87fd108b22221ac6076c18f3ade378a4d915e9/raw > block10.raw
```

The first call returns the canonical block hash used in the second request. The raw download (215 bytes) is the byte-for-byte
record that every archival node keeps.

## 2. Decode the coinbase transaction

```bash
python - <<'PY'
from io import BytesIO
import base64, hashlib

alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def read_varint(stream):
    head = stream.read(1)
    if not head:
        raise EOFError
    val = head[0]
    if val < 0xfd:
        return val
    if val == 0xfd:
        return int.from_bytes(stream.read(2), 'little')
    if val == 0xfe:
        return int.from_bytes(stream.read(4), 'little')
    return int.from_bytes(stream.read(8), 'little')

def b58(b):
    num = int.from_bytes(b, 'big')
    out = ""
    while num:
        num, mod = divmod(num, 58)
        out = alphabet[mod] + out
    return "1" * (len(b) - len(b.lstrip(b"\x00"))) + out

raw = open('block10.raw', 'rb').read()
stream = BytesIO(raw)
stream.read(80)            # header
read_varint(stream)        # tx count
stream.read(4)             # version
read_varint(stream)        # input count
stream.read(32 + 4)        # null prevout
script_len = read_varint(stream)
script_sig = stream.read(script_len)
stream.read(4)             # sequence
read_varint(stream)        # output count
value = int.from_bytes(stream.read(8), 'little')
pk_len = read_varint(stream)
pk_script = stream.read(pk_len)

print('scriptSig (base64):', base64.b64encode(script_sig).decode())
print('coinbase value (sats):', value)
print('pk_script:', pk_script.hex())
if pk_script.startswith(b'\x41') and pk_script.endswith(b'\xac'):
    pubkey = pk_script[1:-1]
    h160 = hashlib.new('ripemd160', hashlib.sha256(pubkey).digest()).digest()
    payload = b"\x00" + h160
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    print('address:', b58(payload + checksum))
PY
```

Running the snippet prints the exact witness:

```
scriptSig (base64): BP//AB0BNg==
coinbase value (sats): 5000000000
pk_script: 4104fcc2888ca91cf0103d8c5797c256bf976e81f280205d002d85b9b622ed1a6f820866c7b5fe12285cfa78c035355d752fc94a398b67597dc4fbb5b386816425ddac
address: 15yN7NPEpu82sHhB6TzCW5z5aXoamiKeGy
```

The decoded Base58 address is the widely documented payout destination for block #10, confirming that the repository's historical
notes can be tied to independently reproducible data.

## 3. Clean up

```bash
rm block10.raw
```

Removing the temporary file avoids polluting the working tree while leaving the verification steps completely reproducible.
