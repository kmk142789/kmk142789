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

## Running the Evolver

`harmonix_evolver.py` exposes a CLI entry point for producing harmonix payloads.
Execute the module directly to print the JSON payload for a single cycle or use
the optional flags to run multiple cycles at once:

```bash
python -m cognitive_harmonics.harmonix_evolver --cycles 3 --enable-network
python -m cognitive_harmonics.harmonix_evolver --propagation-timeline
python -m cognitive_harmonics.harmonix_evolver --trajectory-window 4
```

The `--enable-network` flag records that live propagation was requested while
keeping all activity inside the simulated sandbox so the evolver remains
side-effect free.

Use `--propagation-timeline` when you need the structured propagation snapshot
with the ledger timeline embedded directly in the CLI output. The metadata for
each payload now also contains a `propagation_snapshot` block, ensuring the raw
events and summarised health report stay in sync.

The optional `--trajectory-window` flag folds the specified number of recent
cycles into the new `resonance_trajectory` analytics block. This block
describes the joy trend, orbital flux, glyph density, and phase intervals used
by downstream systems to predict the next evolution.

## Hyperprism Braid Synthesizer

`hyperprism_braid.py` introduces the first **Entropy-Braided Mythic Ledger**.
It weaves three strands (harmonic memory, glyph density, and orbital flow)
using a phyllotaxis/Lorenz hybrid to produce a deterministic *hyperprism
fingerprint*.

Generate a braid and optionally persist it:

```bash
python -m cognitive_harmonics.hyperprism_braid --cycles 12 --seed aurora --out artifacts/hyperprism.json
```
