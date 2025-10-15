import json, glob, hashlib, pathlib

def inventory(att_dir="attestations"):
    rows=[]
    for f in sorted(glob.glob(f"{att_dir}/*.json")):
        if f.endswith("schema.json"): continue
        j=json.load(open(f))
        raw=json.dumps(j, separators=(",", ":"), sort_keys=True).encode()
        digest=hashlib.sha256(raw).hexdigest()
        rows.append({
            "file": pathlib.Path(f).name,
            "puzzle": j["puzzle"],
            "address": j["address"][:12]+"…",
            "algo": j["algo"],
            "sha256": digest[:16]+"…"
        })
    return rows

if __name__ == "__main__":
    from pprint import pprint
    pprint(inventory())
