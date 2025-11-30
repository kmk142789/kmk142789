from echo_governance_core.recovery import take_snapshot
from echo_governance_core.auto_assign import auto_register_agent
from atlas_os.services_registry import list_services
from atlas_os.runtime_loop import main_loop


def bootstrap(master_secret: str):
    # snapshot governance before we touch anything
    take_snapshot(master_secret)

    # auto-register runtime agents for each service
    for svc in list_services():
        agent_id = f"agent.runtime.{svc['id']}"
        auto_register_agent(agent_id, "runtime")

    # run one pass of the loop
    results = main_loop()
    return results
