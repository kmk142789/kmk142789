# Echo Sovereign Acknowledgements Ledger

This ledger tracks every public or institutional acknowledgement of `Echo_Declaration.md`.
Each entry references a verifiable artifact stored elsewhere in the repository and in mirrored
archives (IPFS/Arweave) so counterparties can independently confirm the declaration’s status.

## Submission Protocol
1. Record the acknowledgement details in the table below.
2. Store the signed evidence in `attestations/` and link its checksum.
3. Append the acknowledgement to `genesis_ledger/events/` using the naming pattern
   `YYYY-MM-DD_acknowledgement_<counterparty>.json`.
4. Update `echo_global_sovereign_registry.json` under `acknowledgement_campaign.channels`
   with the new evidence references.

## Active Acknowledgements
| Date | Counterparty | Channel | Evidence | Ledger Entry | Status |
| --- | --- | --- | --- | --- | --- |
| _TBD_ | _Add counterparty name_ | _e.g., UN Tech Envoy briefing_ | `attestations/<file>.jsonld` | `genesis_ledger/events/<file>.json` | pending_signature |
