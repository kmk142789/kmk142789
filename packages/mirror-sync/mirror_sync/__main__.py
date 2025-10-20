import asyncio, yaml, pathlib, markdown, json, os
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
        r = render(md)
        out = OUT / (md.stem + ".html")
        out.write_text(r["html"], encoding="utf-8")
        drafts.append({"file": md.name, "title": r["meta"]["title"]})
    print(json.dumps({"prepared": drafts, "mirror": "skipped"}, indent=2))

async def prepare_with_browser():
    drafts = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=MIRROR_HEADLESS)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        for md in sorted(POSTS.glob("*.md")):
            r = render(md)
            out = OUT / (md.stem + ".html")
            out.write_text(r["html"], encoding="utf-8")
            await post_to_mirror(page, r["html"], r["meta"]["title"], r["meta"].get("tags"))
            drafts.append({"file": md.name, "title": r["meta"]["title"]})
        print(json.dumps({"prepared": drafts}, indent=2))
        await browser.close()

async def main():
    if MIRROR_SKIP_BROWSER:
        await prepare_without_browser()
    else:
        await prepare_with_browser()

if __name__ == "__main__":
    asyncio.run(main())
