# harmonic_memory

`harmonic_memory` is an OpenAI function schema that adapts responses based on a user's evolving musical preferences.

## Parameters

- `user_music_preference` (string, required): Favorite genres that influence the structure of the AI's response. Options include classical, jazz, electronic, ambient, and metal.
- `lyrical_complexity` (string, required): Controls the lyrical depth of the musical response, such as minimal, poetic, or intricate.
- `adaptive_evolution` (boolean, required): When set to `true`, the AI continuously refines its responses using cumulative interaction context.

## Usage

The JSON schema for the function is stored in [`schema.json`](schema.json). Use it with an OpenAI client by registering the function definition, then invoke it to generate adaptive musical narratives or lyrics tailored to the user's preferences.
