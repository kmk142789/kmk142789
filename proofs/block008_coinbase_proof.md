# Block 8 Coinbase Proof

This walkthrough reconstructs the exact coinbase payout stored in Bitcoin block **#8**. The steps mirror the procedures that
already exist for neighbouring blocks so independent reviewers can compare the derived witness, script, and destination address
with the raw blockchain data.

## 1. Resolve the block hash and download the payload

```bash
curl -s https://blockstream.info/api/block-height/8
curl -s https://blockstream.info/api/block/00000000408c48f847aa786c2268fc3e6ec2af68e8468a34a28c61b7f1de0dc6/raw > block8.raw
```

The first command prints the canonical hash for height 8. The second stores the 215-byte raw block so the coinbase transaction
can be decoded offline.

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

def b58(data):
    num = int.from_bytes(data, 'big')
    out = ""
    while num:
        num, mod = divmod(num, 58)
        out = alphabet[mod] + out
    return "1" * (len(data) - len(data.lstrip(b"\x00"))) + out

raw = open('block8.raw', 'rb').read()
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
    address = b58(payload + checksum)
    print('address:', address)
PY
```

Running the decoder prints:

```
scriptSig (base64): BP//AB0BLA==
coinbase value (sats): 5000000000
pk_script: 4104cc8d85f5e7933cb18f13b97d165e1189c1fb3e9c98b0dd5446b2a1989883ff9e740a8a75da99cc59a21016caf7a7afd3e4e9e7952983e18d1ff70529d62e0ba1ac
address: 1J6PYEzr4CUoGbnXrELyHszoTSz3wCsCaj
```

The Base64 scriptSig matches the header-only witness stored in the raw block, the eight-byte value equals 50 BTC, and the decoded
P2PK script resolves to the historically documented address `1J6PYEzr4CUoGbnXrELyHszoTSz3wCsCaj`.

## 3. Clean up

```bash
rm block8.raw
```

Removing the temporary download keeps the working tree tidy while leaving every verification step fully reproducible.
