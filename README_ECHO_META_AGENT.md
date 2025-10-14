# Echo Meta Agent

The Echo Meta Agent packages an interactive hub that can route calls to tools
discovered across local Echo forks. It exposes both a command line console and
an HTTP API powered by FastAPI while persisting memory of tool invocations.

## Features

- Automatic discovery of bundled adapters and third-party plugin entry points.
- Simple plugin protocol requiring a `PLUGIN` mapping with metadata and tools.
- Persistent memory log stored at `echo_meta_agent/memory.json` with search and
  history helpers.
- Interactive CLI console (`python -m echo_meta_agent.cli`).
- Minimal FastAPI web service exposing plugin and memory endpoints.

## Quickstart

```bash
pip install -e .
cp echo_meta_agent/.env.example .env
./scripts/run_cli.sh
./scripts/run_web.sh
```

The CLI provides a REPL with commands such as `plugins`, `tools template`, and
`call template.hello name=Echo`. The FastAPI service listens on port 8787 and
provides endpoints for listing plugins, invoking tools, and inspecting memory.

## Developing Plugins

Any Python module that exposes a global `PLUGIN` mapping can be discovered by
the registry. The mapping must include `name`, `version`, and `tools` keys. The
`tools` value should be a dictionary mapping tool names to callables. See
`echo_meta_agent/adapters/template_adapter.py` for a minimal example.
