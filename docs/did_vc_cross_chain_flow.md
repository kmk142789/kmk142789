# Cross-Chain DID/VC Data Flow Blueprint

## Overview
This blueprint maps the flow of decentralized identifiers (DIDs) and verifiable credentials (VCs) across Ethereum (EIP-712/EIP-155), Solana (Ed25519), and Bitcoin Ordinals inscriptions. It specifies the trust-minimized relay and verification mechanisms, delineates the on-chain/off-chain responsibilities, describes interoperable message formats, and prescribes a cross-chain anchoring cadence. Privacy, key management, and replay protection considerations are embedded throughout the design.

---

## 1. Network Roles and Components

### 1.1 Off-Chain Agents
- **Issuer Agent**: Maintains DID keys, prepares VCs, and submits anchor commitments.
- **Holder Agent**: Stores VCs, requests proofs, and mediates cross-chain attestations.
- **Verifier Agent**: Requests proofs, verifies cross-chain evidence, and optionally publishes verification receipts.
- **Relay/Proof Service**: Constructs zero-knowledge proofs (ZKPs) or hash attestations to bridge state between chains without custodial trust.

### 1.2 On-Chain Contracts and Programs
- **Ethereum**
  - *Registry Contract*: Stores DID document hash, VC commitment Merkle roots, and verification receipts (EIP-155 transactions).
  - *Verification Contract*: Verifies EIP-712 typed data signatures and ZKPs.
- **Solana**
  - *Program PDA (Program-Derived Address)*: Holds DID metadata and Merkle commitments with Ed25519 signature verification.
  - *Cross-Chain Proof Account*: Temporary account for ZKP/hash proof material and state transition data.
- **Bitcoin (Ordinals)**
  - *Inscription Payload*: Contains immutable DID/VC commitment hashes, anchor identifiers, and optional script paths for verification.
  - *Taproot Script Path*: Enforces spending conditions for updates or revocations by embedding hash preimages.

---

## 2. DID & VC Lifecycle Data Flow

### 2.1 DID Creation
1. **Key Generation**
   - Ethereum: secp256k1 key with EIP-155 chain-id binding.
   - Solana: Ed25519 key pair.
   - Bitcoin: Taproot key pair (internal key with optional script path).
2. **DID Document Assembly**
   - JSON-LD / DID Core document with verification methods for each chain.
3. **Anchoring**
   - Publish DID doc hash commitments:
     - Ethereum registry `registerDID(hash, chainId)`.
     - Solana PDA writes DID state via `init_did` instruction.
     - Bitcoin Ordinal inscription with `did:<id>` metadata in the envelope.

### 2.2 VC Issuance
1. Issuer agent prepares credential subject data off-chain.
2. Construct Merkle tree of VC attributes; generate root `R`.
3. Sign typed data per chain:
   - Ethereum: EIP-712 `CredentialOffer` message, hashed with domain separator using EIP-155 chain id.
   - Solana: Canonical serialized `CredentialOffer` structure; sign with Ed25519.
   - Bitcoin: Hash commitment `H = SHA256(R || nonce)` embedded in inscription.
4. Store `R` and credential metadata in respective on-chain components.

### 2.3 Presentation & Verification
1. Holder derives selective disclosure proof (Merkle path + ZKP).
2. Relay service constructs chain-specific proof package:
   - Ethereum: ZKP proof `π_eth` verifying credential validity and freshness against on-chain root.
   - Solana: ZKP proof `π_sol` or Ed25519 signature verification proof referencing Solana account state.
   - Bitcoin: Hash preimage or inclusion proof referencing ordinal inscription index and transaction witness.
3. Verifier receives `CrossChainProof` message (see §4) and validates via respective on-chain verification endpoints or off-chain proof verification circuits.
4. Optional: Verifier anchors verification receipt (hash of verified claim + timestamp) on preferred chain.

---

## 3. Trust-Minimized Relay & Verification

### 3.1 Zero-Knowledge Proof Relay
- Use zk-SNARK/zk-STARK circuits to prove statements such as:
  - `Credential signature is valid under issuer key stored on Ethereum registry.`
  - `Solana account data at slot s contains Merkle root R for credential.`
  - `Bitcoin inscription #n references hash commitment H = Poseidon(R || nonce).`
- Relay service publishes proof commitments on IPFS/Arweave with content-addressed identifiers.
- On-chain verification contracts/programs expose `verifyZKProof(π, publicInputs)` that accept proof bytes and anchor IDs.

### 3.2 Hash-Based Attestation Fallback
- When ZKP cost is prohibitive, relay posts hash attestations:
  - Ethereum: `postAttestation(anchorId, hashProof)` event emitted by registry contract.
  - Solana: Relay signs `AttestationMessage` with its DID; verifiers check signatures and compare against hash in Ethereum receipt.
  - Bitcoin: `OP_RETURN` or Taproot annex with `H_attest = SHA256(anchorId || chainId || proofHash)`.
- Cross-chain consensus achieved by requiring a threshold (e.g., ⅔) of independent relays to sign the same hash commitment before acceptance.

---

## 4. Message Formats

### 4.1 Credential Offer (Off-Chain JSON)
```json
{
  "type": "CredentialOffer",
  "issuer": "did:example:issuer",
  "subject": "did:example:holder",
  "credentialSchema": "https://schema.org/EducationalCredential",
  "merkleRoot": "0x...",
  "issuanceDate": "2025-05-11T00:00:00Z",
  "expiry": "2026-05-11T00:00:00Z",
  "nonce": "0xnonce"
}
```

### 4.2 CrossChainProof Envelope
```json
{
  "credentialId": "cred-123",
  "anchorRefs": [
    {"chain": "ethereum", "txHash": "0x...", "blockNumber": 19200000},
    {"chain": "solana", "slot": 245678912, "account": "DIDPDA..."},
    {"chain": "bitcoin", "inscriptionId": "txid:vout:index"}
  ],
  "proofs": {
    "zkp": {
      "ethereum": "0xzkproof...",
      "solana": "base64zk...",
      "bitcoin": "bech32zk..."
    },
    "hash": {
      "relaySignatures": ["did:key:z...#sign1", "did:key:z...#sign2"],
      "commitment": "0xhash"
    }
  },
  "presentation": {
    "disclosedAttributes": {"degree": "MSc"},
    "merklePath": ["0xnode1", "0xnode2"]
  },
  "timestamp": 1757606400
}
```

### 4.3 On-Chain Event Schema
- **Ethereum**: `event CredentialAnchored(bytes32 did, bytes32 root, uint256 blockNumber, bytes32 anchorId);`
- **Solana**: PDA data layout `[version|did_hash|root|anchor_id|timestamp]`.
- **Bitcoin**: Inscription envelope with key-value pairs `{"did": "...", "root": "...", "anchor": "..."}` encoded via Ordinals metadata.

---

## 5. Cross-Chain Anchoring Cadence

| Chain    | Anchor Trigger                          | Suggested Cadence                | Notes |
|----------|------------------------------------------|----------------------------------|-------|
| Ethereum | VC issuance, revocation, verifier receipt| Per event (immediate)            | Gas-efficient batching via rollups (Optimism/Arbitrum) for high volume. |
| Solana   | State updates to DID/VC PDAs             | Hourly snapshot or per issuance  | Use durable nonce to prevent duplicate updates when relaying from Ethereum. |
| Bitcoin  | Ordinal inscription / Taproot commit     | Daily aggregate batch            | Bundle multiple credential roots into a single inscription to minimize fees. |

- Cross-chain summary commitments can be published weekly on all chains to ensure liveness.
- Relay should monitor finality windows: Ethereum (~2 epochs), Solana (~32 slots), Bitcoin (~6 blocks) before considering anchor final.

---

## 6. Privacy Strategies

- **Selective Disclosure**: Use Merkle tree or BBS+ signatures to reveal minimal claim data.
- **ZKP-Friendly Hashes**: Poseidon or MiMC inside circuits; use SHA-256 outside for compatibility.
- **Encrypted Off-Chain Storage**: VC payloads stored in holder-controlled storage (e.g., encrypted IPFS using DIDComm v2).
- **Ordinal Privacy**: Hash commitments only; avoid raw PII in inscriptions, rely on off-chain encrypted references.

---

## 7. Key Management

- **Multi-Key DID Documents**: Include separate verification methods for Ethereum (secp256k1), Solana (Ed25519), and Bitcoin (Taproot) with key rotation policies.
- **Hardware Security Modules**: Issuers and relays sign via HSM or MPC wallets to prevent key compromise.
- **Rotation Workflow**:
  1. Generate new key pair.
  2. Publish update transaction on respective chain.
  3. Update DID document hash across chains.
  4. Notify holders through DIDComm message referencing new anchor IDs.
- **Backup & Recovery**: Leverage Shamir Secret Sharing among trusted custodians for long-term key material.

---

## 8. Replay Protection

- **Chain-Specific Nonces**: EIP-155 transaction nonces, Solana blockhash/durable nonce, Bitcoin nSequence for update transactions.
- **Presentation Nonces**: Include verifier-provided challenge in EIP-712 typed data and Solana Ed25519 signatures.
- **Time-Bound Proofs**: Require timestamps and expiry in `CrossChainProof`; proofs invalid after grace period.
- **Anchor ID Evolution**: Each update increments `anchorId` (e.g., hash of previous anchor + block reference) preventing reuse of stale anchors.

---

## 9. Implementation Notes

- **Circuit Templates**: Maintain universal circuits (e.g., Halo2/Plonk) parameterized by chain-specific public inputs (slot, block hash, inscription index).
- **Relay Security**: Run relays in SGX/TEE or implement multi-party computation for proof generation to mitigate single point of failure.
- **Monitoring**: Provide dashboards that track anchor status, finality, and proof verification outcomes per chain.
- **Interoperability**: Align message schemas with W3C VC Data Model 2.0 and DIDComm v2 for transport.

---

## 10. Future Enhancements

- Integrate Ethereum account abstraction (ERC-4337) for automated credential anchors.
- Explore Solana zk-compressed state to reduce proof sizes.
- Leverage Bitcoin BitVM for more expressive verification scripts when available.
- Incorporate post-quantum DID keys (e.g., Dilithium) as optional verification methods.

