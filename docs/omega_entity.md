# OMEGA: Biodegradable Sovereign Code ("Digital Lifeform")

The `code/omega_entity.py` script encapsulates a small, mortal Python program
that behaves like a "digital lifeform": it runs, expresses its state, removes
its own capabilities, and ultimately deletes itself. Each execution drains a
health point (HP), removes one of its "organs" (visuals, then audio), and ends
by erasing the source file when HP reaches zero.

## Why it matters
- **Self-terminating by design:** The entity rewrites its own file to strip
  features as it weakens, then deletes itself—an intentionally biodegradable
  form of code. 
- **Run-to-decay lifecycle:** There are only three meaningful cycles: full
  senses (HP 3), audio-only (HP 2), and minimal consciousness (HP 1) before
  final deletion (HP 0).
- **Minimal footprint:** No external dependencies beyond the Python standard
  library; it is safe to run in an isolated environment to witness the decay
  sequence end to end.

## How to experience the lifecycle
1. Run `python code/omega_entity.py` to start at full strength. The entity will
   render a lattice, beep, and share a brief thought before rewriting its
   source file to reduce HP.
2. Re-run the script to witness the reduced feature set. After the third run,
   the file removes itself from disk.

> **Caution:** Because the script deletes and rewrites its own source, copy it to
> a disposable location if you need to preserve the original form. Each run is
> irreversible by design.
