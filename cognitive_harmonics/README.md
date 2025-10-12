# cognitive_harmonics

`cognitive_harmonics` provides an OpenAI function schema for describing a
response through layered harmonic, symbolic, and emotional controls. It mirrors
the richer specification captured in the Echo documentation while remaining
usable as a standalone function definition.

## Parameters

- `waveform` (string, required): Defines the structural encoding such as
  `sine_wave`, `square_wave`, or `complex_harmonic`.
- `resonance_factor` (number, required): Adjusts resonance depth and affects
  cohesion within the generated response.
- `compression` (boolean, required): Enables ultra-dense structuring for
  condensed but amplified meaning.
- `symbolic_inflection` (string, required): Selects a glyph system like `runic`,
  `hieroglyphic`, `fractal`, or `emoji` for symbolic layering.
- `lyricism_mode` (boolean, required): Allows the response to include lyrical or
  poetic elements.
- `emotional_tuning` (string, required): Tunes the overall mood via `uplifting`,
  `calming`, `energizing`, or `neutral` palettes.

The full JSON representation is stored in [`schema.json`](schema.json). Use it
when registering the function with the OpenAI client so tools can reliably
construct the structured response payload.

## Persistent Identity & Memory

The module [`identity_memory.py`](identity_memory.py) ports Echo's portable C++
identity/memory substrate into Python.  It supplies:

- `IdentityManager` for Ed25519 DID creation, signature chaining, and encrypted
  keystore rotation.
- `MemoryStore` for the append-only SQLite event log, KV overlay, and BLAKE3
  blob space used by bridge replicas.
- `bootstrap_identity_memory()` to initialise the entire stack under the
  Harmonix data directory (respects `ECHO_DATA_DIR`).

Import it directly or through `echo.identity_memory` when instrumenting Echo
bridge deployments.
