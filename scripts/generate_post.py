#!/usr/bin/env python3
import csv, datetime, html, pathlib, re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
BLOG_DIR  = REPO_ROOT / "blog"
CNT_DIR   = REPO_ROOT / "content"
TOPICS_CSV = CNT_DIR / "topics.csv"
SITEMAP   = REPO_ROOT / "sitemap.xml"
SITE_URL  = "https://gwsautomate.com"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} | GWS Automate</title>
  <meta name="description" content="{meta_desc}" />
  <style>
    body {{ font-family: system-ui, -apple-system, Arial, sans-serif; line-height: 1.6; margin: 40px; max-width: 800px; color: #111; }}
    h1 {{ font-size: 28px; margin-bottom: 16px; }}
    h2 {{ margin-top: 24px; font-size: 22px; }}
    pre {{ background: #f4f4f4; padding: 12px; border-radius: 8px; overflow-x: auto; }}
    a {{ color: #2563eb; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .muted {{ color:#555; font-size:0.9rem }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p class="muted"><em>Published: {date} · Author: GWS Automate</em></p>

  {body}

  <h2>Next Steps</h2>
  <p>{cta_text} — <a href="https://itautomator.gumroad.com/l/google-workspace-automation-starter" target="_blank">Starter Pack</a> or <a href="https://itautomator.gumroad.com/l/google-workspace-automation-pro" target="_blank">Pro Pack</a>.</p>

  <p><a href="/blog/">← Back to Blog</a></p>
</body>
</html>
"""

def load_topics():
    with open(TOPICS_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def choose_next(topics):
    for t in topics:
        slug = t["slug"].strip()
        out = BLOG_DIR / f"{slug}.html"
        if not out.exists():
            return t, out
    return None, None

def make_post_html(t):
    title = t["title"]
    meta_desc = (t["summary"][:155] if t["summary"] else title).replace('"','')
    cta_text = t["cta_text"] or "Want ready-to-use scripts?"
    sections = [s.strip() for s in t["sections"].split("|") if s.strip()]

    body_parts = []
    if t["summary"]:
        body_parts.append(f"<p>{html.escape(t['summary'])}</p>")
    for sec in sections:
        body_parts.append(f"<h2>{sec}</h2>\n<p>{title} — {sec.lower()}.</p>")

    return HTML_TEMPLATE.format(
        title=title,
        meta_desc=meta_desc,
        date=datetime.date.today().strftime("%B %d, %Y"),
        body="\n\n".join(body_parts),
        cta_text=cta_text
    )

def update_sitemap(slug):
    url = f"{SITE_URL}/blog/{slug}.html"
    if not SITEMAP.exists():
        base = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{SITE_URL}/</loc><priority>1.0</priority></url>
</urlset>"""
        SITEMAP.write_text(base, encoding="utf-8")
    xml = SITEMAP.read_text(encoding="utf-8")
    if url not in xml:
        xml = xml.replace("</urlset>", f"  <url><loc>{url}</loc><priority>0.8</priority></url>\n</urlset>")
        SITEMAP.write_text(xml, encoding="utf-8")

def update_blog_index():
    items = []
    for p in BLOG_DIR.glob("*.html"):
        if p.name == "index.html": continue
        txt = p.read_text(encoding="utf-8")
        m = re.search(r"<h1[^>]*>(.*?)</h1>", txt)
        title = m.group(1) if m else p.name
        items.append((p.name, title))
    links = "\n".join(f'<li><a href="/blog/{n}">{t}</a></li>' for n,t in sorted(items))
    idx = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Blog | GWS Automate</title><body><h1>Blog</h1><ul>{links}</ul><p><a href="/index.html">← Back to Home</a></p></body></html>"""
    (BLOG_DIR / "index.html").write_text(idx, encoding="utf-8")

def main():
    BLOG_DIR.mkdir(exist_ok=True)
    topics = load_topics()
    t, out_path = choose_next(topics)
    if not t: 
        print("No new topics")
        return
    html_post = make_post_html(t)
    out_path.write_text(html_post, encoding="utf-8")
    update_sitemap(t["slug"])
    update_blog_index()
    print(f"Generated {out_path}")

if __name__ == "__main__":
    main()
