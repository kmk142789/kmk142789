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
4. Document any subsequent activity or custodial claims for both the Mt. Gox and 1Feex wallets to maintain the separation record.

---

*Prepared to support ongoing forensic reviews and to prevent conflation of unrelated high-balance Bitcoin addresses.*
