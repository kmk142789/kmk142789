# Little Footsteps — Next Steps Aligned to the Sovereign Trust

These steps keep the Little Footsteps childcare stack in lock-step with the Sovereign Trust posture and the Satoshi Vault backing.

## 1) Publish the vault proof and mirror it to the registry
- Finalize the current Satoshi Vault reserve hash and publish it under `attestations/` with a matching entry in `genesis_ledger/`.
- Add the attestation pointer to `docs/little_footsteps/trust_registry.json` and surface the hash on the transparency dashboard.
- Notify the Sovereign Trust registry maintainers so the vault proof can be referenced in `sovereign_trust_registry.json`.

## 2) Pin the issuer DID to the Sovereign Trust root
- Confirm the `did:web:kmk142789.github.io:little-footsteps-bank` document resolves to the same root controller referenced in `Sovereign_Trust_Root.md`.
- Capture the verification in an attestation that chains to `ECHO-ROOT-2025-05-11` and store it alongside the vault proof.
- Once published, mirror the DID check into the pulse dashboard so verifiers can see the sovereign anchor without reading the repo.

## 3) Connect treasury transparency to the Sovereign Digital Trust ingest
- When the first verified wallet tranches land, run `python tools/sdt_pipeline_register.py --require-complete` and record the output hash in a Little Footsteps transparency log entry.
- Update the Little Footsteps transparency dashboard to link the Sovereign Digital Trust ingest state (pending → partial → complete).
- Ensure any reinvestment yield entries in the bank ledger continue to route back into Little Footsteps destinations to stay compliant with `NonprofitBankStructure.reinvestment_actions`.
