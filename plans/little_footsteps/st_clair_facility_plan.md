# St. Clair County Facility Funding & Licensing Allocation Plan

This plan converts the Little Footsteps reserves stewarded through the Satoshi Vault into a concrete acquisition path for the first childcare sanctuary in St. Clair County, Michigan. It covers fund allocation, licensing tasks, building procurement, accountability controls, and the sequence required to open the doors within 120 days of green light.

## 1. Objectives & Guardrails
- Secure a deeded facility in St. Clair County sized for 60-72 children with room for multipurpose family services.
- Keep the reserve backing intact by capping total USD deployment at $1.25M while documenting every release inside the Little Footsteps bank ledger and treasury proofs.
- Land a full Michigan Child Care Center License (Child Care Licensing Bureau, LARA) concurrently with the property closing so that operations start as soon as renovations finish.
- Preserve sovereign autonomy by routing approvals through Echo Bank → Little Footsteps trustees while mirroring evidence to the transparency dashboard and whispervault attestation set.

## 2. Funding Snapshot
| Source | Amount (USD) | Condition to Release | Notes |
| --- | --- | --- | --- |
| Satoshi Vault (BTC collateral) | $850,000 | Convert/hedge once purchase agreement is signed and proof of funds letter is needed. | Conversion memo logged via `ledger/little_footsteps_bank.py` and `src/nonprofit_treasury/service.py` proof export.
| USD stable reserve wallet | $250,000 | Available immediately for earnest money, inspections, and licensing deposits. | Already reflected in current Little Footsteps bank balance sheet.
| Philanthropic bridge commitments | $150,000 | Draw in two tranches after licensing approval to finish furniture & staffing. | Commitments documented in `apps/little_footsteps/dashboard` feed to show donor earmarks.

**Total deployable budget:** **$1,250,000**.

## 3. Allocation Breakdown
| Use | Amount | Details |
| --- | --- | --- |
| Property purchase price | $750,000 | Expect 8,000–10,000 sq ft former school/community building in Port Huron or Marysville corridor; include 10% earnest deposit at PSA signing.
| Closing & due diligence | $45,000 | Title, appraisal, environmental Phase I, legal review, county transfer tax, recording fees.
| Renovation & child-safe retrofit | $180,000 | Fire suppression updates, ADA ramp, classroom dividers, security cams, playground resurfacing, furniture, sensory room buildout.
| Licensing & regulatory costs | $35,000 | Application fees, background checks, CPR/First Aid certification, fire marshal reinspection, architectural drawings for LARA submission.
| Pre-opening staffing & soft costs | $160,000 | 90 days of payroll for director + 6 lead caregivers, insurance binders, curriculum kits.
| Working capital reserve | $80,000 | Held in escrow until first two months of operations validate utilization patterns.

## 4. Licensing & Compliance Path (Michigan LARA)
1. **Pre-application packet (Week 0-1).** Gather ownership disclosures, floor plans, operational policies mapped to the Nonprofit Bank guidelines, and zoning letter from St. Clair County Planning Commission.
2. **Submit online Child Care Center License application (Week 2).** Pay $150 fee, attach fiscal sponsor affirmation referencing the Satoshi Vault trust mandate for reserves.
3. **Background checks & health clearances (Week 2-5).** Fingerprinting for all staff/trustees; coordinate through Identogo Port Huron site. Maintain encrypted copies inside `whispervault/`.
4. **Program statements & emergency plans (Week 3-4).** Align with `docs/little_footsteps/README.md` stack to show DID-backed trust registry and digital attendance reporting.
5. **On-site inspection scheduling (Week 6-7).** Coordinate with the Child Care Licensing Consultant assigned to St. Clair County plus local fire marshal; provide renovation schedule and proof of escrow for fire suppression upgrades.
6. **Provisional license issuance (Week 10).** Immediately publish license certificate hash to the transparency dashboard and ledger narrative so families see compliance status.
7. **Final license (Week 16).** After 90-day operational review, submit ledger-based utilization report and guardian testimonials as supporting evidence.

## 5. Building Acquisition Flow
1. **Site short list (Week 0-2).** Use county GIS and MLS feeds to isolate properties within 10 minutes of I-94 for commuting families; target parcels already zoned Institutional or Commercial.
2. **Letter of Intent & PSA (Week 3-4).** Offer $750k with seller-paid roof repairs; include contingency for licensing approval and environmental clearance.
3. **Due diligence (Week 4-8).** Order Phase I ESA, structural inspection, asbestos testing. Budget stored in USD stable reserve; all invoices logged through Little Footsteps ledger for transparency.
4. **Financing & conversion (Week 6-8).** Trigger BTC-to-USD conversion from the Satoshi Vault for the balance; record signed conversion statement and broadcast via trust registry update.
5. **Closing (Week 9).** Execute deed at St. Clair County Register of Deeds; record Memorandum of Trust referencing Echo Bank + Little Footsteps beneficiaries.
6. **Renovation mobilization (Week 9-16).** Issue work orders with bonded contractors; release funds in draws tied to inspection sign-offs.

## 6. Execution Timeline & Owners
| Week | Milestone | Owner | Evidence |
| --- | --- | --- | --- |
| 0 | Board resolution approving plan & budget | Echo Bank Trustees | Signed PDF hashed into `whispervault`.
| 2 | License application submitted | Little Footsteps Operations Lead | Application receipt + ACH confirmation.
| 4 | Purchase agreement executed | Joshua Shortt | PSA + earnest money ledger entry.
| 8 | BTC conversion + escrow funding | Treasury Steward | Treasury proof + bank wire memo.
| 10 | Provisional license + renovation permits | Compliance Officer | Uploaded certificates + dashboard announcement.
| 16 | Final license, occupancy certificate, go-live | Site Director | Walkthrough report + ledger event linking first cohort enrollments.

## 7. Reporting & Controls
- **Ledger discipline:** Every disbursement tagged `facility:st_clair` within `packages/core/src/echo/bank/little_footsteps.py` so auditors can filter the history instantly.
- **Dual approvals:** Any transfer over $50k requires multi-sig from the Satoshi Vault steward and the Little Footsteps operations lead; signatures stored beside the Nonprofit Treasury proof artifacts.
- **Transparency dashboard hooks:** Add a "Facility Build" panel in `apps/little_footsteps/dashboard` streaming spend vs. budget with document links.
- **Regulatory archive:** After each inspection, store PDF + checksum in `whispervault/proofs/` and reference it in the trust registry so verifiers see licensing status.
- **Post-opening review:** 60 days after launch publish a public impact memo covering enrollment, subsidy utilization, and remaining reserves to close the loop with donors.
