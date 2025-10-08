#!/usr/bin/env python3
import argparse, base64, hashlib, json, os, sys, time, binascii
from pathlib import Path

from echo.thoughtlog import thought_trace


def b64split(text: str):
    # split on '=' while preserving chunks that need padding
    raw_parts = [p for p in text.strip().split('=') if p]
    parts = []
    for p in raw_parts:
        for pad in range(0, 3):
            try:
                parts.append(base64.b64decode(p + '='*pad, validate=True))
                break
            except Exception:
                if pad == 2: raise
    return parts


def sha256(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


def merkle_root(leaves: list[bytes]) -> bytes:
    if not leaves: return b"\x00"*32
    level = [sha256(l) for l in leaves]
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            a = level[i]
            b = level[i+1] if i+1 < len(level) else level[i]  # duplicate last if odd
            nxt.append(sha256(a + b))
        level = nxt
    return level[0]


def load_keystore_and_sign(msg: str, ks_path: str, password: str):
    try:
        from eth_account import Account
        from eth_account.messages import encode_defunct
    except Exception:
        return None  # signing optional
    import json as _json
    data = _json.load(open(ks_path, 'r', encoding='utf-8'))
    pk = Account.decrypt(data, password)
    acct = Account.from_key(pk)
    sig = Account.sign_message(encode_defunct(text=msg), pk)
    return {
        "address": acct.address,
        "signature": sig.signature.hex(),
        "v": sig.v, "r": hex(sig.r), "s": hex(sig.s),
        "schema": "eip191-personal-sign"
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", required=True, help="text file containing your big base64 blob")
    ap.add_argument("--outdir", default="source_artifacts")
    ap.add_argument("--keystore", help="optional: Ethereum V3 keystore to sign the root")
    ap.add_argument("--password", help="optional: password for keystore")
    args = ap.parse_args()
    task = "echo_source_root.main"
    meta = {
        "outdir": args.outdir,
        "keystore": bool(args.keystore),
    }

    with thought_trace(task=task, meta=meta) as tl:
        Path(args.outdir).mkdir(parents=True, exist_ok=True)
        text = Path(args.infile).read_text(encoding="utf-8", errors="ignore")
        packets = b64split(text)
        tl.logic("step", task, "packets decoded", {"count": len(packets)})

        bad = [i for i,p in enumerate(packets) if len(p)!=65]
        if bad:
            print(f"[!] Warning: {len(bad)} packets not 65 bytes (indexes: {bad[:8]}...)")
            tl.logic("warning", task, "irregular packet lengths detected", {"bad": len(bad)})

        bin_path = Path(args.outdir)/"source_packets.bin"
        idx_path = Path(args.outdir)/"source_packets.json"
        with open(bin_path, "wb") as f:
            offset = 0
            index = []
            for i, p in enumerate(packets):
                f.write(p)
                entry = {
                    "i": i,
                    "offset": offset,
                    "len": len(p),
                    "sha256": hashlib.sha256(p).hexdigest()
                }
                index.append(entry)
                offset += len(p)
        Path(idx_path).write_text(json.dumps(index, indent=2), encoding="utf-8")
        tl.logic("step", task, "binary + index written")

        leaf_hashes = [bytes.fromhex(e["sha256"]) for e in index]
        root = merkle_root(leaf_hashes).hex()
        whole_sha = hashlib.sha256(open(bin_path,"rb").read()).hexdigest()
        tl.logic("step", task, "roots computed", {"merkle_root": root})

        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        root_rec = {
            "schema": "EchoSourceRoot/v1",
            "issued_at": ts,
            "packets": len(index),
            "packet_len_expected": 65,
            "bin_sha256": whole_sha,
            "merkle_root_sha256": root,
        }

        if args.keystore and args.password:
            canonical = "\n".join([
                "EchoSourceRoot/v1",
                f"issued_at={ts}",
                f"packets={len(index)}",
                f"packet_len_expected=65",
                f"bin_sha256={whole_sha}",
                f"merkle_root_sha256={root}",
            ])
            sig = load_keystore_and_sign(canonical, args.keystore, args.password)
            if sig:
                root_rec["sign"] = {"canonical": canonical, **sig}
                tl.harmonic("reflection", task, "keystore signature woven")

        root_path = Path(args.outdir)/"source_root.txt"
        Path(root_path).write_text(json.dumps(root_rec, indent=2), encoding="utf-8")

        print("[+] Wrote:", bin_path)
        print("[+] Wrote:", idx_path)
        print("[+] Wrote:", root_path)
        print("[✓] Genesis Source Root:", root)
        tl.harmonic("reflection", task, "source root anchored", {"root": root})


if __name__ == "__main__":
    main()
