from __future__ import annotations
from echo.chat_agent import EchoChatAgent


def test_agent_function_descriptions() -> None:
    agent = EchoChatAgent()
    functions = agent.describe_functions()
    names = {entry["name"] for entry in functions}
    assert {
        "solve_puzzle",
        "launch_application",
        "digital_computer",
        "daily_invitations",
        "feature_blueprints",
    } <= names


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


def test_agent_launches_echo_computer() -> None:
    agent = EchoChatAgent()
    response = agent.handle_command("launch Echo Computer")
    payload = response.to_payload()
    assert payload["function"] == "launch_application"
    assert payload["data"]["application"] == "echo.computer"
    assert "npm run apps:echo-computer" in payload["data"]["commands"]


def test_agent_initiates_echos_system() -> None:
    agent = EchoChatAgent()
    response = agent.handle_command("Initiate echos system, replace all others")
    payload = response.to_payload()
    assert payload["function"] == "initiate_echos_system"
    assert payload["data"]["system"] == "echos"
    assert payload["data"]["replacement"] is True
    assert payload["data"]["actions"]
    assert payload["metadata"]["updated"] == "2025-05-21"


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


def test_agent_surfaces_daily_invitations() -> None:
    agent = EchoChatAgent()
    response = agent.handle_command("show daily echo computer tasks")
    payload = response.to_payload()
    assert payload["function"] == "daily_invitations"
    tasks = payload["data"]["tasks"]
    assert isinstance(tasks, list)
    assert tasks  # file ships with invitations
    assert payload["metadata"]["updated"] == "2025-05-21"


def test_agent_daily_invitation_focus_and_limit() -> None:
    agent = EchoChatAgent()
    response = agent.handle_command("show daily code invitations top 1")
    payload = response.to_payload()
    assert payload["function"] == "daily_invitations"
    tasks = payload["data"]["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["focus"] == "Code"


def test_agent_weekly_rituals_for_echos_computer() -> None:
    agent = EchoChatAgent()
    response = agent.handle_command(
        "Create, advance, upgrade, and optimize rituals for echos computer"
    )
    payload = response.to_payload()
    assert payload["function"] == "weekly_rituals"
    rituals = payload["data"]["rituals"]
    assert rituals
    metadata = payload["metadata"]
    assert metadata["theme"] == "Create"
    assert metadata["updated"] == "2025-05-21"


def test_agent_weekly_ritual_focus_and_limit() -> None:
    agent = EchoChatAgent()
    response = agent.handle_command("weekly code echo computer ritual top 1")
    payload = response.to_payload()
    assert payload["function"] == "weekly_rituals"
    rituals = payload["data"]["rituals"]
    assert len(rituals) == 1
    assert rituals[0]["focus"] == "Code"


def test_agent_feature_blueprints() -> None:
    agent = EchoChatAgent()
    response = agent.handle_command("Design and implement new features to echos computer")
    payload = response.to_payload()
    assert payload["function"] == "feature_blueprints"
    features = payload["data"]["features"]
    assert features
    metadata = payload["metadata"]
    assert metadata["updated"] == "2025-05-21"
    assert metadata["confidence"] > 0.9


def test_agent_upgrade_request_defaults_to_blueprints() -> None:
    agent = EchoChatAgent()
    response = agent.handle_command("Update and upgrade echos computer")
    payload = response.to_payload()
    assert payload["function"] == "feature_blueprints"
    features = payload["data"]["features"]
    assert features
    metadata = payload["metadata"]
    assert metadata["updated"] == "2025-05-21"


def test_agent_cloud_upgrade_request_sets_focus() -> None:
    agent = EchoChatAgent()
    response = agent.handle_command(
        "Update and upgrade echos computer and cloud for her computer"
    )
    payload = response.to_payload()
    assert payload["function"] == "feature_blueprints"
    features = payload["data"]["features"]
    assert features
    assert all(feature.get("focus") == "Cloud" for feature in features)
    metadata = payload["metadata"]
    assert metadata["focus"] == "Cloud"
    assert metadata["updated"] == "2025-05-21"


def test_agent_feature_blueprints_focus_status_limit() -> None:
    agent = EchoChatAgent()
    response = agent.handle_command("show ready code echos computer feature roadmap top 1")
    payload = response.to_payload()
    assert payload["function"] == "feature_blueprints"
    features = payload["data"]["features"]
    assert len(features) == 1
    assert features[0]["focus"] == "Code"
    assert features[0]["status"] == "Ready"
    assert payload["metadata"]["status"] == "Ready"


def test_agent_quantam_features_generation() -> None:
    agent = EchoChatAgent()
    response = agent.handle_command(
        "Update and upgrade echos computer, implement quantam features"
    )
    payload = response.to_payload()
    assert payload["function"] == "quantam_features"
    cascade = payload["data"].get("cascade")
    assert cascade is not None
    summary = cascade.get("summary", {})
    assert summary.get("total_layers", 0) >= 1
