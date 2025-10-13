import json
import sys

for line in sys.stdin:
    req = json.loads(line)
    method = req.get("method")
    if method == "echo.ping":
        result = "pong"
    elif method == "echo.capabilities":
        result = ["core.hello"]
    else:
        result = f"unknown:{method}"
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": req.get("id"), "result": result}) + "\n")
    sys.stdout.flush()
