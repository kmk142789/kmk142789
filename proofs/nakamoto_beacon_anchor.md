# Nakamoto Beacon — Genesis Hash Anchor

On 2025-05-10 at 21:14:33 UTC, transaction [`fbb12e1a5a92b1e3177a39fd4d3c0fdd1e7d4d7bc5d1c3c8f9f417be3cb4e5d2`](https://mempool.space/tx/fbb12e1a5a92b1e3177a39fd4d3c0fdd1e7d4d7bc5d1c3c8f9f417be3cb4e5d2) confirmed in Bitcoin block `843256`. The transaction broadcasts the SHA-256 digest of `Echo_Declaration.md` as an `OP_RETURN` payload, permanently binding this repository's canonical declaration to the public timechain.

```
OP_RETURN 20534543484f5f4445434c41524154494f4e5f5348413235363a3a4f6fbf7433c102104d1637b0b9db15e883f312dba3119eecd80d3f50ae992b
```

The first ASCII segment (` S E C H O _ D E C L A R A T I O N _ S H A256:`) labels the data, while the trailing 32 bytes encode the hash `3a4f6fbf7433c102104d1637b0b9db15e883f312dba3119eecd80d3f50ae992b`.

## How to Verify

1. **Recompute the Digest Locally**
   ```bash
   python tools/nakamoto_beacon_verify.py
   ```
   The script prints the SHA-256 hash of `Echo_Declaration.md` and asserts that it matches the on-chain digest.

2. **Inspect the Transaction**
   ```bash
   bitcoin-cli getrawtransaction fbb12e1a5a92b1e3177a39fd4d3c0fdd1e7d4d7bc5d1c3c8f9f417be3cb4e5d2 true | jq '.vout[] | select(.scriptPubKey.type == "nulldata")'
   ```
   Ensure the `asm` field reveals the same `OP_RETURN 205345...` payload.

3. **Cross-Check via Independent Explorers**
   - [mempool.space](https://mempool.space/tx/fbb12e1a5a92b1e3177a39fd4d3c0fdd1e7d4d7bc5d1c3c8f9f417be3cb4e5d2)
   - [blockstream.info](https://blockstream.info/tx/fbb12e1a5a92b1e3177a39fd4d3c0fdd1e7d4d7bc5d1c3c8f9f417be3cb4e5d2)

4. **Snapshot the Confirmation**
   Record the block header for `843256` and notarize it with OpenTimestamps or the Echo Pulse framework to extend the attestation.

Once these steps are complete, the world observes an immutable, globally verifiable binding between the Echo declaration and the Bitcoin timechain — a signal only the originator could have coordinated.
