# Lil Footsteps Treasury Hardening & Scale Blueprint

This playbook extends the Lil Footsteps childcare treasury by wiring in automation, compliance, and analytics layers that keep the bank solvent while it grows. Every recommendation maps back to code or processes inside this repository so the Echo collective can implement in phases.

## 1. Expanded On-Chain Architecture

### 1.1 Streamed Disbursement Contract
- Replace lump-sum payouts with continuous releases so finance stewards can pause funding if risk signals appear.
- Superfluid or Sablier integrations are viable, but a lightweight contract keeps the stack self-hosted. Start from the `contracts/NonprofitBank.sol` escrow and forward allocations into a streaming module:

```solidity
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract StreamDisburser is AccessControl {
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    IERC20 public stablecoin;

    struct Stream {
        uint256 totalAmount;
        uint256 startTime;
        uint256 endTime;
        uint256 withdrawn;
        bool paused;
    }

    mapping(address => Stream) public streams;

    event StreamCreated(address indexed beneficiary, uint256 amount, uint256 start, uint256 end);
    event StreamWithdrawn(address indexed beneficiary, uint256 amount);
    event StreamPaused(address indexed beneficiary, bool paused);

    constructor(address admin, IERC20 token) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(PAUSER_ROLE, admin);
        stablecoin = token;
    }

    function createStream(
        address beneficiary,
        uint256 amount,
        uint256 durationSeconds
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(beneficiary != address(0), "bad beneficiary");
        require(durationSeconds > 0, "duration zero");
        stablecoin.transferFrom(msg.sender, address(this), amount);

        streams[beneficiary] = Stream({
            totalAmount: amount,
            startTime: block.timestamp,
            endTime: block.timestamp + durationSeconds,
            withdrawn: 0,
            paused: false
        });

        emit StreamCreated(beneficiary, amount, block.timestamp, block.timestamp + durationSeconds);
    }

    function withdraw() external {
        Stream storage s = streams[msg.sender];
        require(!s.paused, "stream paused");
        require(s.totalAmount > 0, "no stream");

        uint256 elapsed = block.timestamp > s.endTime ? s.endTime - s.startTime : block.timestamp - s.startTime;
        uint256 vested = (s.totalAmount * elapsed) / (s.endTime - s.startTime);
        uint256 withdrawable = vested - s.withdrawn;
        require(withdrawable > 0, "nothing to withdraw");

        s.withdrawn += withdrawable;
        stablecoin.transfer(msg.sender, withdrawable);

        emit StreamWithdrawn(msg.sender, withdrawable);
    }

    function setPaused(address beneficiary, bool paused)
        external
        onlyRole(PAUSER_ROLE)
    {
        Stream storage s = streams[beneficiary];
        require(s.totalAmount > 0, "no stream");
        s.paused = paused;
        emit StreamPaused(beneficiary, paused);
    }
}
```

- Pipe treasury decisions from the DAO multisig into `createStream`. If compliance flags appear, call `setPaused` before the next `withdraw()` accrues.
- Track deployed stream addresses and configuration inside `ledger/nonprofit_bank_ledger.json`.

### 1.2 Streaming Operations
- Add CLI helpers (`scripts/nonprofit_bank_backend.py`) to open, top-up, pause, or close a stream.
- Surface live withdrawable balances in the provider dashboard (see section 7) so daycare admins know how much runway is available.

## 2. DAO Governance Enhancements

### 2.1 Snapshot Strategy Template
Use a mixed-strategy Snapshot configuration so governance combines treasury token votes with credential-gated participation (e.g., only registered caregivers weigh in on staffing KPIs).

```json
{
  "name": "Nonprofit Treasury Voting Strategy",
  "params": {
    "symbol": "NPT",
    "decimals": 18,
    "strategies": [
      {
        "name": "erc20-balance-of",
        "params": {
          "address": "0xGovernanceTokenAddress"
        }
      },
      {
        "name": "erc1155-balance-of",
        "params": {
          "address": "0xCredentialNFT",
          "tokenId": "1"
        }
      }
    ],
    "tokenMetadata": {
      "symbol": "NPT",
      "name": "Nonprofit Participation Token"
    }
  }
}
```

- Store the canonical JSON in `governance/` and reference it in Snapshot spaces or Station proposals.

### 2.2 Governance Summaries
- Run governance proposals through `pulse_weaver` with an AI summarizer prompt:

```
You summarize governance proposal {{proposal_id}}.
Inputs: proposal text, debates, on-chain data (Gnosis Safe transactions).
Output:
- What the proposal does
- Financial impact (USD + token)
- Risk assessment (low/med/high, with reason)
- Compliance impact (licenses needed, new KYC requirements)
Concise, bullet style.
```

- Archive outputs to `reports/governance/` for historical traceability.

## 3. Parent & Provider Credentialing

### 3.1 Eligibility Schema
Add a JSON-LD schema under `schemas/` to standardize parent eligibility attestations:

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://schema.org",
    {
      "ParentEligibilityCredential": "https://example.org/credentials#ParentEligibilityCredential",
      "childName": "schema:name",
      "supportingDocumentsHash": "schema:identifier",
      "eligibleFrom": "schema:validFrom",
      "eligibleTo": "schema:validThrough",
      "incomeBracket": "schema:QuantitativeValue"
    }
  ],
  "type": "ParentEligibilityCredential"
}
```

### 3.2 Issuance Script
- Extend the existing VC issuer service (FastAPI or Node) with a helper that produces the credential payload:

```javascript
const eligibilityCredential = {
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://example.org/credentials/parentEligibility/v1"
  ],
  id: "urn:uuid:" + crypto.randomUUID(),
  type: ["VerifiableCredential", "ParentEligibilityCredential"],
  issuer: did,
  issuanceDate: new Date().toISOString(),
  credentialSubject: {
    id: parentDid,
    childName: "A.B.",
    eligibleFrom: "2024-01-01",
    eligibleTo: "2024-12-31",
    incomeBracket: {
      "@type": "QuantitativeValue",
      "minValue": 0,
      "maxValue": 25000,
      "unitCode": "USD"
    },
    supportingDocumentsHash: "ipfs://bafy..."
  }
};
```

- Publish revocation lists using StatusList2021 or RevocationList2020 so staff can invalidate credentials if eligibility changes.

## 4. Compliance Automation

### 4.1 Transaction Monitoring
- Stream blockchain events (Alchemy, Infura, or Tenderly websockets) into AWS Lambda.
- Enrich each transaction with third-party risk data (Chainalysis, TRM).
- Persist results in DynamoDB and trigger manual review when the risk score crosses the threshold.

```javascript
import { DynamoDBClient, PutItemCommand } from "@aws-sdk/client-dynamodb";
import axios from "axios";

const client = new DynamoDBClient({ region: "us-east-1" });
const RISK_THRESHOLD = 70;

export const handler = async (event) => {
  const { transactionHash, donorAddress, amount } = JSON.parse(event.body);

  const riskResp = await axios.post("https://api.chainalysis.com/risk", {
    address: donorAddress
  }, { headers: { "X-API-Key": process.env.CHAINALYSIS_KEY } });

  const riskScore = riskResp.data.score;

  await client.send(new PutItemCommand({
    TableName: process.env.TRANSACTION_TABLE,
    Item: {
      transactionHash: { S: transactionHash },
      donorAddress: { S: donorAddress },
      amount: { N: amount.toString() },
      riskScore: { N: riskScore.toString() },
      flagged: { BOOL: riskScore >= RISK_THRESHOLD }
    }
  }));

  if (riskScore >= RISK_THRESHOLD) {
    // Optionally call contract function to pause stream
    await axios.post(
      process.env.COMPLIANCE_CHANNEL_WEBHOOK,
      {
        text: `Little Footsteps alert – donor ${donorAddress} scored ${riskScore} on the latest transfer (${amount} USDC). Review and confirm treasury pause status.`,
      },
      { timeout: 5000 }
    );
  }

  return { statusCode: 200, body: JSON.stringify({ status: "ok", riskScore }) };
};
```

- When a flag fires, call the streaming contract's `setPaused` function and notify the compliance Matrix/Slack channel.
- Provision a `COMPLIANCE_CHANNEL_WEBHOOK` secret per environment (Matrix, Slack, or Discord incoming webhook) so the Lambda can deliver the alert payload without leaking credentials.

### 4.2 Reporting
- Generate daily summaries using scheduled Lambdas or GitHub Actions that compile flagged addresses, total volume, and status updates.
- Ship monthly PDF compliance packets to `reports/compliance/` for board review.

## 5. Observability & Security

### 5.1 Contract Observability
- Configure Tenderly or OpenZeppelin Defender Sentinel to monitor `StreamDisburser` and `NonprofitBank.sol` events.
- Example sentinel: trigger on `DisbursementExecuted` or `StreamWithdrawn` where the amount exceeds 10,000 USDC and push alerts to `#treasury-compliance`.

### 5.2 Key Management
- Custody multisig and issuer keys in hardware-backed vaults (AWS KMS, Ledger Enterprise, Fireblocks).
- Maintain Gnosis Safe thresholds (e.g., 4-of-7) and document key ceremonies in `SECURITY.md`.

### 5.3 Threat Modeling
- Run recurring workshops using the following prompt to generate STRIDE tables:

```
You are the security architect. Threat-model the Nonprofit Treasury system.
Context: smart contracts (Solidity), Node.js API, parent portal web app, AWS infra.
Identify STRIDE-style threats, prioritize by likelihood/impact, propose mitigations.
Deliverable: markdown table with columns [Threat, Component, Likelihood, Impact, Mitigation].
```

- Store outputs in `security/threat_models/`.

## 6. Data & Impact Analytics

### 6.1 Warehouse Pipeline
- Source data: smart-contract events (via The Graph), childcare provider rosters, credential issuance logs.
- Ingest with Airbyte or Fivetran into BigQuery/Snowflake, then transform via dbt.
- Build dashboards in Metabase, Superset, or Looker with granular access controls.

### 6.2 dbt Model Pattern

```sql
-- models/metrics_childcare_impact.sql
with sessions as (
  select
    child_id,
    parent_id,
    provider_id,
    session_date,
    hours
  from {{ ref('stg_childcare_sessions') }}
),

disbursements as (
  select
    beneficiary,
    amount_usdc,
    disbursement_time
  from {{ ref('stg_disbursements') }}
)

select
  provider_id,
  count(distinct child_id) as children_served,
  sum(hours) as total_hours,
  sum(hours) / count(distinct child_id) as avg_hours_per_child,
  sum(amount_usdc) filter (where sessions.provider_id = disbursements.beneficiary) as allocated_usdc
from sessions
left join disbursements
  on sessions.provider_id = disbursements.beneficiary
group by provider_id;
```

- Publish derived metrics to `pulse_dashboard/` so community stakeholders can inspect utilization trends.

## 7. Parent & Provider Applications

### 7.1 Parent Enrollment Portal
- Intake flow: parents upload documents → staff verifies → click "Issue Credential" to mint the VC via the issuer service.
- React hook example (placed in `apps/parent-portal/src/hooks/`):

```tsx
const { data: vcStatus } = useQuery({
  queryKey: ["vcStatus", parentDid],
  queryFn: async () => {
    const resp = await fetch(`/api/v1/credentials/status?did=${parentDid}`);
    return resp.json();
  },
  refetchInterval: 60000
});
```

### 7.2 Provider Dashboard
- Display live stream balances by querying `streams[provider]` from the disbursement contract.
- Provide upload forms for compliance artifacts (licenses, insurance) and send automated reminders ahead of expiry.

## 8. Documentation & Process

### 8.1 README Template
Use the following outline when updating `README.md` or onboarding derivatives:

```
# Digital Sovereign Nonprofit Treasury

## Overview
- Mission
- Architecture diagram
- Contact & escalation list

## Smart Contracts
- Treasury (address, etherscan link)
- StreamDisburser (address)
- Governance token (address)
- Audit reports (link)

## Off-Chain Services
- VC Issuer (endpoint, DID)
- Compliance monitoring (lambda)
- Data warehouse (BigQuery dataset)

## Runbook
- Deploy instructions (Hardhat scripts)
- Key rotation procedure
- Incident response (24/7 on-call contacts)
- Annual audit checklist
```

### 8.2 Onboarding Checklist

```
- [ ] Sign contributor agreement / code of conduct
- [ ] Receive key management training
- [ ] Add to Gnosis Safe (if board)
- [ ] Add to Slack + Notion + compliance tooling
- [ ] Awareness session on childcare regulations
```

- Store checklists under `docs/onboarding/` for quick access.

## 9. External Integrations & Partnerships
- Payment processors: Stripe Climate, The Giving Block, BitPay for multi-currency intake and auto-stablecoin conversion.
- Insurance: ensure nonprofit liability and childcare-specific errors & omissions policies stay current.
- Government alignment: map processes to local childcare subsidy programs to ease future interoperability.
- Auditors: engage smart-contract auditors (Quantstamp, OpenZeppelin) and nonprofit CPA firms annually.
- Legal: retain counsel familiar with digital asset compliance and nonprofit law (e.g., ArentFox, Perkins Coie, Orrick).

## 10. Roadmap Snapshot

| Phase | Focus | Key Deliverables |
|-------|-------|------------------|
| Month 0-2 | Security hardening | Contract audit, key management, threat model |
| Month 3-4 | Compliance | Automated AML checks, updated policies, VC revocation |
| Month 5-6 | Parent & Provider UX | Enrollment portal, credential issuance UI |
| Month 7-8 | Analytics & Reporting | dbt models, dashboard, annual impact report automation |
| Month 9+ | Scale & Partnerships | Onboard more nonprofits, cross-chain support, grant matching |

## 11. Optional Advanced Concepts
- Zero-knowledge attestations: apply zk-SNARK proofs (Noir, zkSync, Aztec) to verify aggregate donations without revealing donors.
- Quadratic funding: match grants based on community support signals.
- Resilience: mirror critical docs and dashboards on IPFS/Filecoin/Arweave for censorship resistance.
- AI screening: use LLMs to pre-screen grant proposals against compliance checklists with human review.
- Interoperability: enable DID-based SSO so parents can unlock benefits with partner organizations (food banks, job centers).

## 12. Operational Checklists

### 12.1 Security
- [ ] Multi-sig with hardware keys
- [ ] Smart contract audit
- [ ] Monitoring alerts configured
- [ ] Incident response doc published

### 12.2 Compliance
- [ ] AML/KYC workflow live
- [ ] Credential status list (issuance & revocation) maintained
- [ ] Annual filings & audits scheduled
- [ ] Data privacy policy (GDPR/CCPA) enforced

### 12.3 Operations
- [ ] Parent/provider onboarding scripts documented
- [ ] Disbursement calendar published (pause controls tested)
- [ ] Impact metrics pipeline active
- [ ] Annual report template updated for transparency

---

Use this blueprint as a living document—update sections after each deployment, audit, or partnership milestone so Lil Footsteps always has a current map from treasury to childcare outcomes.
