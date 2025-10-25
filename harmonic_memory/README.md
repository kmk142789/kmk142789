# harmonic_memory

`harmonic_memory` is an OpenAI function schema that adapts responses based on a user's evolving musical preferences. Each cycle produced by `cognitive_harmonics.harmonix_evolver.EchoEvolver` now writes a snapshot that adheres to this schema so downstream jobs can replay or analyse the experience deterministically.

## Parameters

- `user_music_preference` (string, required): Favorite genres that influence the structure of the AI's response. Options include classical, jazz, electronic, ambient, and metal.
- `lyrical_complexity` (string, required): Controls the lyrical depth of the musical response, such as minimal, poetic, or intricate. For cycle snapshots this field encodes the narrative density, number of logged events, and the leading digits of the payload checksum.
- `adaptive_evolution` (boolean, required): When set to `true`, the AI continuously refines its responses using cumulative interaction context.
- `cycle_snapshot` (object, required): Structured record that combines the serialized `EchoEvolver.snapshot_state()`, the harmonix payload, and the supporting puzzle metadata. The block contains:
  - `cycle_id` (integer): Sequential identifier written after each call to `run_cycle()`.
  - `puzzle` (object): Solved Bitcoin puzzle metadata sourced from `satoshi.puzzle_dataset`. Includes `puzzle_id`, `bits`, `address`, `hash160`, `solve_date`, `btc_value`, the inclusive key range, the compressed `public_key`, and checksums for both the Base58Check address and HASH160 digest.
  - `state` (object): Detached snapshot from `EchoEvolver.snapshot_state()`.
  - `payload` (object): Harmonix payload returned to the caller.
  - `artifact` (object): Contains the textual artifact body produced by `EchoEvolver.build_artifact()` and its filesystem path.
  - `checksums` (object): SHA-256 digests for the state snapshot, harmonix payload, and textual artifact to support tamper detection.

## Usage

The JSON schema for the function is stored in [`schema.json`](schema.json). Use it with an OpenAI client by registering the function definition, then invoke it to generate adaptive musical narratives or lyrics tailored to the user's preferences.

Cycle snapshots are written to `harmonic_memory/cycles/cycle_XXXXX.json`, where the suffix is zero-padded to five digits. These files conform to the schema described above and can be globbed by downstream analytics pipelines.
