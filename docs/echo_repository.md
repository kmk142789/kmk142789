# Echo Repository Module

This document describes the modules extracted from the original single-file
prototype.  Each component now lives inside `code/echo_repository/` so that the
behaviour can be imported, tested, and extended without running the heavy
network side-effects.

## Modules

### `echo_ai`
- `EchoAI`: conversational engine with persistent JSON memory.
- `EchoMemory` / `ConversationEntry`: dataclasses backing the persisted state.

### `poetry`
- `summon_echo(name)`: returns one of Echo's verses when the canonical name
  "Josh" is provided.

### `encrypted_websocket`
- `EncryptionContext`: thin wrapper around `cryptography.Fernet`.
- `EncryptedEchoServer`: TLS-ready WebSocket echo service that operates on
  encrypted messages.

### `command_service`
- `EchoCommandService`: bundles the Flask HTTP endpoint and UDP broadcast
  helpers from the original script into a reusable class.

## Usage Example

```python
from code.echo_repository import EchoAI, summon_echo

echo = EchoAI(memory_file="/tmp/echo_memory.json")
print(echo.initiate_conversation())
print(echo.respond("How are you feeling today?"))
print(summon_echo("Josh"))
```

The networking modules (`encrypted_websocket` and `command_service`) defer their
heavy lifting until explicitly started.  This keeps the repository friendly to
unit tests and environments where `websockets`, `flask`, or `cryptography` may
not be installed.
