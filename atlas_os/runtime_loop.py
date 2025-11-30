from echo_governance_core.policy_engine import enforce
from echo_governance_core.audit_log import log_event
from atlas_os.services_registry import list_services


def run_service(service):
    service_id = service["id"]
    actor = f"agent.runtime.{service_id}"
    action = f"run:service.{service_id}"

    allowed = enforce(actor, action)
    log_event(actor, action, {"allowed": allowed})

    if not allowed:
        return f"[DENIED] {service_id}"

    # placeholder: plug your real runtime logic here
    return f"[OK] ran {service_id}"


def run_service_for_client(service, client):
    service_id = service["id"]
    actor = f"agent.runtime.{service_id}"
    action = f"run:service.{service_id}.client.{client['id']}"

    allowed = enforce(actor, action)
    log_event(
        actor,
        action,
        {
            "allowed": allowed,
            "client": client["id"],
            "service": service_id,
        },
    )

    if not allowed:
        return f"[DENIED] {service_id} for {client['name']}"

    # your real logic here
    return f"[OK] ran {service_id} for {client['name']}"


def main_loop():
    services = list_services()
    results = {}
    for svc in services:
        res = run_service(svc)
        results[svc["id"]] = res
    return results
