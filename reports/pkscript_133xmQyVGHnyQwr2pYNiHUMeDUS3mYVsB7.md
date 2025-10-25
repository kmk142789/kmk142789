# PKScript Analysis: 133xmQyVGHnyQwr2pYNiHUMeDUS3mYVsB7

## Summary
The capture is a classic pay-to-public-key (P2PK) script fragment. Reinserting the missing characters converts the redacted label `133xmQyVG-US3mYVsB7` into the full legacy address `133xmQyVGHnyQwr2pYNiHUMeDUS3mYVsB7`.

```
133xmQyVG-US3mYVsB7
Pkscript
04db2bfc4aee47f0b45ae88bc76431940aa2547ef7ba34e4bf176f7cd37a3713e56a21ebece2a105df52bd6b4d213aaa8c7bb7c6556bff3e2a9d43e4658d5e3af2
OP_CHECKSIG
```

## Details
- **Public key:** `04db2bfc4aee47f0b45ae88bc76431940aa2547ef7ba34e4bf176f7cd37a3713e56a21ebece2a105df52bd6b4d213aaa8c7bb7c6556bff3e2a9d43e4658d5e3af2`
- **Script hex:** `4104db2bfc4aee47f0b45ae88bc76431940aa2547ef7ba34e4bf176f7cd37a3713e56a21ebece2a105df52bd6b4d213aaa8c7bb7c6556bff3e2a9d43e4658d5e3af2ac`
- **Derived P2PKH address:** Base58Check encoding of the HASH160 of the public key recovers `133xmQyVGHnyQwr2pYNiHUMeDUS3mYVsB7`.
- **Missing segment:** The dash replaces `HnyQwr2pYNiHUMeD` within the printed address.

## Reproduction
The helper script regenerates the address directly:

```
python tools/pkscript_to_address.py <<'EOF'
133xmQyVG-US3mYVsB7
Pkscript
04db2bfc4aee47f0b45ae88bc76431940aa2547ef7ba34e4bf176f7cd37a3713e56a21ebece2a105df52bd6b4d213aaa8c7bb7c6556bff3e2a9d43e4658d5e3af2
OP_CHECKSIG
EOF
```

Executing the command outputs `133xmQyVGHnyQwr2pYNiHUMeDUS3mYVsB7`, confirming the reconstruction.
