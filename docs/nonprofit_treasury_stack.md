# Nonprofit Treasury Stack

The Lil Footsteps initiative now supports an ERC-20 powered treasury that complements the existing ETH-based NonprofitBank flow. This document captures the contract, backend utilities, verifiable credential tooling, and governance prompt required to operate the stablecoin pool end-to-end.

## 1. On-Chain Contract
- Source: `contracts/NonprofitTreasury.sol`
- Token support: any ERC-20 stablecoin (USDC by default)
- Roles: default admin + treasurer (grant/revoke on-chain)
- Events:
  - `DonationReceived(donor, amount, memo)`
  - `DisbursementExecuted(beneficiary, amount, reason)`
- State tracking: `totalDonations`, `totalDisbursed`, donation log length, beneficiary wallet
- Security: custom reentrancy guard, role-restricted disbursements, zero-address validation on constructor and updates

Deploy with Hardhat/Foundry and assign the Lil Footsteps multisig as both the initial admin and treasurer. Additional treasurers can be granted via `grantRole(TREASURER_ROLE, account)` once the contract is live.

## 2. Backend Service
A new Python package powers the ledger mirroring and transaction automation:

- Module: `src/nonprofit_treasury/`
  - `TreasuryConfig`: loads RPC URL, contract, stablecoin, beneficiary, and treasurer key from env
  - `TreasuryLedger`: JSON append-only ledger capturing donations and disbursements with memos/reasons
  - `NonprofitTreasuryService`: syncs on-chain events, exposes balance/total helpers, and can execute disbursements

### Minimal usage example
```python
from pathlib import Path
from nonprofit_treasury import TreasuryConfig, NonprofitTreasuryService

config = TreasuryConfig.from_env()
config.write_snapshot(Path("ledger/nonprofit_treasury.config.json"))

service = NonprofitTreasuryService(config)
service.sync_donations(from_block=0)
service.sync_disbursements(from_block=0)
print("Treasury balance:", service.treasury_balance())
```

### Verifiable Little Footsteps treasury proof
The backend now exposes `NonprofitTreasuryService.generate_proof()` and a `proof`
CLI command that emit a signed-hash JSON snapshot. Each proof bundles the
checksummed contract, stablecoin, beneficiary wallet, live token balances, the
append-only ledger totals, and a `little_footsteps_linked` flag confirming the
contract beneficiary currently points at the Little Footsteps multisig. Run the
helper from this repository's root:

```bash
python scripts/nonprofit_treasury_backend.py proof
```

The output includes a `proof_hash` field (`sha256:<digest>`) so dashboards or
parents can recompute the canonical payload and verify the proof really ties the
treasury reserves back to Little Footsteps.

Environment variables consumed by `TreasuryConfig.from_env()`:

| Variable | Description |
| --- | --- |
| `NONPROFIT_TREASURY_RPC_URL` | HTTPS RPC endpoint |
| `NONPROFIT_TREASURY_CONTRACT` | Deployed `NonprofitTreasury` address |
| `NONPROFIT_TREASURY_STABLECOIN` | Stablecoin contract address (e.g., USDC) |
| `NONPROFIT_TREASURY_BENEFICIARY` | Little Footsteps multisig |
| `NONPROFIT_TREASURY_TREASURER_KEY` | Signing key with `TREASURER_ROLE` and admin rights |
| `NONPROFIT_TREASURY_LEDGER_PATH` *(optional)* | Custom ledger JSON location |

## 3. Donor Credential Issuance (Node + DIDKit)
The treasury service can mint verifiable credentials that recognize major donors. Install the dependencies and run the issuance helper script.

```bash
npm install didkit @digitalbazaar/jsonld jsonwebtoken
```

```javascript
// scripts/issueDonorCredential.mjs
import { issueCredential } from "@spruceid/didkit-wasm-node";
import crypto from "crypto";
import fs from "fs";

const [donorDid, amount, txHash, fiscalYear] = process.argv.slice(2);
if (!donorDid || !amount || !txHash || !fiscalYear) {
  console.error("Usage: node scripts/issueDonorCredential.mjs <donorDid> <amount> <txHash> <fiscalYear>");
  process.exit(1);
}

const issuerDid = process.env.NONPROFIT_TREASURY_ISSUER_DID;
const keyPath = process.env.NONPROFIT_TREASURY_ISSUER_KEY || "issuerKey.json";
const key = JSON.parse(fs.readFileSync(keyPath, "utf8"));

const credential = {
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://schema.org",
    "https://w3id.org/security/suites/jcs-2021/v1"
  ],
  id: `urn:uuid:${crypto.randomUUID()}`,
  type: ["VerifiableCredential", "NonprofitDonorCredential"],
  issuer: issuerDid,
  issuanceDate: new Date().toISOString(),
  credentialSubject: {
    id: donorDid,
    donation: {
      token: "USDC",
      amount,
      txHash
    },
    fiscalYear
  }
};

const options = {
  proofPurpose: "assertionMethod",
  verificationMethod: `${issuerDid}#controller`,
  proofFormat: "jwt"
};

const jwt = await issueCredential(JSON.stringify(credential), JSON.stringify(options), JSON.stringify(key));
console.log("VC (JWT):", jwt);
```

Store `issuerKey.json` in an HSM or secrets manager. Commit only the script—not the keys.

## 4. Governance Snapshot Prompt
Use the following prompt inside Snapshot, Notion, or your DAO operations interface to auto-generate the year-end disbursement report:

```
You are the treasury AI for the Digital Sovereign Nonprofit DAO.
Summarize the fiscal year ending {{date}}.

Inputs:
- On-chain donation log at contract {{address}}
- Audit report summary at {{url}}
- Impact metrics dataset at {{url2}}

Constraints:
- Highlight top 5 donor organizations and their totals.
- Report total disbursement to Little Footsteps and percentage of funds spent.
- Include compliance notes (audit outcome, policy changes, credential issuance stats).
- Tone: transparent, factual, community-facing.

Return:
1. Executive summary (<=200 words)
2. Key metrics (table)
3. Donor recognition bullets
4. Compliance & audit notes
5. CTA for next year
```

## 5. Front-End Hooks
The React donation form from the spec can live inside a Wagmi/RainbowKit powered UI. Point it at the deployed treasury contract and reuse the ABI exported from `src/nonprofit_treasury/service.py`.

```tsx
import { useState } from "react";
import { useWriteContract, useAccount } from "wagmi";
import { parseUnits } from "viem";

import treasuryAbi from "../abi/NonprofitTreasury.json"; // Generated with your build tool

export function DonateForm() {
  const [amount, setAmount] = useState("");
  const [memo, setMemo] = useState("");
  const { address } = useAccount();

  const { writeContract, isPending, isSuccess, error } = useWriteContract({
    address: "0xTreasuryAddress",
    abi: treasuryAbi,
    functionName: "donate"
  });

  return (
    <form
      onSubmit={async (event) => {
        event.preventDefault();
        await writeContract({
          args: [parseUnits(amount, 6), memo]
        });
      }}
      className="donate-form"
    >
      <label>Amount (USDC)</label>
      <input type="number" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} required />
      <label>Memo (optional)</label>
      <input value={memo} onChange={(e) => setMemo(e.target.value)} />
      <button type="submit" disabled={isPending || !address}>
        {isPending ? "Processing..." : "Donate"}
      </button>
      {isSuccess && <p>Donation submitted!</p>}
      {error && <p className="error">{error.shortMessage}</p>}
    </form>
  );
}
```

Include a credential verification widget that hits the Node issuance API to confirm donor credentials.
