from echo_meta_agent.registry import PluginRegistry


def test_template_plugin_discovered() -> None:
    registry = PluginRegistry()
    plugins = registry.list_plugins()
    assert "template" in plugins

    tools = registry.list_tools("template")
    assert "hello" in tools

    result = registry.call("template", "hello", name="Echo")
    assert result == "Hello, Echo!"
