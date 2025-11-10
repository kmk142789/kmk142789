#!/usr/bin/env python3
import os, sys, json, time, hashlib, argparse, pathlib, yaml

ROOT = pathlib.Path(__file__).resolve().parent

def h(s): return hashlib.sha256(s.encode()).hexdigest()[:12]

def load_yaml(p): return yaml.safe_load(open(p, "r", encoding="utf-8"))
def dump_yaml(p, obj): open(p, "w", encoding="utf-8").write(yaml.safe_dump(obj, sort_keys=False))

def verify_wallet(addr_path):
    data = json.load(open(addr_path, "r", encoding="utf-8"))
    proof_path = ROOT / data["proof_file"]
    if not proof_path.exists():
        return False, "missing proof"
    proof = open(proof_path, "r", encoding="utf-8").read().strip()
    # OFFLINE sanity check: require template fields + a signature block
    ok = ("WhisperVault Steward Attestation" in proof) and ("SIGNATURE:" in proof)
    if not ok: return False, "malformed proof"
    data["verified"] = True
    data["status"] = "verified"
    json.dump(data, open(addr_path, "w", encoding="utf-8"), indent=2)
    return True, "verified"

def cmd_verify(args):
    changed = 0
    for chain_dir in (ROOT/"sources").glob("*"):
        for f in chain_dir.glob("*.json"):
            ok, msg = verify_wallet(f)
            if ok: changed += 1
    print(f"[wv] verified/updated: {changed}")

def cmd_list(args):
    rows = []
    for chain_dir in (ROOT/"sources").glob("*"):
        for f in chain_dir.glob("*.json"):
            d = json.load(open(f, "r", encoding="utf-8"))
            rows.append((d["chain"], d["address"], d.get("label",""), d.get("verified",False)))
    for r in rows:
        mark = "✅" if r[3] else "⏳"
        print(f"{mark} {r[0]:9} {r[1]}  {r[2]}")

def cmd_approve(args):
    p = ROOT/"approvals"/"pending"/args.file
    if not p.exists(): sys.exit("approval file not found in pending/")
    y = load_yaml(p)
    y["approvals"][args.role] = f"{args.name} @ {time.strftime('%Y-%m-%dT%H:%MZ', time.gmtime())}"
    out = ROOT/"approvals"/"approved"/p.name
    dump_yaml(out, y)
    os.remove(p)
    print(f"[wv] approved -> {out}")

def cmd_ledger(args):
    led = ROOT/"ledger"/f"{time.strftime('%Y-%m')}.ldg"
    os.makedirs(led.parent, exist_ok=True)
    line = f"{time.strftime('%Y-%m-%d')} | {args.kind} | ${args.amount} | {args.category} | {args.payee} | {args.ref} | tx:{args.tx or '-'} | notes:{args.notes or '-'}\n"
    open(led, "a", encoding="utf-8").write(line)
    print(f"[wv] ledger appended -> {led}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(prog="wv")
    sp = ap.add_subparsers()

    s = sp.add_parser("verify"); s.set_defaults(fn=cmd_verify)
    s = sp.add_parser("list"); s.set_defaults(fn=cmd_list)

    s = sp.add_parser("approve"); s.add_argument("file"); s.add_argument("--role", default="second_approver"); s.add_argument("--name", required=True); s.set_defaults(fn=cmd_approve)

    s = sp.add_parser("ledger")
    s.add_argument("--kind", required=True); s.add_argument("--amount", required=True)
    s.add_argument("--category", required=True); s.add_argument("--payee", required=True)
    s.add_argument("--ref", required=True); s.add_argument("--tx"); s.add_argument("--notes")
    s.set_defaults(fn=cmd_ledger)

    args = ap.parse_args()
    if hasattr(args, "fn"): args.fn(args)
    else: ap.print_help()
