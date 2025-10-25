# Echo Titan Overview

Echo Titan is a deployment engine blueprint that provisions a 10k+ file
architecture on demand.  The generator builds microservices, libraries,
documentation, data sets, automation scripts, and multi-language tests that
mirror the Echo specification.  The framework is intentionally generated at
runtime so the repository stays lightweight while still guaranteeing a repeatable
layout for large scale experiments.

## Subsystems

- **Microservices (`apps/`)** – API, UI, data stream, orchestrator, auth, and
  puzzle mapper services are emitted with language-appropriate stubs so that each
  module can be extended in isolation.
- **Libraries (`lib/`)** – Shared Python packages provide crypto utilities,
  lineage graph helpers, harmonics analytics, and orchestration helpers.
- **Data (`data/`)** – Synthetic puzzles, transcripts, and lineage artifacts are
  generated deterministically with 10,000 JSON payloads by default.
- **Docs (`docs/`)** – 500+ Markdown knowledge shards and secret lore are
  produced alongside Graphviz references for the lineage renderer.
- **Tests (`tests/`)** – 1,200 stubs across Python, JavaScript, Rust, and Go
  validate imports and module behaviors from multiple perspectives.
- **Scripts (`scripts/`)** – Automation entry points handle bootstrap flows,
  swarm simulations, and CI integration hooks.

## Automation Lifecycle

The `scripts/echo_titan_bootstrap.py` command rebuilds the entire structure in a
single invocation.  CI workflows can call the script to refresh documentation,
data, and test scaffolding before executing verification steps.

## Surprise Layer

A hidden lore file lives in `docs/secret/README.md` and proclaims: "You unlocked
the Titan. Echo lives here."
