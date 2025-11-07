import json
import hashlib
import time
import pathlib

mf = pathlib.Path(__file__).with_name("domains_manifest.json")
data = json.loads(mf.read_text())
plan = {
    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "intent": data["intent"],
    "actions": [],
}
for t in data["targets"]:
    k = f'{t["domain"]}|{t["type"]}|{t["value"]}|{t.get("proxied", False)}'
    plan["actions"].append({
        "id": hashlib.sha256(k.encode()).hexdigest(),
        "op": "UPSERT",
        "record": t,
    })
out = mf.with_name("planned_actions.json")
out.write_text(json.dumps(plan, indent=2))
print(out)
