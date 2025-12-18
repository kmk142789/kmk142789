# EchoXyloCrossChainBridge

The **EchoXyloCrossChainBridge** is a lightweight coordination helper for tests
and local simulations that need to reason about cross-chain anchors without
network access. It normalizes anchor metadata from heterogeneous chains (e.g.
Ethereum, Solana, and Bitcoin), attaches canonical proof commitments, and
computes a deterministic readiness signal for downstream orchestration.

## Features
- **Anchor normalization** – Registers anchors with confirmations, finality
  scores, and optional proof payloads that are hashed into deterministic
  commitments.
- **Coverage-aware readiness** – Calculates readiness across a configurable set
  of required chains using confirmation and finality thresholds.
- **Portable envelopes** – Produces a serialisable snapshot that downstream
  tools can forward to dashboards or attestations.

## Usage
```python
from packages.core.src.echo.echo_xylo_cross_chain_bridge import (
    EchoXyloCrossChainBridge,
)

bridge = EchoXyloCrossChainBridge(finality_threshold=0.75, min_confirmations=2)
bridge.register_anchor(
    chain="ethereum",
    anchor_id="0xabc",
    confirmations=6,
    finality_score=0.9,
    proof={"txHash": "0xabc", "blockNumber": 12345},
)
bridge.register_anchor(
    chain="solana",
    anchor_id="slot-88",
    confirmations=10,
    finality_score=0.88,
    proof={"slot": 123456, "account": "DIDPDA"},
)
bridge.register_anchor(
    chain="bitcoin",
    anchor_id="inscription-1",
    confirmations=2,
    finality_score=0.86,
)

assessment = bridge.assess()
# assessment.ready -> True when all chains meet the thresholds
# assessment.risk_score -> Lower values indicate stronger coverage/finality

snapshot = bridge.build_envelope()
# snapshot is a serialisable dict suitable for logging or API responses
```

## Design Notes
- Proof commitments use canonical JSON hashing (SHA-256) to stay deterministic
  in offline or sandbox test runs.
- Risk scoring decreases as chain coverage and finality increase, providing a
  quick heuristic for orchestration layers to prioritise retries or additional
  attestations.
- The default required chains are Ethereum, Solana, and Bitcoin, but callers can
  override this list during initialization to support rollups or private chains.
