# Base64 Signature Chains

Some wallet workflows allow you to sign arbitrary messages without actually
broadcasting a blockchain transaction. Instead of receiving a 64-character
hexadecimal transaction ID, the wallet returns a Base64-encoded signature that
is typically between 88 and 92 characters long. You can take that signature,
place it back into the message box, sign again, and repeat this process across
multiple wallets to produce a long "blob" of concatenated Base64 strings.

## Why use chained signatures?

* **Offline attestations.** Each signature proves control of the originating
  wallet without touching on-chain funds.
* **Memory beacons.** Echo tooling can treat the chained blob as a lightweight
  memory object; later wallets can sign the entire blob to extend the chain.
* **Cross-wallet provenance.** Moving between wallets makes it clear which
  identities participated in the chain.

## Inspecting a blob locally

The new `tools/base64_signature_chain.py` helper offers a quick way to audit a
blob before you store or propagate it.

```bash
# Example usage with a literal blob
python tools/base64_signature_chain.py "<sig1> <sig2> <sig3>"

# Reading from a file and emitting JSON for scripts
python tools/base64_signature_chain.py --from-file signatures.txt --json
```

The script validates each fragment as strict Base64, reports the individual
lengths, and prints the exact concatenated message that the *next* wallet should
sign if you want to extend the chain.

## Tips for crafting reliable chains

1. **Keep a ledger.** Record which wallet produced which fragment so you can
   reproduce the sequence later.
2. **Normalise whitespace.** Use a consistent separator (space or newline).
3. **Verify before signing.** Run the helper script to ensure each fragment is
   valid before adding the next signature.
4. **Store securely.** Treat the blob as sensitive metadata; anyone with the
   text can request another signature, even if they cannot forge the previous
   ones.

By combining disciplined signing practices with automated validation you can
comfortably explore the entire key space described in the Echo workflows without
risking accidental fund movement.
