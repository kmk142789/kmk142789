# harmonic_cognition (function schema)

This directory stores the OpenAI function schema for the `harmonic_cognition`
tool. While the Python implementation lives in
[`code/harmonic_cognition.py`](../../code/harmonic_cognition.py), this schema
allows API-driven orchestration layers to call the assistant with a
consistent payload structure.

## Parameters

- `waveform` (string, required): Determines the tonal character such as
  `sine_wave`, `legato`, `staccato`, or `polyphonic`.
- `resonance_factor` (number, required): Controls the depth of the harmonic
  pattern applied to the text.
- `lyricism_mode` (boolean, required): Enables lyrical or poetic embellishment
  when `true`.
- `emotional_tuning` (string, required): Guides the emotional orientation of the
  response. Options include `uplifting`, `calming`, `energizing`, or `neutral`.

The schema is defined in [`schema.json`](schema.json) for easy consumption by
OpenAI API clients.
