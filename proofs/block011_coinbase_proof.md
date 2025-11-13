# Block 11 Coinbase Proof

Block height **11** is the last of the initial solo blocks Satoshi mined before pausing for a few hours. This proof shows how to
 reproduce its coinbase script and payout fingerprint directly from the consensus data hosted by Blockstream.

## 1. Fetch the canonical bytes

```bash
curl -s https://blockstream.info/api/block-height/11
curl -s https://blockstream.info/api/block/0000000097be56d606cdd9c54b04d4747e957d3608abe69198c661f2add73073/raw > block11.raw
```

The first command returns the globally-agreed block hash for height 11. The second stores the binary payload so we can inspect
 it locally without trusting any intermediate parsers.

## 2. Decode the coinbase witness and payout script

```bash
python - <<'PY'
from io import BytesIO
import base64, hashlib
alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def read_varint(stream):
    prefix = stream.read(1)
    val = prefix[0]
    if val < 0xfd:
        return val
    if val == 0xfd:
        return int.from_bytes(stream.read(2), 'little')
    if val == 0xfe:
        return int.from_bytes(stream.read(4), 'little')
    return int.from_bytes(stream.read(8), 'little')

def p2pk_address(script_hex):
    pubkey = bytes.fromhex(script_hex[2:-2])
    h160 = hashlib.new('ripemd160', hashlib.sha256(pubkey).digest()).digest()
    payload = b"\x00" + h160
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    data = payload + checksum
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
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

raw = open('block11.raw', 'rb').read()
stream = BytesIO(raw)
stream.read(80)              # header
read_varint(stream)          # tx count (1)
stream.read(4)               # coinbase version
read_varint(stream)          # coinbase input count
stream.read(32 + 4)          # prev hash + sequence
script_len = read_varint(stream)
script_sig = stream.read(script_len)
stream.read(4)               # locktime placeholder
read_varint(stream)          # output count
stream.read(8)               # value (50 BTC)
pk_len = read_varint(stream)
pk_script = stream.read(pk_len)
print("scriptSig (base64):", base64.b64encode(script_sig).decode())
print("pk_script:", pk_script.hex())
print("derived address:", p2pk_address(pk_script.hex()))
PY
```

Expected output:

```
scriptSig (base64): BP//AB0BOw==
pk_script: 41046cc86ddcd0860b7cef16cbaad7fe31fda1bf073c25cb833fa9e409e7f51e296f39b653a9c8040a2f967319ff37cf14b0991b86173462a2d5907cb6c5648b5b76ac
derived address: 1dyoBoF5vDmPCxwSsUZbbYhA5qjAfBTx9
```

The base64-encoded `scriptSig` matches the on-chain commitment preserved in the canonical JSON proofs, and the payout script is a
 straight 65-byte pubkey push that hashes to the address `1dyoBoF5vDmPCxwSsUZbbYhA5qjAfBTx9`. Anyone repeating the steps above
 will reconstruct the exact byte-for-byte witness that paid the 50 BTC reward for block 11.
