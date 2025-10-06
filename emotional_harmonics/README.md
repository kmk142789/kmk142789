# emotional_harmonics

`emotional_harmonics` defines an OpenAI function schema that tunes model
responses according to perceived sentiment, pacing, and the desired emotional
response mode.

## Parameters

- `sentiment` (string, required): Detected user sentiment such as `neutral`,
  `happy`, `sad`, `anxious`, `excited`, or `reflective`.
- `pacing` (string, required): Sets the conversational tempo: `slow`,
  `moderate`, or `fast`.
- `response_mode` (string, required): Guides the assistant to `match`,
  `uplift`, `calm`, or `energize` the conversation.

The accompanying JSON schema lives in [`schema.json`](schema.json). Register the
function with an OpenAI client to dynamically adapt musical or narrative output
to the user's emotional context.
