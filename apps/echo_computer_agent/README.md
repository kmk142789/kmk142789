# Echo Computer Assistant Agent

This package exposes the `EchoChatAgent` over an HTTP interface powered by
FastAPI.  The agent translates natural language commands into deterministic
function calls.  It can resolve puzzle metadata, surface launch instructions
for key Echo applications, and compile / execute Echo digital computer programs
on demand.

## Quickstart

```bash
pip install -r requirements.txt uvicorn
uvicorn apps.echo_computer_agent.server:app --reload
```

### Example requests

```bash
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "solve puzzle #96"}'

curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "compute factorial", "execute": true, "inputs": {"n": 5}}'
```

Use `GET /functions` to inspect the advertised function-calling schema if you
want to integrate the agent with LangChain, OpenAI function-calling, or similar
orchestration frameworks.
