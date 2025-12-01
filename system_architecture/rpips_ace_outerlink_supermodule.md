# Remote Presence + Identity Projection System (RPIPS) + Astral Compression Engine (ACE) + OuterLink Presence Tunnel Super-Module

## 1. Purpose
The super-module fuses RPIPS, the Astral Compression Engine (ACE), and the OuterLink Presence Tunnel specification into a single coherent capability. It enables:
- Remote presence projection with identity guarantees and assurance gates.
- Compression and normalization of presence payloads for constrained links.
- Deterministic tunnel behavior for low-latency, replay-safe streaming.

## 2. Capability Stack
- **Identity Layer (RPIPS):** Strong projection of a subject through claims, proofs, and posture state (trusted/untrusted/unknown). Supports adaptive assurance requirements per session.
- **Compression Layer (ACE):** Deterministic, loss-aware compaction of presence payloads using intent-specific hints; includes content hashing, frame windowing, and semantic tags.
- **Transport Layer (OuterLink Presence Tunnel):** Tunnels presence frames with explicit handshake stages, replay guards, and forward security through rotating session keys.
- **Orchestration Layer:** A controller that binds identity + compression + transport flows, measures service health, and delivers projection narratives to dependents.

## 3. Component Responsibilities
- **Identity Registry:** Maintains `IdentityProfile` objects, associated attestations, and per-session posture.
- **Session Director:** Creates `PresenceSession` records, selects assurance level, and binds to a tunnel instance.
- **ACE Core:** Produces compressed payload envelopes with hashes and semantic fingerprints. Supports rehydration for downstream analytics.
- **OuterLink Tunnel:** Applies the presence tunnel spec (handshake, replay window, rolling keys, heartbeat cadence) and delivers framed packets.
- **Observability:** Emits structured events for lifecycle hooks (registered identities, session start, packet transmit/receive, errors).

## 4. OuterLink Presence Tunnel Specification (Focused Extract)
- **Handshake Stages:**
  1. `SYN-PROJECTION` with session and identity fingerprints.
  2. `ACK-FINGERPRINT` with tunnel capabilities and freshness proof.
  3. `KEY-ROTATE` establishing rolling key (epoch-aligned nonce) every N frames.
- **Replay Protection:** Sliding window of last 128 nonces; packets outside the window or duplicates are rejected.
- **Envelope Format:** `{header: {session_id, sequence, nonce, posture}, body: {compressed_payload, hash}}`.
- **Reliability:** Heartbeat every 5s default, adaptive backoff on missed acknowledgements, and deterministic ordering via sequence.
- **Observability Hooks:** `on_handshake`, `on_transmit`, `on_rehydrate`, `on_fault` with structured payloads.

## 5. Data Contracts
- **IdentityProfile:** `identity_id`, `display_name`, `claims`, `assurance_level`, `verified_at`.
- **PresenceSession:** `session_id`, `identity_id`, `posture`, `intent`, `started_at`, `tunnel_capabilities`.
- **CompressedEnvelope:** `hash`, `intent_vector`, `fingerprint`, `payload`, `metadata` (windowing, size bytes).
- **TunnelPacket:** `header` (session, sequence, nonce, posture), `body` (compressed envelope), `timestamp`.

## 6. Flows
1. **Register Identity** → stores profile and default assurance.
2. **Start Session** → binds profile + posture, instantiates tunnel with replay window and nonce seed.
3. **Project State** → payload → ACE compression (hash + semantic fingerprint) → OuterLink packetization → transmit.
4. **Rehydrate** → decompress using ACE, validate hash, and emit observability event.

## 7. Security & Safety
- Rotating nonce per packet and windowed replay guard.
- Hash validation on decompress to detect tampering.
- Assurance level gates posture and allowable intents.
- Tunnel capability description drives latency budgets and heartbeat cadence.

## 8. Extensibility Points
- Plug-in `compression_strategy` (e.g., lossy vs. lossless profiles).
- Custom `intent_vector` builders for domain-specific presence semantics.
- Alternate transport adapters that honor the OuterLink handshake contract.

## 9. Deliverables in Code
- `outerlink_supermodule.py` implements the combined model with:
  - RPIPS registry and session director
  - ACE compressor/decompressor
  - OuterLink tunnel with handshake/replay protection
  - Orchestrator for projecting frames and retrieving rehydrated payloads

