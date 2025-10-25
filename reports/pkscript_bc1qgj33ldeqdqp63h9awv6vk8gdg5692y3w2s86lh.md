# PKScript Analysis: bc1qgj33ldeqdqp63h9awv6vk8gdg5692y3w2s86lh

## Summary
The excerpt describes another P2WPKH locking script. Completing the dashed address `bc1qgj33l-y3w2s86lh` restores the full bech32 string `bc1qgj33ldeqdqp63h9awv6vk8gdg5692y3w2s86lh`.

```
bc1qgj33l-y3w2s86lh
Pkscript
OP_0
44a31fb7206803a8dcbd7334cb1d0d453455122e
Witness
3044022009ed1dba532f5e31025bdf11aba8b694704311a612d29f664ae71f2fe69dd04c02203105377da89f4b4a38a09a6ac8f8b7947b6d05aa83e9dbb7f5334cdcdc7eff6401
029b6480bfe42a1f3ffc865852fcc851b4dc1486fe565c39dd419c0d0adf89547e
```

## Details
- **Witness program:** `001444a31fb7206803a8dcbd7334cb1d0d453455122e` matches the standard version-0, 20-byte HASH160 template for P2WPKH. The shortened variant without the trailing `e` appears later in the transcript, reinforcing the reconstruction.
- **Derived address:** Bech32 encoding produces `bc1qgj33ldeqdqp63h9awv6vk8gdg5692y3w2s86lh`.
- **Witness stack:** The DER signature again ends with `0x01` (`SIGHASH_ALL`). The compressed public key begins with `0x02`; hashing it yields the witness program above.
- **Missing segment:** The hyphen stands in for the substring `deqdqp63h9awv6vk8gdg5692` inside the published address.

## Reproduction
Confirm the address with the helper:

```
python tools/pkscript_to_address.py <<'EOF'
bc1qgj33l-y3w2s86lh
Pkscript
OP_0
44a31fb7206803a8dcbd7334cb1d0d453455122e
EOF
```

Executing the command prints `bc1qgj33ldeqdqp63h9awv6vk8gdg5692y3w2s86lh`, verifying the P2WPKH decoding.
