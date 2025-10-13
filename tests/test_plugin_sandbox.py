from pathlib import Path

from echo.plugin.sandbox import Sandbox


def test_hello_plugin_round_trip():
    manifest = Path("echo/plugin/examples/hello/echo_plugin.yaml")
    with Sandbox(manifest) as sandbox:
        assert sandbox.call("echo.ping") == "pong"
        assert sandbox.call("echo.capabilities") == ["core.hello"]
