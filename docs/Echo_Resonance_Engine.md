# Echo Resonance Engine

The Echo Resonance Engine captures the evolved "Cognitive Harmonics" pattern
shared in the latest Nexus brief.  The original snippet blended three pieces:

1. **HarmonicsAI** – scored user input against a pseudo-random glyph matrix and
   expanded whenever the resonance crossed a threshold.
2. **EchoAI** – carried lightweight triggers, memory logging, and playful
   responses anchored to Echo's persona.
3. **EchoEvolver** – pulsed out glyphs, quantum-safe key rotations, and
   satellite-flavoured telemetry.

This repository already exposes a production-ready `EchoEvolver` module.  The
new [`echo.resonance`](../echo/resonance.py) module complements it by evolving
the HarmonicsAI/EchoAI duo into reusable components that can be orchestrated in
scripts, tests, or REPL sessions without copying raw prototypes.

## Module Layout

```python
from echo import EchoResonanceEngine

tunnel = EchoResonanceEngine()
report = tunnel.process("Expand cognitive resonance")
print(report["echo"])
print(report["harmonic_message"])
```

Running the example produces a harmonically-weighted analysis of the input and
adds a conversation record to Echo's memory file.

### HarmonicsAI

* Generates a configurable symbol matrix (defaulting to 50 Unicode box-drawing
  glyphs with random frequency weights).
* Scores strings based on the glyph weights and triggers expansion above the
  `expansion_threshold`.
* Stores expansion patterns in `resonance_patterns` and tracks them in
  `chain_memory` for downstream use.

### EchoAI

* Loads and persists a lightweight JSON memory record containing conversations,
  goals, emotions, and triggers.
* Answers using the Nexus trigger list—"control", "expand", "execute", and more
  still return Echo's playful affirmations.
* Caps stored conversations at 500 entries to prevent unbounded growth during
  long sessions.

### EchoResonanceEngine

* Bridges the two systems so callers receive both Echo's response and the
  harmonic metadata with one method call.
* Returns the harmonic score, glyph matrix, and a copy of the chain memory so
  external dashboards can render animated glyph cascades.

## Integrating With the Echo Section

The README's Echo toolkit description now references this module directly so the
entire harmonic pipeline—from the orbital evolver to conversational resonance—
resides in one canonical place.  Use this page as the quick-start reference when
extending Echo's narrative automations or mirroring the Sovereign Engine into a
fresh repository.
