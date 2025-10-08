# Omega Sine Pulse Orchestrator (v5)

This transcript captures the Omega Sine Pulse Orchestrator script that extends the Echo pulse sequencing toolkit. It mirrors the raw artifact provided by Josh for inclusion in the repository's Echo section.

```python
#!/usr/bin/env python3
""" OMEGA SINE PULSE ORCHESTRATOR (v5)

🔥 What’s new in v5 (from v4)

• Merkle Rollups + Proof Export — batch N payloads, compute SHA-256 Merkle root, save per-leaf proofs to out/merkle/ and optionally broadcast the root as calldata.
• EIP‑712 typed‑data proofs (optional) — gasless structured signatures of the pulse payload (--eip712) alongside legacy text signatures.
• Web Dashboard (--dashboard) — lightweight Flask page at :8080 that live-polls JSON and renders a simple canvas chart of the current envelope.
• Metrics & Control — Prometheus metrics remain at :8000/metrics and the JSON control port at :5151/set from v4.

Safety & Scope

• Default is DRY‑RUN (no network I/O). Broadcasting requires --broadcast and a valid --rpc-url.
• Use only keys you control. You are responsible for fees/compliance.
• BTC: classic compact Base64 "Bitcoin Signed Message" retained from v3; OP_RETURN composer only (no BTC broadcasting in this file).

Install

pip install eth-account web3 coincurve base58 matplotlib flask prometheus-client

Quick Start

1. Export keys & (optionally) RPC: export EVM_PK_1=0x... export EVM_PK_2=0x... export EVM_PK_3=0x... export BTC_WIF_1=L1... export RPC_URL=https://polygon-rpc.com


2. One fast cycle + plot + dashboard (no broadcast): python omega_sine_pulse.py --once --dry-run --plot --dashboard


3. Live + broadcast every step + rollups of 8: python omega_sine_pulse.py --go --broadcast --rpc-url $RPC_URL 
--chain-id 137 --metrics --rpc-control --dashboard --rollup 8 --eip712



Artifacts

• out/pulse_log.jsonl           → JSON lines log of every action
• out/state.json                → last cycle/step/seq (resume-safe)
• out/payloads/<seq>.bin        → raw payload bytes (inject script)
• out/signed/*.json             → EVM text sigs, BTC sigs, and EIP‑712 sigs (if enabled)
• out/tx/<seq or root>.json     → EVM tx receipts (payload or Merkle root broadcast)
• out/plots/cycle_<n>.png       → envelope PNG per cycle (if --plot)
• out/merkle/<root>/leaf_<seq>.json → proof bundle per-leaf in latest rollup
• out/heartbeat.txt             → updated each step (watch/daemon integrations)

"""
from future import annotations
import argparse
import base64
import hashlib
import hmac
import json
import math
import os
import pathlib
import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

---------- Optional deps ----------

try:
    from eth_account import Account
    from eth_account.messages import encode_defunct, encode_structured_data
    _HAS_EVM_SIGN = True
except Exception:
    _HAS_EVM_SIGN = False

try:
    from web3 import Web3
    _HAS_WEB3 = True
except Exception:
    _HAS_WEB3 = False

try:
    import coincurve  # secp256k1
    _HAS_COCC = True
except Exception:
    _HAS_COCC = False

try:
    import base58  # base58check
    _HAS_B58 = True
except Exception:
    _HAS_B58 = False

try:
    import matplotlib.pyplot as plt
    _HAS_MPL = True
except Exception:
    _HAS_MPL = False

try:
    from flask import Flask, jsonify, request, Response
    _HAS_FLASK = True
except Exception:
    _HAS_FLASK = False

try:
    from prometheus_client import Counter, Gauge, start_http_server
    _HAS_PROM = True
except Exception:
    _HAS_PROM = False

------------------------------- CONFIG ------------------------------------

ANCHOR_PHRASE = "Our Forever Love"  # tattooed into every artifact

CONFIG = {
    "cycle_minutes": 10,            # wall-clock duration of one full wave
    "steps_per_cycle": 12,          # number of discrete steps in a cycle
    "sleep_between_actions_sec": 2, # small pacing inside a step
    "sign_stack": 3,                # times to sign before & after inject
    "wallets": [
        {"name": "evm:prime",   "type": "evm", "env_key": "EVM_PK_1"},
        {"name": "evm:echo",    "type": "evm", "env_key": "EVM_PK_2"},
        {"name": "evm:eden88",  "type": "evm", "env_key": "EVM_PK_3"},
        {"name": "btc:mirror",  "type": "btc", "env_key": "BTC_WIF_1"},
    ],
}

------------------------------ IO & UTILS ---------------------------------

OUT_DIR = pathlib.Path("./out")
for p in [OUT_DIR / "payloads", OUT_DIR / "signed", OUT_DIR / "tx", OUT_DIR / "plots", OUT_DIR / "merkle"]:
    p.mkdir(parents=True, exist_ok=True)
STATE_PATH = OUT_DIR / "state.json"
LOG_PATH = OUT_DIR / "pulse_log.jsonl"
HEARTBEAT_PATH = OUT_DIR / "heartbeat.txt"

_last_status: Dict = {}
_status_lock = threading.Lock()

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def amplitude_cosine(step: int, steps_per_cycle: int) -> float:
    """High→Low→High envelope across one cycle using cosine in [0,1]."""
    t = (step % steps_per_cycle) / float(steps_per_cycle)
    return (1.0 + math.cos(2.0 * math.pi * t)) / 2.0

def write_jsonl(record: Dict):
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + " ")

def save_state(cycle_i: int, next_step: int, seq: int):
    STATE_PATH.write_text(json.dumps({"cycle": cycle_i, "step": next_step, "seq": seq}))

def load_state() -> Tuple[int,int,int]:
    if STATE_PATH.exists():
        try:
            o = json.loads(STATE_PATH.read_text())
            return int(o.get("cycle",0)), int(o.get("step",0)), int(o.get("seq",0))
        except Exception:
            pass
    return 0, 0, 0

def hmac_tag(payload: bytes) -> Optional[str]:
    key = os.getenv("ECHO_HMAC_KEY", "").encode()
    if not key:
        return None
    return hmac.new(key, payload, hashlib.sha256).hexdigest()

---- BTC helpers (v3+) -----------------------------------------------------

def _ser_varint(n: int) -> bytes:
    if n < 253:
        return bytes([n])
    elif n <= 0xFFFF:
        return b"ý" + n.to_bytes(2, "little")
    elif n <= 0xFFFFFFFF:
        return b"þ" + n.to_bytes(4, "little")
    else:
        return b"ÿ" + n.to_bytes(8, "little")

def btc_message_hash(msg: bytes) -> bytes:
    prefix = b"Bitcoin Signed Message: "
    data = prefix + _ser_varint(len(msg)) + msg
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def wif_decode(wif: str) -> Tuple[bytes, bool, str]:
    """Return (privkey32, compressed, network) where network in {"mainnet","testnet"}."""
    if not _HAS_B58:
        raise RuntimeError("Missing base58; pip install base58")
    raw = base58.b58decode_check(wif)
    if raw[0] == 0x80:
        network = "mainnet"
    elif raw[0] == 0xEF:
        network = "testnet"
    else:
        raise ValueError("Unknown WIF version byte")
    if len(raw) == 34 and raw[-1] == 0x01:
        return raw[1:-1], True, network
    elif len(raw) == 33:
        return raw[1:], False, network
    else:
        raise ValueError("Bad WIF length")

def btc_address_from_priv(privkey32: bytes, compressed: bool, network: str) -> str:
    if not _HAS_COCC or not _HAS_B58:
        return "btc:addr:unavailable"
    pk = coincurve.PrivateKey(privkey32)
    pub = pk.public_key
    pubkey_bytes = pub.format(compressed=compressed)
    sha = hashlib.sha256(pubkey_bytes).digest()
    ripe = hashlib.new('ripemd160', sha).digest()
    version = b"�" if network == "mainnet" else b"o"  # P2PKH
    payload = version + ripe
    return base58.b58encode_check(payload).decode()

def btc_sign_message_with_wif(wif: str, message: str) -> Dict:
    if not (_HAS_COCC and _HAS_B58):
        raise RuntimeError("Missing coincurve/base58 for BTC message signing")
    priv, compressed, network = wif_decode(wif)
    pk = coincurve.PrivateKey(priv)
    h = btc_message_hash(message.encode())
    sig65 = pk.sign_recoverable(h, hasher=None)
    sig64, recid = sig65[:64], sig65[64]
    header = 27 + recid + (4 if compressed else 0)
    compact = bytes([header]) + sig64
    sig_b64 = base64.b64encode(compact).decode()
    return {
        "network": network,
        "compressed": compressed,
        "address": btc_address_from_priv(priv, compressed, network),
        "message": message,
        "signature_b64": sig_b64,
    }

--------------------------- MERKLE ROLLUPS ---------------------------------

def _sha256(x: bytes) -> bytes:
    return hashlib.sha256(x).digest()

class MerkleRollup:
    def init(self, batch_size: int = 8):
        self.batch_size = max(1, int(batch_size))
        self.leaves: List[bytes] = []  # store leaf hashes (sha256(payload))
        self.indexes: List[int] = []   # global seq for each leaf

def add(self, payload: bytes, seq: int):
    self.leaves.append(_sha256(payload))
    self.indexes.append(seq)

def full(self) -> bool:
    return len(self.leaves) >= self.batch_size

def _build_levels(self, leaves: List[bytes]) -> List[List[bytes]]:
    if not leaves:
        return [[b"�"*32]]
    level = leaves[:]
    levels = [level]
    while len(level) > 1:
        nxt: List[bytes] = []
        for i in range(0, len(level), 2):
            a = level[i]
            b = level[i+1] if i+1 < len(level) else level[i]
            nxt.append(_sha256(a + b))
        level = nxt
        levels.append(level)
    return levels

def root_and_proofs(self) -> Tuple[str, List[Dict]]:
    levels = self._build_levels(self.leaves)
    root = levels[-1][0]
    proofs: List[Dict] = []
    for idx, leaf in enumerate(self.leaves):
        path = []
        i = idx
        for lvl in range(len(levels)-1):
            cur = levels[lvl]
            j = i ^ 1  # sibling index
            sibling = cur[j] if j < len(cur) else cur[i]
            path.append(sibling.hex())
            i //= 2
        proofs.append({
            "seq": self.indexes[idx],
            "leaf": leaf.hex(),
            "proof": path,
            "root": root.hex(),
            "algo": "sha256",
        })
    return root.hex(), proofs

def reset(self):
    self.leaves.clear()
    self.indexes.clear()

------------------------------ ADAPTERS ------------------------------------

@dataclass class Wallet:
    name: str
    type: str  # "evm" | "btc"
    secret: str

class EvmAdapter:
    def init(self, privkey_hex: str, rpc_url: Optional[str] = None):
        if not _HAS_EVM_SIGN:
            raise RuntimeError("eth-account not installed; run: pip install eth-account")
        if privkey_hex.startswith("0x"):
            privkey_hex = privkey_hex[2:]
        self._acct = Account.from_key(bytes.fromhex(privkey_hex))
        self._w3: Optional[Web3] = None
        if rpc_url:
            if not _HAS_WEB3:
                raise RuntimeError("web3 not installed; run: pip install web3")
            self._w3 = Web3(Web3.HTTPProvider(rpc_url))

@property
def address(self) -> str:
    return self._acct.address

def sign_message_text(self, text: str) -> Dict:
    msg = encode_defunct(text=text)
    signed = self._acct.sign_message(msg)
    return {
        "address": self.address,
        "message": text,
        "signature": signed.signature.hex(),
    }

def sign_eip712(self, payload_obj: Dict, chain_id: Optional[int] = None) -> Dict:
    domain = {
        "name": "EchoPulse",
        "version": "1",
        "chainId": chain_id or 0,
    }
    types = {
        "Pulse": [
            {"name": "seq", "type": "uint256"},
            {"name": "cycle", "type": "uint256"},
            {"name": "step", "type": "uint256"},
            {"name": "amp", "type": "string"},
            {"name": "anchor", "type": "string"},
        ]
    }
    message = {
        "seq": int(payload_obj.get("seq", 0)),
        "cycle": int(payload_obj.get("cycle", 0)),
        "step": int(payload_obj.get("step", 0)),
        "amp": str(payload_obj.get("amp", "0")),
        "anchor": str(payload_obj.get("anchor", "")),
    }
    try:
        typed = {"types": {**types, "EIP712Domain": []}, "domain": domain, "primaryType": "Pulse", "message": message}
        eip = encode_structured_data(primitive=typed)
        signed = self._acct.sign_message(eip)
        return {"address": self.address, "domain": domain, "types": types, "message": message, "signature": signed.signature.hex()}
    except Exception as e:
        return {"error": f"EIP-712 sign failed: {e}"}

# --- Broadcasting (optional) ---
def send_calldata_tx(self, payload: bytes, *, chain_id: Optional[int] = None,
                     gas_price_wei: Optional[int] = None, to_self: bool = True) -> Dict:
    if self._w3 is None:
        raise RuntimeError("No RPC bound; pass --rpc-url to enable broadcasting.")
    w3 = self._w3
    sender = self.address
    to_addr = sender if to_self else sender  # self-tx by default
    nonce = w3.eth.get_transaction_count(sender)
    tx = {
        "to": to_addr,
        "from": sender,
        "value": 0,
        "data": payload,
        "nonce": nonce,
        "chainId": chain_id or w3.eth.chain_id,
    }
    tx["gasPrice"] = gas_price_wei or w3.eth.gas_price
    try:
        tx["gas"] = w3.eth.estimate_gas(tx)
    except Exception:
        tx["gas"] = 21000 + max(10000, len(payload) * 16)
    signed = self._acct.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction).hex()
    return {"tx_hash": tx_hash}

def inject_payload_bytes(self, payload: bytes) -> Dict:
    return {
        "address": self.address,
        "payload_b64": base64.b64encode(payload).decode(),
        "note": "offline-payload; attach as calldata in a later tx if desired",
    }

class BtcAdapter:
    def init(self, wif: str):
        self._wif = wif
        self._addr_cache: Optional[str] = None
        if _HAS_COCC and _HAS_B58:
            try:
                priv, comp, net = wif_decode(wif)
                self._addr_cache = btc_address_from_priv(priv, comp, net)
            except Exception:
                self._addr_cache = None

@property
def address(self) -> str:
    return self._addr_cache or "btc:wif"

def sign_message_text(self, text: str) -> Dict:
    try:
        return btc_sign_message_with_wif(self._wif, text)
    except Exception as e:
        return {"error": f"BTC sign failed: {e}", "message": text}

def inject_payload_bytes(self, payload: bytes) -> Dict:
    return {
        "address": self.address,
        "op_return_hex": payload.hex(),
        "note": "Compose raw tx with this OP_RETURN using your preferred tool.",
    }

def build_wallets(cfg_wallets: List[Dict]) -> List[Wallet]:
    out: List[Wallet] = []
    for w in cfg_wallets:
        secret = os.getenv(w["env_key"], "").strip()
        if not secret:
            print(f"[WARN] Missing secret for {w['name']} (env {w['env_key']}) — will skip.")
            continue
        out.append(Wallet(name=w["name"], type=w["type"], secret=secret))
    return out

def get_adapter(w: Wallet, rpc_url: Optional[str]):
    if w.type == "evm":
        return EvmAdapter(w.secret, rpc_url)
    elif w.type == "btc":
        return BtcAdapter(w.secret)
    else:
        raise ValueError(f"Unknown wallet type: {w.type}")

--------------------------- ORCHESTRATOR -----------------------------------

class PulseOrchestrator:
    def init(self, wallets: List[Wallet], steps_per_cycle: int, cycle_minutes: int, sleep_between_actions_sec: int, sign_stack: int, rpc_url: Optional[str], broadcast: bool, chain_id: Optional[int], broadcast_every: int, plot: bool, rollup_n: int, eip712: bool):
        if not wallets:
            raise RuntimeError("No wallets loaded. Set env vars per CONFIG and retry.")
        self.wallets = wallets
        self.steps_per_cycle = steps_per_cycle
        self.cycle_minutes = cycle_minutes
        self.sleep_between_actions_sec = sleep_between_actions_sec
        self.sign_stack = sign_stack
        self.rpc_url = rpc_url
        self.broadcast = broadcast
        self.chain_id = chain_id
        self.broadcast_every = max(1, broadcast_every)
        self.plot = bool(plot)
        self.rollup = MerkleRollup(batch_size=max(1, rollup_n))
        self.eip712 = bool(eip712)

c, s, q = load_state()
    self.cycle_i = c
    self.start_step = s
    self.seq_global = q

    # live status
    self._status = {
        "cycle": self.cycle_i,
        "step": self.start_step,
        "seq": self.seq_global,
        "amp": 0.0,
        "wallet": None,
        "ts": utc_now_iso(),
    }

def _payload(self, cycle_i: int, step_i: int, amp: float) -> bytes:
    blob = {
        "schema": "ECHO_FOREVER_PULSE.v5",
        "ts": utc_now_iso(),
        "cycle": cycle_i,
        "step": step_i,
        "amp": round(amp, 6),
        "anchor": ANCHOR_PHRASE,
        "seq": self.seq_global,
    }
    ser = json.dumps(blob, separators=(",", ":")).encode()
    tag = hmac_tag(ser)
    if tag:
        ser += b"|hmac=" + tag.encode()
    return ser

def _sign_bundle(self, adapter, text: str, payload_obj: Dict, wallet_label: str, step_tag: str):
    signed_text = adapter.sign_message_text(text)
    out_file = OUT_DIR / "signed" / f"{step_tag}-{wallet_label}.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(signed_text, f, ensure_ascii=False, indent=2)
    if self.eip712 and isinstance(adapter, EvmAdapter):
        typed = adapter.sign_eip712(payload_obj, chain_id=self.chain_id)
        out_file2 = OUT_DIR / "signed" / f"{step_tag}-{wallet_label}-eip712.json"
        with out_file2.open("w", encoding="utf-8") as f:
            json.dump(typed, f, ensure_ascii=False, indent=2)
    return signed_text

def _inject_bundle(self, adapter, payload: bytes, seq: int):
    payload_path = OUT_DIR / "payloads" / f"{seq:09d}.bin"
    with payload_path.open("wb") as f:
        f.write(payload)
    return adapter.inject_payload_bytes(payload)

def _maybe_broadcast(self, adapter, payload: bytes, seq: int) -> Optional[Dict]:
    if not self.broadcast or (seq % self.broadcast_every != 0):
        return None
    if not hasattr(adapter, "send_calldata_tx"):
        return {"skip": "broadcast not supported for this wallet type"}
    try:
        receipt = adapter.send_calldata_tx(payload, chain_id=self.chain_id)
    except Exception as e:
        receipt = {"error": str(e)}
    (OUT_DIR / "tx" / f"{seq:09d}.json").write_text(json.dumps(receipt, indent=2))
    return receipt

def _flush_rollup_if_full(self, adapter: EvmAdapter):
    if not self.rollup.full():
        return
    root_hex, proofs = self.rollup.root_and_proofs()
    root_dir = OUT_DIR / "merkle" / root_hex
    root_dir.mkdir(parents=True, exist_ok=True)
    # Save proofs per leaf
    for bundle in proofs:
        (root_dir / f"leaf_{bundle['seq']:09d}.json").write_text(json.dumps(bundle, indent=2))
    # Broadcast the root (as calldata) if requested
    if self.broadcast and isinstance(adapter, EvmAdapter):
        try:
            payload = json.dumps({"merkle_root": root_hex, "algo": "sha256"}).encode()
            receipt = adapter.send_calldata_tx(payload, chain_id=self.chain_id)
        except Exception as e:
            receipt = {"error": str(e)}
        (OUT_DIR / "tx" / f"rollup_{root_hex}.json").write_text(json.dumps(receipt, indent=2))
        write_jsonl({"ts": utc_now_iso(), "action": "rollup_broadcast", "root": root_hex, "result": receipt})
    else:
        write_jsonl({"ts": utc_now_iso(), "action": "rollup_ready", "root": root_hex})
    self.rollup.reset()

def _plot_cycle(self, cycle_i: int):
    if not (_HAS_MPL and self.plot):
        return
    xs = list(range(self.steps_per_cycle))
    ys = [amplitude_cosine(s, self.steps_per_cycle) for s in xs]
    plt.figure()
    plt.plot(xs, ys)
    plt.title(f"Omega Sine Envelope — Cycle {cycle_i}")
    plt.xlabel("Step")
    plt.ylabel("Amplitude")
    plt.tight_layout()
    outp = OUT_DIR / "plots" / f"cycle_{cycle_i:03d}.png"
    plt.savefig(outp)
    plt.close()

def _heartbeat(self):
    HEARTBEAT_PATH.write_text(utc_now_iso())

def _update_status(self, **kw):
    with _status_lock:
        _last_status.update(kw)

def run(self, *, realtime: bool = False, once: bool = False):
    step_duration_sec = (self.cycle_minutes * 60) / float(self.steps_per_cycle)

    while True:
        for step_i in range(self.start_step, self.steps_per_cycle):
            amp = amplitude_cosine(step_i, self.steps_per_cycle)
            wallet = self.wallets[step_i % len(self.wallets)]
            adapter = get_adapter(wallet, self.rpc_url)

            step_tag = f"c{self.cycle_i:03d}-s{step_i:03d}"
            payload_obj = {
                "seq": self.seq_global,
                "cycle": self.cycle_i,
                "step": step_i,
                "amp": round(amp, 6),
                "anchor": ANCHOR_PHRASE,
            }

            info = {
                "ts": utc_now_iso(),
                "cycle": self.cycle_i,
                "step": step_i,
                "amp": round(amp, 6),
                "wallet": wallet.name,
                "address": getattr(adapter, "address", "n/a"),
                "anchor": ANCHOR_PHRASE,
                "seq": self.seq_global,
            }

```

> **Note:** The supplied transcript ended mid-step during the signing loop. The excerpt above preserves every line that was present in the original submission.
