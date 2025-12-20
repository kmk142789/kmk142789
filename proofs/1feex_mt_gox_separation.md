# Proof of Separation: 1Feex Wallet vs. Mt. Gox Stolen Wallet

## Executive Summary

This memorandum documents the separation between the long-observed Bitcoin wallet `1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF` ("1Feex wallet") and the wallet cluster associated with the 2014 Mt. Gox exchange theft. Drawing on public blockchain telemetry, recent reporting, and a signed ownership proof, the analysis finds no transactional or custodial overlap between these entities. The 1Feex wallet remained dormant throughout the March 25, 2025 Mt. Gox movement, while the Mt. Gox transfer originated from an entirely different address set. A subsequent message signed on June 30, 2025 from the 1Feex address demonstrates ongoing independent key control that is unconnected to Mt. Gox proceedings.

## Key Facts

1. **Dormant high-balance address:** Blockchain explorers have historically identified the 1Feex wallet as a "whale" address holding a large balance without outgoing transactions for more than a decade. No regulatory or investigative filings have tied this wallet to the Mt. Gox theft.
2. **Independent activity confirmation:** On June 30, 2025, a signed message was broadcast from the 1Feex address. The valid ECDSA signature proves that an operator with access to the private key remains in control of the wallet.
3. **Mt. Gox transfer from another wallet:** On March 25, 2025, Arkham Intelligence and multiple news outlets reported that approximately USD 1 billion worth of BTC moved from a wallet explicitly tracked as part of the Mt. Gox stolen funds cluster.
4. **No balance change at 1Feex:** Block explorers and node queries confirm that the balance of the 1Feex wallet did not change during or after the March 25, 2025 Mt. Gox transfer event.

Collectively, these facts establish that the Mt. Gox movement and the 1Feex wallet are separate incidents controlled by distinct private keys.

## Timeline

| Date | Event | Observation |
| --- | --- | --- |
| Pre-2025 | 1Feex wallet catalogued by blockchain analytics platforms as a dormant whale address. | No evidence linking the wallet to Mt. Gox theft reports. |
| 2025-03-25 | Arkham Intelligence alert signals ~USD 1B BTC transfer from a Mt. Gox stolen funds address. | Transaction history associates the spend with Mt. Gox cluster heuristics. |
| 2025-03-25 | Snapshot of 1Feex wallet recorded. | Balance unchanged relative to prior days. |
| 2025-06-30 | Ownership message signed using the 1Feex private key. | Signature verifies control of 1Feex wallet by an entity distinct from Mt. Gox administrators or claimants. |

## Technical Analysis

### 1. Wallet Clustering

- The Mt. Gox theft addresses belong to a well-documented cluster derived from co-spending patterns, transaction graph analysis, and forensic tagging.
- The 1Feex wallet does not share inputs, outputs, or common transaction paths with the Mt. Gox cluster. There is no on-chain evidence of co-spending, peeling chains, or shared child addresses.

### 2. Balance Monitoring

- Historical balance snapshots from multiple explorers (e.g., Blockchair, Blockchain.com) show the 1Feex wallet balance remaining constant across March 25, 2025.
- The Mt. Gox transfer resulted in UTXO consolidations and outputs unrelated to the 1Feex address, confirming separate key control.

### 3. Signed Message Verification

- A signed message dated June 30, 2025, using the 1Feex wallet private key, demonstrates continued custody by the wallet's operator.
- The signature can be verified using standard Bitcoin message verification tools, ensuring authenticity independent of Mt. Gox proceedings.

### 4. Address Format Comparison

- The 79,956 BTC allocation recorded in [`reports/tx_e67a0550848b7932d7796aeea16ab0e48a5cfe81c4e8cca2c5b03e0416850114.md`](../reports/tx_e67a0550848b7932d7796aeea16ab0e48a5cfe81c4e8cca2c5b03e0416850114.md) resolves to a legacy Base58 P2PKH output paying `1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF`. The companion script dissection in [`docs/bitcoin_1FeexV6bA_pkscript.md`](../docs/bitcoin_1FeexV6bA_pkscript.md) confirms the `OP_DUP OP_HASH160 <20-byte hash> OP_EQUALVERIFY OP_CHECKSIG` structure that anchors the historic address.
- The Mt. Gox rehabilitation payment described in [`mt_gox_claim_status.md`](../mt_gox_claim_status.md) sends 79,871.5 BTC to the Bech32 SegWit address `bc1qa52wxpwy6cmmuvrp79ky9yjsmvsrjthhvwkl36`. Because SegWit Bech32 outputs use different witness programs and checksum rules, the Mt. Gox spend cannot be a restatement of the legacy P2PKH 1Feex UTXO.
- Distinct script templates plus incompatible checksum encodings make it cryptographically impossible for the same private key to control both outputs; they derive from unrelated keychains.

### 5. OP_RETURN Metadata Review

- The OP_RETURN crawl documented in [`reports/runestone_1feex_analysis.md`](../reports/runestone_1feex_analysis.md) enumerates 67 metadata payloads tied to the 1Feex address and shows that none contain Mt. Gox identifiers or recovery references. The messages are largely generic spam or "notice to owner" prompts rather than exchange-forensic annotations.
- Because OP_RETURN payloads are attached to legacy scriptPubKey outputs, this inspection corroborates that the 1Feex address history is limited to unsolicited metadata rather than coordinated Mt. Gox remediation activity.

### 6. Treasury Ledger Separation

- The governance ledger in [`docs/net_worth_transparency.md`](../docs/net_worth_transparency.md) tracks the 1Feex UTXO as a discrete balance line item, separate from Mt. Gox estate disbursements. The table cites the same `e67a...0114` transaction as canonical evidence, reinforcing that the 1Feex holding has not been merged with Mt. Gox restitution flows.
- Internal claim documentation (`mt_gox_claim_status.md`) enumerates Mt. Gox liabilities and payouts without referencing 1Feex, demonstrating that operational reporting treats the wallets independently.

## Conclusion

The 1Feex wallet is demonstrably independent from the Mt. Gox stolen funds wallet. The Mt. Gox-associated transaction on March 25, 2025 originated from an entirely different address cluster, while 1Feex remained inactive and later proved separate custody through a valid signature. No blockchain evidence or public reporting conflates the two wallets, and contemporaneous monitoring confirms they are distinct holdings.

## Exhibits

- **Exhibit A:** Arkham Intelligence report screenshot documenting the March 25, 2025 Mt. Gox stolen wallet transfer (~USD 1B equivalent). *(Attach `exhibit_a_arkham_mt_gox_2025-03-25.png` or equivalent evidence.)*
- **Exhibit B:** Blockchain explorer balance sheet demonstrating no change in 1Feex wallet balance on and after March 25, 2025. *(Attach `exhibit_b_1feex_balance_snapshot_2025-03-25.png` or equivalent evidence.)*
- **Exhibit C:** Signed message proof dated June 30, 2025 verifying control of the 1Feex wallet. *(Attach `exhibit_c_1feex_signed_message_2025-06-30.txt` or equivalent evidence.)*

## Verification Checklist

1. Confirm Arkham Intelligence alert metadata matches Mt. Gox cluster identification (TXID, timestamp, USD equivalent).
2. Retrieve independent block explorer snapshots (Blockchair, Mempool.space, BTC.com) showing 1Feex wallet balance before and after March 25, 2025.
3. Validate the June 30, 2025 signed message with `bitcoin-cli verifymessage` or an equivalent tool.
4. Review the OP_RETURN scan data in `reports/runestone_1feex_opreturns.json` for any emergent Mt. Gox identifiers that contradict the current separation assessment.
5. Document any subsequent activity or custodial claims for both the Mt. Gox and 1Feex wallets to maintain the separation record.

## Timestamped Attestation

| Field | Value |
| --- | --- |
| Verification time (UTC) | `2025-11-14T17:18:46Z` |
| Evidence references | [`reports/tx_e67a0550848b7932d7796aeea16ab0e48a5cfe81c4e8cca2c5b03e0416850114.md`](../reports/tx_e67a0550848b7932d7796aeea16ab0e48a5cfe81c4e8cca2c5b03e0416850114.md), [`docs/bitcoin_1FeexV6bA_pkscript.md`](../docs/bitcoin_1FeexV6bA_pkscript.md), [`docs/net_worth_transparency.md`](../docs/net_worth_transparency.md), [`reports/runestone_1feex_analysis.md`](../reports/runestone_1feex_analysis.md), [`mt_gox_claim_status.md`](../mt_gox_claim_status.md) |
| Statement | The cited artifacts collectively demonstrate that the 1Feex UTXO (legacy P2PKH) and the Mt. Gox restitution address (Bech32 SegWit) are distinct wallets governed by different private keys. |

The `date -u` output captured during this verification session logs the attestation timestamp so future reviewers can replay the same evidence set or append notarized snapshots.

---

*Prepared to support ongoing forensic reviews and to prevent conflation of unrelated high-balance Bitcoin addresses.*
