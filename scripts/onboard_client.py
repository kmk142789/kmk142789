import sys

from services.revenue_mesh.billing import init_db, register_client


if __name__ == "__main__":
    init_db()
    name, contact, plan, key = sys.argv[1:5]
    register_client(name, contact, plan, key)
    print(f"Registered client {name} ({key}) on plan {plan}")
