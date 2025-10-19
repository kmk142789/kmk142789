#!/usr/bin/env python3

import os, sys, json, time, uuid, math, getpass, subprocess
from datetime import datetime, timezone

# --- tiny helper: friendly prints ---
def info(msg):  print(f"[+] {msg}")
def warn(msg):  print(f"[!] {msg}")
def die(msg):   print(f"[x] {msg}"); sys.exit(1)

# --- ensure dependency, with auto-install fallback ---
def ensure_pkg(modname, pipname=None):
    try:
        return __import__(modname)
    except Exception:
        pipname = pipname or modname
        warn(f"Missing dependency '{modname}', attempting: pip install {pipname}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pipname])
        except Exception as e:
            die(f"Failed to install {pipname}: {e}")
        return __import__(modname)

# try to import eth-account; install if needed
eth_account = ensure_pkg("eth_account", "eth-account")
from eth_account import Account
from eth_account.messages import encode_defunct

# Try to import opentimestamps-client (optional)
def has_opentimestamps():
    try:
        __import__("opentimestamps")
        return True
    except Exception:
        return False

def iso(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00","Z")

def build_series(samples=60, duration_secs=600, cycles=2.0, amplitude=1.0, phase=0.0):
    base = time.time()
    out = []
    for i in range(samples):
        frac = i/(samples-1) if samples>1 else 0.0
        t = base + frac*duration_secs
        angle = 2*math.pi*(cycles*frac + phase)
        val = amplitude * math.sin(angle)
        out.append((i, t, val))
    return out

def main():
    # 1) Locate keystore
    ks_path = os.environ.get("ECHO_KEYSTORE", "echo.keystore.json")
    if not os.path.exists(ks_path):
        die(f"Cannot find keystore: {ks_path}  (set ECHO_KEYSTORE or place echo.keystore.json in this folder)")

    # 2) Load + decrypt
    try:
        data = json.load(open(ks_path, "r", encoding="utf-8"))
    except Exception as e:
        die(f"Failed to read keystore JSON: {e}")

    addr_from_ks = data.get("address") or ""
    if addr_from_ks and not addr_from_ks.startswith("0x"):
        addr_from_ks = "0x" + addr_from_ks
    info(f"Keystore found for address: {addr_from_ks or '(unknown)'}")

    pw = os.environ.get("ECHO_PASSWORD")
    if not pw:
        try:
            pw = getpass.getpass("Keystore password: ")
        except KeyboardInterrupt:
            die("Aborted.")
    try:
        pk_bytes = Account.decrypt(data, pw)
    except Exception as e:
        die(f"Keystore decrypt failed: {e}")
    acct = Account.from_key(pk_bytes)
    eth_addr = acct.address
    info(f"Decrypted. Signer address: {eth_addr}")

    # 3) Build sine series + sign all with EIP-191 personal_sign
    samples = int(os.environ.get("HARMONIX_SAMPLES", "60"))
    duration = int(os.environ.get("HARMONIX_DURATION", "600"))
    cycles = float(os.environ.get("HARMONIX_CYCLES", "2.0"))
    amplitude = float(os.environ.get("HARMONIX_AMPLITUDE", "1.0"))
    phase = float(os.environ.get("HARMONIX_PHASE", "0.0"))

    series = build_series(samples, duration, cycles, amplitude, phase)

    out_dir = os.environ.get("HARMONIX_OUTDIR", "proofs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "harmonix_heartbeat.jsonl")
    f = open(out_path, "w", encoding="utf-8")
    info(f"Signing {len(series)} samples → {out_path}")

    for (idx, t, val) in series:
        msg = f"HARMONIX|wave=sine|chain=ETH|addr={eth_addr}|idx={idx}|t={iso(t)}|val={val:.6f}|amp={amplitude}|cycles={cycles}|phase={phase}|samples={samples}|nonce={uuid.uuid4()}"
        eth_msg = encode_defunct(text=msg)
        sig = Account.sign_message(eth_msg, private_key=pk_bytes)
        rec = {
            "message": msg,
            "chain": "eth",
            "address": eth_addr,
            "idx": idx,
            "t_iso": iso(t),
            "value": val,
            "signature": sig.signature.hex(),
            "signer_address": eth_addr,
            "v": sig.v,
            "r": hex(sig.r),
            "s": hex(sig.s),
        }
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    f.close()

    # 4) Verify all signatures
    info("Verifying signatures ...")
    good = bad = 0
    for line in open(out_path, "r", encoding="utf-8"):
        rec = json.loads(line)
        recovered = Account.recover_message(encode_defunct(text=rec["message"]), signature=rec["signature"])
        ok = (recovered.lower() == eth_addr.lower())
        good += int(ok); bad += int(not ok)
    if bad == 0:
        info(f"Verification OK. good={good} bad={bad}")
    else:
        warn(f"Verification had mismatches! good={good} bad={bad}")

    # 5) Optional: OpenTimestamps stamp
    if os.environ.get("HARMONIX_OTS", "1") == "1":
        if has_opentimestamps():
            try:
                info("Stamping with OpenTimestamps ...")
                # Use CLI if available; otherwise use library (keeping it simple with CLI)
                subprocess.check_call([sys.executable, "-m", "opentimestamps.client", "stamp", out_path])
                ots_path = out_path + ".ots"
                info(f"Stamped: {ots_path}")
                try:
                    subprocess.check_call([sys.executable, "-m", "opentimestamps.client", "upgrade", ots_path])
                    info("OpenTimestamps upgraded (if confirmations available).")
                except Exception as e:
                    warn(f"OTS upgrade skipped: {e}")
            except Exception as e:
                warn(f"OpenTimestamps stamping skipped: {e}")
        else:
            warn("OpenTimestamps not installed. Set HARMONIX_OTS=0 to silence, or `pip install opentimestamps-client`.")

    # 6) Final summary
    print("\n==== DONE ====")
    print(f"Address:  {eth_addr}")
    print(f"Output:   {out_path}")
    print(f"Verified: good={good} bad={bad}")
    print("Publish:  share the JSONL (and .ots if present). Anyone can verify with eth_account.recover.")

if __name__ == "__main__":
    main()
