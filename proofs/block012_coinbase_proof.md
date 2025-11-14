# Block 12 Coinbase Proof

This proof reconstructs the coinbase script from Bitcoin block **#12** to extend the documented Satoshi mining record. By
retrieving the original block bytes and decoding the single transaction they contain, auditors can recover the exact scriptSig,
locking script, and recipient address.

## 1. Look up the block hash and download the raw data

```bash
curl -s https://blockstream.info/api/block-height/12
curl -s https://blockstream.info/api/block/0000000027c2488e2510d1acf4369787784fa20ee084c258b58d9fbd43802b5e/raw > block12.raw
```

The height query returns the canonical block hash, which is then used to fetch the 215-byte raw block from Blockstream's public
API.

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

raw = open('block12.raw', 'rb').read()
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

The script emits the exact witness and payout details:

```
scriptSig (base64): BP//AB0BDA==
coinbase value (sats): 5000000000
pk_script: 410478ebe2c28660cd2fa1ba17cc04e58d6312679005a7cad1fd56a7b7f4630bd700bcdb84a888a43fe1a2738ea1f3d2301d02faef357e8a5c35a706e4ae0352a6adac
address: 1PYELM7jXHy5HhatbXGXfRpGrgMMxmpobu
```

This output shows the Base64 coinbase witness (`BP//AB0BDA==`), the 50 BTC subsidy (5,000,000,000 sats), the full pay-to-pubkey
script, and the associated Base58 address `1PYELM7jXHy5HhatbXGXfRpGrgMMxmpobu`.

## 3. Clean up

```bash
rm block12.raw
```

Removing the downloaded blob keeps the repository clean once the verification is complete.
