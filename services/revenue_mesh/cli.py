import argparse
import services.revenue_mesh.packs  # noqa: F401
from services.revenue_mesh.billing import init_db
from services.revenue_mesh.runtime import run_paid_task
from services.revenue_mesh.service_packs import load


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--client-key", required=True)
    p.add_argument("--service", required=True)
    p.add_argument("--unit-price", type=int, required=True)
    p.add_argument("--metadata", default="{}")
    args = p.parse_args()

    init_db()

    metadata = eval(args.metadata)

    task_fn = load(args.service)

    result = run_paid_task(
        client_key=args.client_key,
        job_type=args.service,
        unit_price_cents=args.unit_price,
        task_fn=task_fn,
        **metadata
    )

    print(result)


if __name__ == "__main__":
    main()
