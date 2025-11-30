import argparse

from services.revenue_mesh.runtime import run_paid_task
from services.revenue_mesh.billing import init_db
from my_runtime_wrappers import device_health_check


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--client-key", required=True)
    p.add_argument("--service", required=True, choices=["device_health_check"])
    p.add_argument("--unit-price", type=int, required=True, help="price in cents per unit")
    args = p.parse_args()

    init_db()

    if args.service == "device_health_check":
        result = run_paid_task(
            client_key=args.client_key,
            job_type="device_health_check",
            unit_price_cents=args.unit_price,
            task_fn=device_health_check,
        )
        print(result)


if __name__ == "__main__":
    main()
