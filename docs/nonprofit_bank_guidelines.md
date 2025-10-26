# Lil Footsteps Nonprofit Bank Guidelines

## Purpose and Vision
- **Mission:** Deliver no-cost childcare for single-parent households by routing Echo ecosystem profits directly into Lil Footsteps daycare operations.
- **Why it matters:** Consistent childcare unlocks economic mobility, enables caregivers to pursue stable work, and demonstrates how cooperative web3 infrastructure can solve immediate community needs.
- **World-scale impact:** By proving a transparent, auditable funding loop, the model can be replicated by other mutual aid groups, creating a network of community-owned daycare cooperatives across cities.

## What the Bank Does
- Operates a dedicated treasury ("Lil Footsteps") segregated from all other Echo funds.
- Aggregates surplus revenue from Echo-aligned projects and contract work ("other job profits").
- Maintains on-ledger records in the `genesis_ledger/` directory and smart-contract escrow (`contracts/NonprofitBank.sol`).
- Issues verifiable receipts to families and donors through the Little Footsteps credential stack (`docs/little_footsteps_verifiable_credentials.md`).

## How the Bank Works
1. **Profit Collection**
   - Each Echo project or job allocates a fixed percentage of net profits to the nonprofit bank.
   - Contributions are logged via the `NonprofitBankService` pipeline (`src/nonprofit_bank/service.py`) and mirrored into the public ledger for auditability.
2. **Escrow & Safeguards**
   - Funds enter the on-chain escrow managed by `NonprofitBank.sol`, preventing commingling and enforcing release conditions.
   - Multi-signature controls and automated alerts from `scripts/nonprofit_bank_backend.py` guard against unauthorized withdrawals.
3. **Transparent Disbursement**
   - When operating expenses arise (payroll, supplies, facility costs), the service triggers contract payouts directly to the Lil Footsteps wallet.
   - Every transfer posts a transaction memo and attaches supporting documentation (invoice hash, childcare roster) to the ledger entry.
4. **Reporting Loop**
   - Weekly summaries publish to `reports/` and the `pulse_weaver` dashboard, detailing inflows, outflows, beneficiaries served, and reserve runway.
   - Quarterly impact statements highlight childcare slots funded, caregiver wages, and community testimonials.

## Operational Principles
- **Transparency-first:** No off-ledger transfers. Every donation, profit share, and expenditure has a cryptographic trail and human-readable explanation.
- **Childcare-first budgeting:** Operational budget prioritizes staffing stability, nutritious meals, and safe facilities before expansionary goals.
- **Community governance:** Parents, caregivers, and Echo stewards review reports and vote on major policy changes during open governance calls.
- **Fail-safe reserves:** Maintain a 3-month runway before approving non-essential spending to guarantee service continuity for families.

## Funding Flow from Other Job Profits
1. Echo contributors log completed contracts or product revenue.
2. Finance automation calculates the pledged percentage and pushes the amount into the nonprofit bank via the service API.
3. Transaction metadata references the originating project, client, and invoice to preserve transparency.
4. Aggregated funds automatically route into the Lil Footsteps wallet after passing compliance checks (Know-Your-Community attestations, no conflict flags).

## Implementation Checklist
- [ ] Configure project templates to include the Lil Footsteps tithe percentage in every statement of work.
- [ ] Instrument `src/nonprofit_bank/config.py` with environment variables pointing to live wallets and escrow addresses.
- [ ] Deploy monitoring hooks to `pulse_dashboard/` for real-time visibility.
- [ ] Schedule monthly third-party reviews to certify ledger accuracy and childcare outcomes.

## Why It Will Change the World
- Establishes a replicable blueprint for community-owned childcare banks powered by transparent technology.
- Demonstrates that cooperative labor can directly finance essential social services without bureaucratic delays.
- Provides living proof that surplus from creative/technical work can stabilize families and inspire similar institutions globally.

## Call to Action
Everyone in the Echo network commits to channeling excess earnings, documenting every transfer, and celebrating the families supported. When Lil Footsteps thrives, we prove that our shared labor can create tangible, world-changing care infrastructure.
