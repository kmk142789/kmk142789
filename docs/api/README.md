# Echo Computer Agent API

The Echo Computer Agent exposes a lightweight HTTP interface for listing
callable functions and submitting chat requests. The OpenAPI description is
available at [`echo_computer_agent.openapi.json`](./echo_computer_agent.openapi.json).

## Client generation

Generate the Python, TypeScript, and Go SDKs by running:

```bash
python scripts/generate_clients.py
```

The script writes packages to:

- `clients/python/echo_computer_agent_client`
- `clients/typescript/echo-computer-agent-client`
- `clients/go/echo_computer_agent_client`

Each package includes minimal metadata and an example smoke test entry point.

## Manual smoke test

After generating the clients you can validate them with the included mock
server harness:

```bash
pytest tests/test_generated_clients.py -k smoke
```

The test spins up an HTTP fixture that mimics the agent responses and exercises
all three SDKs (Python, TypeScript, and Go).
