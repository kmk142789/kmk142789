from __future__ import annotations
from echo.chat_agent import EchoChatAgent


def test_agent_function_descriptions() -> None:
    agent = EchoChatAgent()
    functions = agent.describe_functions()
    names = {entry["name"] for entry in functions}
    assert {"solve_puzzle", "launch_application", "digital_computer"} <= names


def test_agent_solves_known_puzzle() -> None:
    agent = EchoChatAgent()
    response = agent.handle_command("solve puzzle #96")
    payload = response.to_payload()
    assert payload["function"] == "solve_puzzle"
    puzzle = payload["data"]["puzzle"]
    assert puzzle["id"] == 96
    assert puzzle["address"].startswith("15ANY")


def test_agent_launch_instructions() -> None:
    agent = EchoChatAgent()
    response = agent.handle_command("launch echo.bank")
    payload = response.to_payload()
    assert payload["function"] == "launch_application"
    assert "npm run dev" in payload["data"]["commands"]


def test_agent_executes_digital_program() -> None:
    agent = EchoChatAgent()
    response = agent.handle_command(
        "compute factorial of n",
        inputs={"n": 5},
        execute=True,
    )
    payload = response.to_payload()
    assert payload["function"] == "digital_computer"
    assert payload["data"]["suggestion"]["metadata"]["template"] == "factorial"
    execution = payload["data"].get("execution")
    assert execution is not None
    assert execution["output"] == ["120"]
