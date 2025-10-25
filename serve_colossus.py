#!/usr/bin/env python3
"""
serve_colossus.py  —  stdlib-only viewer + API for Echo Colossus

Features
- Serves a zero-dependency HTML app with instant search and infinite scroll
- JSON API:
    GET /api/puzzles?offset=0&limit=100
    GET /api/puzzle/<id>
    GET /api/search?q=<term>&limit=100
    GET /api/lineage.dot
    GET /api/verify          # returns verification summary + recomputed rollup
- Live rollup verification: recomputes every file hash and compares to summary
- Optional lineage PNG rendering if Graphviz `dot` is on PATH

Usage
  python serve_colossus.py --root ./echo_colossus --port 8080
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path.cwd()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def iter_records(root: pathlib.Path):
    data_dir = root / "data" / "puzzles"
    for path in sorted(data_dir.glob("puzzle_*.json")):
        yield path


def load_record(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_summary(root: pathlib.Path):
    summary_path = root / "build" / "proofs" / "verification_summary.json"
    if not summary_path.exists():
        return None
    return json.loads(summary_path.read_text(encoding="utf-8"))


def recompute_rollup(root: pathlib.Path) -> dict:
    files = {}
    for path in iter_records(root):
        rel = str(path.relative_to(root))
        files[rel] = sha256_hex(path.read_bytes())
    rollup = sha256_hex(
        json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    )
    return {"files": files, "rollup_sha256": rollup, "total_files": len(files)}


def try_render_lineage_png(root: pathlib.Path) -> bytes | None:
    dot_file = root / "build" / "lineage" / "lineage.dot"
    if not dot_file.exists():
        return None
    try:
        result = subprocess.run(
            ["dot", "-Tpng", str(dot_file)],
            capture_output=True,
            check=True,
        )
        return result.stdout
    except Exception:
        return None


INDEX_HTML = """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Echo Colossus Explorer</title>
<style>
:root{--bg:#0b0f14;--fg:#e6eef7;--mut:#8aa1b4;--acc:#56b6c2;--chip:#1b2836;--card:#0f141b;--br:#1c2734}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.45 system-ui,Segoe UI,Roboto}
header{position:sticky;top:0;z-index:2;background:linear-gradient(180deg,#0b0f14 0%,#0b0f14cc 60%,#0b0f1400 100%);backdrop-filter:saturate(120%) blur(6px);border-bottom:1px solid var(--br)}
.wrap{max-width:1100px;margin:auto;padding:16px}
h1{margin:0 0 8px 0;font-size:22px}
.search{display:flex;gap:10px;align-items:center}
input[type=search]{flex:1;padding:10px 12px;border:1px solid var(--br);border-radius:10px;background:var(--card);color:var(--fg)}
button{background:var(--acc);color:#001215;border:0;border-radius:10px;padding:10px 12px;font-weight:600;cursor:pointer}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin-top:14px}
.card{background:var(--card);border:1px solid var(--br);border-radius:14px;padding:12px;min-height:120px;display:flex;flex-direction:column}
.id{font-weight:700}
.addr{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color:#c4f1ff}
.meta{color:var(--mut);font-size:13px;margin-top:4px}
a{color:#9ddff1}
footer{color:var(--mut);text-align:center;padding:28px}
.kv{display:grid;grid-template-columns:120px 1fr;gap:6px 10px}
.kv div:nth-child(odd){color:var(--mut)}
.drawer{position:fixed;inset:auto 0 0 0;background:#0b0f14f0;border-top:1px solid var(--br);backdrop-filter:blur(6px);max-height:70vh;overflow:auto;transform:translateY(100%);transition:.2s;z-index:3}
.drawer.open{transform:none}
pre{white-space:pre-wrap;word-break:break-word;background:#081019;border:1px solid #0e2233;padding:10px;border-radius:10px}
.badge{display:inline-block;background:var(--chip);padding:2px 8px;border-radius:999px;font-size:12px;border:1px solid var(--br);color:#cbe7ff}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
img{max-width:100%;border-radius:10px;border:1px solid var(--br)}
.small{font-size:12px}
</style>
<header><div class="wrap">
  <h1>Echo Colossus Explorer</h1>
  <div class="search">
    <input id="q" type="search" placeholder="Search id, address, or hash160… (e.g., 42 or 1ABC… or a1b2c3)">
    <button id="verify">Verify</button>
  </div>
  <div class="row small" id="stat"></div>
</div></header>
<main class="wrap">
  <div id="grid" class="grid"></div>
  <div id="more" style="text-align:center;margin:14px;"><button>Load more</button></div>
</main>
<div class="drawer" id="drawer"><div class="wrap" id="drawerContent"></div></div>
<footer>Built with ❤️ and only the Python stdlib</footer>
<script>
const grid = document.getElementById('grid');
const more = document.querySelector('#more button');
const stat = document.getElementById('stat');
const drawer = document.getElementById('drawer');
const drawerContent = document.getElementById('drawerContent');
const q = document.getElementById('q');

let offset = 0, limit = 60, total = 0, mode = 'browse', lastQ = '';

function chip(text){return `<span class="badge">${text}</span>`}
function card(p){
  return `<div class="card">
    <div class="id">#${p.id} — ${p.name}</div>
    <div class="addr">${p.address_base58}</div>
    <div class="meta">${chip(p.hash160.slice(0,8))} ${chip('checksum:'+p.checksum.slice(0,8))}</div>
    <div style="margin-top:auto"><button onclick="openDetail(${p.id})">Open</button></div>
  </div>`;
}
function setStat(){ stat.innerHTML = `${chip('mode:'+mode)} ${chip('loaded:'+grid.childElementCount)} ${total?chip('total:'+total):''}` }

async function loadBatch(){
  const url = mode==='browse'
    ? `/api/puzzles?offset=${offset}&limit=${limit}`
    : `/api/search?q=${encodeURIComponent(lastQ)}&limit=${limit}&offset=${offset}`;
  const r = await fetch(url); const j = await r.json();
  total = j.total||0; setStat();
  const frag = document.createDocumentFragment();
  j.data.forEach(p=>{ const d=document.createElement('div'); d.innerHTML=card(p); frag.appendChild(d.firstChild); });
  grid.appendChild(frag);
  offset += j.data.length;
  more.disabled = (offset >= total);
}
more.onclick = loadBatch;

async function openDetail(id){
  const r = await fetch(`/api/puzzle/${id}`); const p = await r.json();
  drawerContent.innerHTML = `
  <div class="row" style="justify-content:space-between;align-items:center;margin:12px 0">
    <h2 style="margin:0">#${p.id} — ${p.name}</h2>
    <button onclick="drawer.classList.remove('open')">Close</button>
  </div>
  <div class="kv">
    <div>Address</div><div class="addr">${p.address_base58}</div>
    <div>hash160</div><div class="small">${p.hash160}</div>
    <div>checksum</div><div class="small">${p.checksum}</div>
  </div>
  <h3>Script</h3>
  <pre>${p.script}</pre>
  <h3>Lineage preview</h3>
  <div id="lg">loading…</div>`;
  drawer.classList.add('open');
  // try PNG first, fall back to DOT text
  try{
    const img = new Image(); img.onload=()=>{document.getElementById('lg').innerHTML=''; document.getElementById('lg').appendChild(img);};
    img.onerror=async()=>{ const t=await (await fetch('/api/lineage.dot')).text(); document.getElementById('lg').innerHTML = '<pre>'+t.slice(0,8000)+'</pre>'; };
    img.src = '/api/lineage.png';
  }catch(e){}
}

q.addEventListener('keydown', e=>{
  if(e.key==='Enter'){ doSearch(); }
});
async function doSearch(){
  const v = q.value.trim();
  grid.innerHTML=''; offset=0; lastQ=v;
  mode = v? 'search' : 'browse';
  await loadBatch();
}

document.getElementById('verify').onclick = async ()=>{
  const r = await fetch('/api/verify'); const j = await r.json();
  const ok = j.summary && j.recomputed && j.summary.rollup_sha256===j.recomputed.rollup_sha256;
  alert((ok?'✓ OK ':'✗ MISMATCH ') + '\nsummary: '+(j.summary&&j.summary.rollup_sha256)+'\nrecomputed: '+(j.recomputed&&j.recomputed.rollup_sha256));
};

loadBatch();
</script>
"""


class App(BaseHTTPRequestHandler):
    server_version = "EchoColossus/1.0"

    def _send(self, code: int = 200, ctype: str = "application/json", body: bytes = b"", headers: dict | None = None) -> None:
        self.send_response(code)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Type", ctype)
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler API)
        try:
            if self.path == "/" or self.path.startswith("/index.html"):
                self._send(200, "text/html; charset=utf-8", INDEX_HTML.encode())
                return

            if self.path.startswith("/api/puzzles"):
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                offset = int(qs.get("offset", ["0"])[0])
                limit = int(qs.get("limit", ["100"])[0])
                files = list(iter_records(ROOT))
                slice_files = files[offset : offset + limit]
                data = [load_record(path) for path in slice_files]
                self._send(200, body=json.dumps({"total": len(files), "data": data}).encode())
                return

            if self.path.startswith("/api/puzzle/"):
                match = re.match(r"^/api/puzzle/(\d+)$", self.path)
                if not match:
                    self._send(404, body=b'{"error":"bad id"}')
                    return
                puzzle_id = int(match.group(1))
                puzzle_path = ROOT / "data" / "puzzles" / f"puzzle_{puzzle_id:05d}.json"
                if not puzzle_path.exists():
                    self._send(404, body=b'{"error":"not found"}')
                    return
                self._send(200, body=puzzle_path.read_bytes())
                return

            if self.path.startswith("/api/search"):
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                term = (qs.get("q", [""])[0] or "").lower().strip()
                offset = int(qs.get("offset", ["0"])[0])
                limit = int(qs.get("limit", ["100"])[0])
                files = list(iter_records(ROOT))
                matches = []
                for path in files:
                    record = load_record(path)
                    if (
                        not term
                        or term in str(record["id"]).lower()
                        or term in record["address_base58"].lower()
                        or term in record["hash160"].lower()
                    ):
                        matches.append(record)
                total = len(matches)
                data = matches[offset : offset + limit]
                self._send(200, body=json.dumps({"total": total, "data": data}).encode())
                return

            if self.path.startswith("/api/lineage.dot"):
                dot_path = ROOT / "build" / "lineage" / "lineage.dot"
                if not dot_path.exists():
                    self._send(404, body=b'{"error":"no lineage"}')
                    return
                self._send(200, "text/vnd.graphviz", dot_path.read_bytes())
                return

            if self.path.startswith("/api/lineage.png"):
                img = try_render_lineage_png(ROOT)
                if img:
                    self._send(200, "image/png", img, headers={"Cache-Control": "max-age=60"})
                    return
                self._send(404, body=b'{"error":"dot not available"}')
                return

            if self.path.startswith("/api/verify"):
                summary = load_summary(ROOT)
                recomputed = recompute_rollup(ROOT)
                ok = (
                    summary is not None
                    and summary.get("rollup_sha256") == recomputed["rollup_sha256"]
                )
                payload = {"ok": bool(ok), "summary": summary, "recomputed": recomputed}
                self._send(200, body=json.dumps(payload).encode())
                return

            local = ROOT / self.path.lstrip("/")
            if local.exists() and local.is_file():
                ctype = "application/octet-stream"
                if str(local).endswith(".json"):
                    ctype = "application/json"
                if str(local).endswith(".md"):
                    ctype = "text/markdown; charset=utf-8"
                if str(local).endswith(".png"):
                    ctype = "image/png"
                self._send(200, ctype, local.read_bytes())
                return

            self._send(404, body=b'{"error":"not found"}')
        except Exception as exc:  # pragma: no cover - defensive guard
            self._send(
                500,
                body=json.dumps({"error": "server error", "detail": str(exc)}).encode(),
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=str, default="./echo_colossus")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    global ROOT
    ROOT = pathlib.Path(args.root).resolve()
    if not (ROOT / "data" / "puzzles").exists():
        print(
            f"[!] dataset not found in {ROOT}. Run the generator first.",
            file=sys.stderr,
        )
        sys.exit(1)

    server = ThreadingHTTPServer(("0.0.0.0", args.port), App)
    print(f"Echo Colossus @ http://localhost:{args.port}  (root={ROOT})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover - CLI UX
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
