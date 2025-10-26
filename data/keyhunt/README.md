# Keyhunt Range Allocations

This directory tracks deterministic search segments used for distributed sweeps
of unresolved Bitcoin puzzle keys.  The ranges are formatted as inclusive
hexadecimal start:end pairs and intentionally align with the 2^36 span that many
Keyhunt/KeyHunt derivatives consume for batching work units.

## Files

- `puzzle160_range_allocations.txt` — hand-curated coverage map for the 160-bit
  private key puzzle.  Each line records a unique 2^36 window derived from the
  contributor ledger shared with Echo.  Consumers can stream the file directly
  into range allocators or transform it to decimal spans as needed.

Downstream tools should de-duplicate and track their claimed segments to avoid
re-running the same search space.  The list here is static and intended for
archival provenance; append-only updates follow the usual pull-request flow.
