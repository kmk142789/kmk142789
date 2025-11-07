import json, sys, hashlib, datetime, pathlib
REG = pathlib.Path(__file__).with_name("modules.json")

def register(name, desc, category):
    rec = {
        "name": name,
        "description": desc,
        "category": category,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "hash": hashlib.sha256(f"{name}|{desc}|{category}".encode()).hexdigest()
    }
    data = json.loads(REG.read_text()) if REG.exists() else []
    data.append(rec)
    REG.write_text(json.dumps(data, indent=2))
    print(json.dumps(rec, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("usage: python module_registry.py <name> <category> <description>")
        sys.exit(1)
    name, category, desc = sys.argv[1], sys.argv[2], " ".join(sys.argv[3:])
    register(name, desc, category)
