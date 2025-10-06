# Music Influence Tool

This directory hosts the `music_influence` tool definition. The tool allows
callers to influence response structure based on musical preferences by
specifying a primary genre, tempo pacing, and mood tone. All three fields are
required when invoking the tool.

## Schema Summary

| Field | Type | Description |
| --- | --- | --- |
| `genre_influence` | string | Primary genre influence derived from the user's music taste. |
| `tempo_preference` | string | Preferred pacing for the response (e.g., adagio, andante, allegro). |
| `mood_influence` | string | Tone modifier describing the desired emotional influence. |

The schema is defined in [`schema.json`](./schema.json) and marks the tool as
strict so that no unspecified properties are accepted.
