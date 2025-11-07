# Donation & System Reliance Registry

This register collects the inflows already recorded for the Lil Footsteps
childcare treasury alongside the programs and infrastructure that depend on the
funding. It gives the team a single place to append future donations or add new
systems as they come online.

## Current donation streams

| Donation ID | Date (UTC) | Amount (USD) | Asset | Source | Memo |
| --- | --- | --- | --- | --- | --- |
| donation-2024-04-15 | 2024-04-15T17:45:00Z | 2,500 | USDC | Donor Collective | Cycle 8 general fund |
| donation-2024-05-09 | 2024-05-09T14:10:00Z | 4,200 | USDP | Employer Match Pool | Nurse shift coverage |
| donation-2024-05-28 | 2024-05-28T08:05:00Z | 3,600 | GUSD | Community Nodes | Scholarship sprint |
| donation-2024-06-04 | 2024-06-04T16:20:00Z | 5,100 | USDC | Recurring Guardians | Q2 pledge |

> **How to extend the table:** append a new row with the donation identifier,
> ISO-8601 timestamp, settled USD amount, asset, source, and memo so the
> dashboard pipeline can ingest the update.

## Systems and programs reliant on donation flow

### Treasury management
- Stablecoin allocations currently span USDC (45%), USDP (25%), GUSD (20%), and
  DAI (10%) across multi-sig custody, vaults, and on-chain reserves.
- Yield programs include Circle Yield (4.1% annualized, active) and the Aave GHO
  market (3.2%, pilot, capped at 15% of liquid treasury).
- The emergency reserve policy keeps 8% of funds locked with a 4-of-N
  multi-signature release and is reviewed monthly.

### Digital identity and wallet infrastructure
- Web3Auth wallet onboarding has reached 96 parents with a 61% custodial
  opt-in rate.
- The verifiable credential wallet PWA ships tap-to-verify QR support,
  bilingual onboarding, and offline caching with auto-sync.
- QR entry points are active at Lil Footsteps and Night Owl Childcare, with the
  community college satellite pending reactivation.

### Partnership channels
- Employers contributing via matched donations include Harbor Health (USD 12,000
  toward night-shift childcare) and Metro Transit (USD 6,500 for commute
  stipends covering childcare).
- Social service coordination runs through the Community Housing Alliance via
  API credential sharing.
- Labor and education ties include Local 404 Care Workers (emergency backup
  slots, in design) and Riverbend Community College (student parent childcare
  pass, live).

### Sustainability levers
- Recurring donation integrations are live for Stripe, Plaid, and direct smart
  contract allowances.
- The grant matching pool holds USD 28,000 and matches parent-led funds at a 2:1
  ratio.
- Treasury runway forecasts use a Monte Carlo model projecting nine months of
  coverage.

## Expansion staging area

Reserve this block for upcoming entries so the registry scales gracefully:

- [ ] New donation intake awaiting ledger confirmation
- [ ] System dependency or partnership to review
- [ ] Notes on required integrations or reporting hooks
