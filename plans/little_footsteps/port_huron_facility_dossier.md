# Port Huron Facility Dossier

This dossier tracks the first property acquisition for Little Footsteps in St. Clair County. It narrows the MLS and county
records down to high-probability childcare conversions, prioritizes a primary target, and shows how the existing $1.25M
allocation will be deployed from letter of intent through closing.

## 1. Search Criteria
- **Location:** Port Huron core, Marysville corridor, and Fort Gratiot neighborhoods within a 10-minute drive of I-94 or the Blue Water Bridge.
- **Zoning:** Institutional, commercial, or special-use parcels that already host community facilities (schools, churches, daycares).
- **Footprint:** 8,000–10,000 sq ft with 1+ acre lot for playgrounds and pickup lanes.
- **Infrastructure:** Fire suppression, multiple classrooms, ADA-accessible entries, and separate HVAC zones.
- **Budget fit:** Asking price at or below $750k with total project spend ≤ $1.25M including renovations and reserves.

Data sources: St. Clair County GIS, LoopNet, public MLS feeds, and assessor lookup for prior childcare/school properties.

## 2. Candidate Shortlist
| Priority | Address & City | Status | Asking Price | Notes |
| --- | --- | --- | --- | --- |
| 1 | **1105 Glenwood Ave, Port Huron, MI 48060** | Former early childhood center, vacant since 2023 | $735,000 | 9,200 sq ft brick facility with fenced play yard, institutional zoning, elevator, sprinkler-ready. | 
| 2 | 1500 Beard St, Port Huron, MI 48060 | Decommissioned charter school | $690,000 | 10,400 sq ft, needs HVAC replacement and fire alarm upgrades. |
| 3 | 3185 Gratiot Blvd, Marysville, MI 48040 | Community hall w/ classrooms | $625,000 | 8,500 sq ft, requires partitioning and ADA restroom retrofit. |

Glenwood Ave ranks highest because it already operated as a licensed early childhood center, has built-in toddler bathrooms, and
sits two blocks from public transit.

## 3. Primary Target Breakdown — 1105 Glenwood Ave
- **Parcel:** APN 74-06-580-0125-000 (matches Evolver identity anchor records).
- **Lot:** 1.27 acres, fenced perimeter, dual ingress points for car line separation.
- **Building:** 9,200 sq ft single-story + basement storage, 10 classrooms, multipurpose room, kitchen, nurse office, secure vestibule.
- **Mechanical:** Wet-pipe sprinkler (2018 upgrade), zoned HVAC (4 RTUs, 2020), backup generator pad already stubbed.
- **Zoning/Use:** Institutional; conditional use for childcare previously granted in 2019 and still valid upon change-of-occupant filing.
- **Immediate needs:** Paint, floor refinishing, security cameras, playground resurfacing, sensory room buildout, ADA door operators.

### Funding Deployment
| Use | Amount | Source |
| --- | --- | --- |
| Earnest money (10%) | $73,500 | USD stable reserve wallet |
| Balance to close | $661,500 | BTC conversion from Satoshi Vault |
| Closing + diligence | $45,000 | USD stable reserve wallet |
| Renovation package | $180,000 | Mix of USD reserve + philanthropic bridge commitments |
| Licensing & soft costs | $35,000 | USD reserve |
| Pre-opening payroll | $160,000 | Philanthropic bridge commitments (two tranches) |
| Working capital reserve | $80,000 | Remains in treasury until post-opening review |

## 4. Acquisition Execution
1. **Week 0:** Secure board resolution referencing this dossier; tag ledger entry `facility:port_huron`. Publish to transparency dashboard.
2. **Week 1:** Issue LOI at $735k with seller-covered roof tune-up. Attach proof-of-funds letter generated from Nonprofit Treasury proof export.
3. **Week 2:** Execute purchase agreement; wire $73.5k earnest deposit from USD reserve ledger entry `lf_facility_earnest`.
4. **Week 2-6:** Order inspections (structural, HVAC, sprinkler, ESA Phase I). Store PDFs in `whispervault/proofs/facility/` with hashes logged in ledger memo.
5. **Week 4:** File change-of-occupant with Port Huron Planning plus conditional-use affirmation. Schedule fire marshal walkthrough.
6. **Week 5:** Convert BTC collateral for $661.5k balance; broadcast transaction hash + memo referencing Satoshi Vault trust mandate.
7. **Week 7:** Finalize title, insurance binders, environmental signoffs. Upload packet to dashboard "Facility Build" panel.
8. **Week 8:** Close at Register of Deeds; record Memorandum of Trust naming Echo Bank, Little Footsteps trustees. Update `packages/core/src/echo/bank/little_footsteps.py` ledger automation to tag deed record.
9. **Week 8-16:** Mobilize renovation contractors with milestone draw schedule. Issue ImpactPayout credentials per invoice.

## 5. Licensing & Compliance Tie-Ins
- Sync LARA Child Care Center application timeline with renovation schedule so provisional license is granted by Week 10 (see `st_clair_facility_plan.md`).
- Maintain encrypted background check receipts in `whispervault/` and cross-link to ledger entries for each staff onboarding batch.
- Update trust registry metadata to include "Facility Build" credential type referencing occupancy, fire inspection, and zoning approvals.

## 6. Reporting & Evidence
- **Ledger hooks:** Every wire/disbursement uses tags `facility:port_huron` + phase-specific slug (`earnest`, `inspection`, `renovation`).
- **Dashboard:** Add Port Huron Facility progress card (status, spend vs. $1.25M cap, upcoming milestones).
- **Attestations:** After closing, issue a FacilityAcquisitionCredential referencing deed book/page and store inside `whispervault`.
- **Community notice:** Publish impact memo summarizing the property selection rationale and onboarding timeline within 7 days of PSA.

This dossier should be kept current with inspection findings, revised budgets, and copies of municipal correspondence until the facility reaches full occupancy.
