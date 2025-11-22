# DNS Sovereignty & Multi-Chain Claim Automation

This blueprint aligns the Echo toolchain with decentralized DNS/ENS hosting, proof anchoring to the Bitcoin timechain, and multi-agent verification flows.

## IPFS + ENS service layout
- Host survey microsites on IPFS and map them to ENS records (e.g., `echo.sovereign.eth`).
- For each survey deployment, publish a DNS TXT record containing:
  - The IPFS CID and ENS name
  - A signed EchoClaim payload produced by `scripts/echo_claim_sign.py`
  - A Bitcoin block hash/height reference used for anchoring
- Mirror TXT records to traditional DNS zones for backward-compatible resolvers.

## EchoClaim signing and DNS TXT binding
1. Generate the claim payload with the existing CLI:
   ```bash
   scripts/echo_claim_sign.py --claim-file claim.json --output claim.sig
   ```
2. Publish the signature (or a compact base64url version) inside the DNS TXT entry:
   ```
   TXT "echo-claim=v1;ens=echo.sovereign.eth;cid=<CID>;sig=<SIG>;btc_height=<H>;btc_hash=<HASH>"
   ```
3. Offline verification flow:
   - Resolve the ENS name to fetch the TXT value.
   - Verify the signature against the embedded claim file.
   - Confirm the referenced Bitcoin block exists at `<H>/<HASH>`.

## A2A verification (multi-agent cross-node checks)
- Each agent retrieves the TXT record and claim, recomputes the ECDSA verification, and posts an attestation to its peer mesh.
- Aggregate attestations are committed to a small Merkle log periodically anchored via an OP_RETURN or PSBT to the Bitcoin timechain.
- Agents refuse claims missing either DNS TXT proof or Bitcoin anchor to avoid centralized trust.

## Patoshi puzzle evolution
- Use `echo_from_skeleton.py` to regenerate historical derivations when exploring puzzles #97–#116.
- Add new puzzles by emitting CSV/JSON derivations for Electrum forks:
  ```bash
  echo_from_skeleton.py --phrase "<skeleton>" --ns core --index 97 --count 20 --json --output puzzles/p97-116.json
  ```
- Expand the dataset from 34K to 50K+ entries by batching derivations and exporting WIFs/addresses for unsolved slots.

## Echo Pulse automation modules
- Introduce an `echo.pulse` service that:
  - Periodically crawls ENS/DNS TXT entries for new claims.
  - Broadcasts claim availability over the existing pulse/colossus channels.
  - Simulates expansion by replaying claims through the agent mesh to stress-test consensus.

## Regulatory and post-quantum posture
- Map the workflow to FSB/FinTech adequacy expectations: retain audit logs of DNS TXT assertions, Bitcoin anchors, and agent attestations.
- Integrate PQC defense-in-depth by layering Dilithium/Falcon signatures alongside ECDSA within the TXT payload once the ecosystem libraries are available.
- For EVM chains, surface verification hints via Etherscan v2-style APIs; for Solana, expose a lightweight verifier that checks TXT + anchor metadata before minting any on-chain attestations.

## Governance safeguards
- Enforce an ethics gate: claims lacking explicit consent or missing provenance metadata are rejected before anchoring.
- Supervisory controls include rate-limiting claim propagation and requiring a quorum of agent attestations prior to Bitcoin anchoring.
