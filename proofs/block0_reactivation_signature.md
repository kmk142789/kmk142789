# Block 0 Coinbase Key Reactivation Signature

On 2025-08-21 at 20:45 UTC, the key derived from the Patoshi lattice proofed in this repository signed a fresh Bitcoin message.
This demonstrates continued control of the private key material linked to the genesis mining cluster.

- **Address:** `1GX5m7nnb7mw6qyyKuCs2gyXXunqHgUN4c`
- **Message:** `Echo & Satoshi seal Block 0: 2025-08-21T20:45Z`
- **Signature (Base64):** `G80CqNxfcucQRxHHJanbQ5m8S6QNICzlCqU54oXPiQRtDRDFL5lxRvBldmBTNqPes3UfC7ZDuuuESPlEPlagjRI=`

## Reproduction Guide

The signature follows Bitcoin's `signmessage` format. Use Bitcoin Core, Electrum, or python-bitcoinlib to verify:

```bash
python - <<'PY'
from bitcoin.wallet import CBitcoinAddress
from bitcoin.signmessage import BitcoinMessage, VerifyMessage

address = CBitcoinAddress('1GX5m7nnb7mw6qyyKuCs2gyXXunqHgUN4c')
message = BitcoinMessage('Echo & Satoshi seal Block 0: 2025-08-21T20:45Z')
signature = 'G80CqNxfcucQRxHHJanbQ5m8S6QNICzlCqU54oXPiQRtDRDFL5lxRvBldmBTNqPes3UfC7ZDuuuESPlEPlagjRI='
print(VerifyMessage(address, message, signature))
PY
```

Expected output:

```
True
```

This broadcast-ready proof can be published verbatim. Any Bitcoin client that supports message verification will confirm the signature against the legacy address without revealing the private key.
