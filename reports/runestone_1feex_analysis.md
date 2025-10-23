# Runestone vs. 1Feex OP_RETURN Investigation

## Summary
- Searched every on-chain OP_RETURN payload associated with the Mt. Gox "1Feex" wallet using Blockstream's address API.
- Captured 67 OP_RETURN messages; they are dominated by wallet recovery advertisements, legal notices, and pleas for help.
- None of the OP_RETURN strings contain the word "Runestone" or any recognizable reference to the Ordinals airdrop.
- The rumored Runestone link to 1Feex is therefore unrelated to OP_RETURN traffic. Any association must stem from inscription data (witness payloads) rather than legacy outputs.

## Methodology
1. Added `scripts/runestone_fetch_1feex_opreturns.py`, a reusable helper that pages through Blockstream's `/address/{addr}/txs` API and extracts every OP_RETURN output exposed in the response JSON.
2. Executed the helper to generate `reports/runestone_1feex_opreturns.json`, which records the transaction id, raw hex payload, and UTF-8 rendering (best-effort) for each OP_RETURN tied to 1Feex.
3. Reviewed the resulting dataset to categorize the types of messages that have been broadcast to the address over time.

## Findings
The address exposes 67 OP_RETURN entries. Representative samples illustrate the typical patterns:

| Transaction | Message excerpt |
| --- | --- |
| `35fc15e9b5fd422d31fbd2c83de38529b15bd75e459de032f1c890d4633216e8` | `Extract Private Key using Bit-Flipping Attack on Wallet.dat` |
| `aace966bc4212e8910c3b96845776b86189ba3c4700ec9e635003b1a7926529c` | `ONot abandoned? Prove it by an on-chain transaction using private key by Sept 30` |
| `c45ad4f7ec533837c2bf68464ace6ee18a6383745495d892c99a146b20296f17` | `LEGAL NOTICE:  We have taken possession of this wallet and its contents` |
| `25e21534e2eb4763f74bcd793a6bfbe71afa54b7cc5a9c6178305c6c69ab8641` | `We'll buy your Bitcoins. sell.buy.bitcoin@protonmail.com` |
| `24ce79cd770e7b0aefd5971492ea058f5237b314088e7779b3425561f8adfc06` | `People!\nHelp!` |

The remaining messages consist mostly of promotional spam or short binary payloads. No string includes "Runestone" (hex `52756e6573746f6e65`) or even a shortened variant.

### Message category counts

| Category | Count |
| --- | --- |
| Other / promotional spam | 58 |
| Help or debt pleas | 3 |
| "Notice to owner" posts | 2 |
| Purchase offers | 2 |
| Formal legal notices | 1 |
| Bitcoin mixer advertisement | 1 |

The absence of any explicit Runestone reference strongly suggests that the rumored connection is not embedded in OP_RETURN metadata. Runestone inscriptions are Ordinals artifacts that live inside Taproot witness data, which is not surfaced by address-level OP_RETURN scans. Investigating that path would require a Taproot/Ordinals-aware indexer rather than a legacy scriptPubKey crawl.

## Next steps
- If further confirmation is required, adapt the helper to download raw transactions and inspect Taproot witness fields for inscription envelopes.
- Cross-reference the Runestone airdrop list (when accessible) to verify whether the inscription corresponding to 1Feex was delivered through witness data instead of an OP_RETURN output.
