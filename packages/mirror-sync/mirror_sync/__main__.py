import argparse
import asyncio, yaml, pathlib, markdown, json, os, hashlib, datetime, importlib
from jinja2 import Template
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parents[3]
POSTS = ROOT / "posts"
OUT   = ROOT / "out/mirror_drafts"
OUT.mkdir(parents=True, exist_ok=True)

HTML_TMPL = Template("""
<article>
  <h1>{{ title }}</h1>
  {% if summary %}<p><em>{{ summary }}</em></p>{% endif %}
  {{ body | safe }}
  {% if canonical_url %}<p><small>Canonical: <a href="{{ canonical_url }}">{{ canonical_url }}</a></small></p>{% endif %}
</article>
""")

MIRROR_SKIP_BROWSER = os.environ.get("MIRROR_SYNC_SKIP_BROWSER") == "1"
MIRROR_HEADLESS = os.environ.get("MIRROR_SYNC_HEADLESS") == "1"
MIRROR_IPFS_ENDPOINT = os.environ.get("MIRROR_SYNC_IPFS_API")
MIRROR_IPFS_TOKEN = os.environ.get("MIRROR_SYNC_IPFS_TOKEN")
MIRROR_BRIDGE_TARGETS = os.environ.get("MIRROR_SYNC_BRIDGE_TARGETS")


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()

def render(md_path: pathlib.Path) -> dict:
    text = md_path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Missing front matter in {md_path}")
    _, fm, body_md = parts
    meta = yaml.safe_load(fm.strip())
    html = markdown.markdown(body_md.strip(), extensions=["extra", "toc"])
    html_doc = HTML_TMPL.render(body=html, **meta)
    return {"meta": meta, "html": html_doc}

async def post_to_mirror(page, html, title, tags):
    # 1) assumes you are already logged in on first run (Mirror remembers)
    await page.goto("https://mirror.xyz/new", wait_until="domcontentloaded")
    # 2) Fill the title/content (Mirror editor uses contenteditable)
    await page.locator('[data-testid="post-title"]').fill(title)
    editor = page.locator('[data-testid="post-body"]')
    await editor.click()
    await page.keyboard.insert_text(html)
    # 3) set tags (optional – UI may differ; kept resilient)
    for tag in (tags or []):
        try:
            await page.get_by_placeholder("Add tag").fill(tag)
            await page.keyboard.press("Enter")
        except Exception:
            pass
    # Leave as draft; you click publish + sign
    await page.wait_for_timeout(500)
    return True

async def prepare_without_browser():
    drafts = []
    for md in sorted(POSTS.glob("*.md")):
        rendered = render(md)
        out = OUT / (md.stem + ".html")
        out.write_text(rendered["html"], encoding="utf-8")
        drafts.append(
            {
                "file": md.name,
                "title": rendered["meta"]["title"],
                "output": str(out.relative_to(ROOT)),
                "sha256": sha256_file(out),
            }
        )
    return drafts


async def prepare_with_browser():
    drafts = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=MIRROR_HEADLESS)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        for md in sorted(POSTS.glob("*.md")):
            rendered = render(md)
            out = OUT / (md.stem + ".html")
            out.write_text(rendered["html"], encoding="utf-8")
            await post_to_mirror(page, rendered["html"], rendered["meta"]["title"], rendered["meta"].get("tags"))
            drafts.append(
                {
                    "file": md.name,
                    "title": rendered["meta"]["title"],
                    "output": str(out.relative_to(ROOT)),
                    "sha256": sha256_file(out),
                }
            )
        await browser.close()
    return drafts


def push_to_ipfs(ipfs_endpoint: str | None, ipfs_token: str | None):
    spec = importlib.util.find_spec("ipfshttpclient")
    if spec is None:
        return {"cid": None, "status": "ipfshttpclient not installed"}

    import ipfshttpclient  # type: ignore

    if not ipfs_endpoint:
        return {"cid": None, "status": "IPFS endpoint not provided"}

    headers = {"Authorization": f"Bearer {ipfs_token}"} if ipfs_token else None
    try:
        client = ipfshttpclient.connect(ipfs_endpoint, session=True, headers=headers)
        added = client.add(str(OUT), recursive=True, wrap_with_directory=True)
        # When wrapping, the last item is the directory CID
        cid = next((item["Hash"] for item in reversed(added) if item.get("Hash")), None)
        return {"cid": cid, "status": "pushed" if cid else "push failed"}
    except Exception as exc:  # pragma: no cover - defensive
        return {"cid": None, "status": f"push error: {exc}"}


def write_bridge_manifest(drafts, cid=None, bridge_targets=None):
    manifest = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "ipfs": {"cid": cid} if cid else None,
        "bridge_targets": bridge_targets or [],
        "drafts": drafts,
    }
    manifest_path = OUT / "bridge_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path

async def main():
    parser = argparse.ArgumentParser(description="Prepare Mirror drafts and optional IPFS bundles")
    parser.add_argument("--skip-browser", action="store_true", help="Render drafts without opening Mirror")
    parser.add_argument("--push-ipfs", action="store_true", help="Push generated drafts to an IPFS endpoint")
    parser.add_argument("--bridge-targets", help="Comma-separated bridge targets for downstream servers")
    parser.add_argument("--ipfs-endpoint", help="IPFS API multiaddr (defaults to MIRROR_SYNC_IPFS_API)")
    parser.add_argument("--ipfs-token", help="Optional bearer token for IPFS endpoint auth")
    args = parser.parse_args()

    skip_browser = args.skip_browser or MIRROR_SKIP_BROWSER
    ipfs_endpoint = args.ipfs_endpoint or MIRROR_IPFS_ENDPOINT
    ipfs_token = args.ipfs_token or MIRROR_IPFS_TOKEN
    bridge_targets = (
        [t.strip() for t in (args.bridge_targets or MIRROR_BRIDGE_TARGETS or "").split(",") if t.strip()]
    )

    if skip_browser:
        drafts = await prepare_without_browser()
        mirror_status = "skipped"
    else:
        drafts = await prepare_with_browser()
        mirror_status = "posted"

    ipfs_status = {"cid": None, "status": "skipped"}
    if args.push_ipfs:
        ipfs_status = push_to_ipfs(ipfs_endpoint, ipfs_token)

    manifest_path = write_bridge_manifest(drafts, ipfs_status.get("cid"), bridge_targets)
    print(
        json.dumps(
            {
                "prepared": drafts,
                "mirror": mirror_status,
                "ipfs": ipfs_status,
                "bridge_manifest": str(manifest_path.relative_to(ROOT)),
            },
            indent=2,
        )
    )

if __name__ == "__main__":
    asyncio.run(main())
