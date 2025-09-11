#!/usr/bin/env python3
import csv, datetime, html, pathlib, re

# --- paths ---
REPO_ROOT  = pathlib.Path(__file__).resolve().parents[1]
BLOG_DIR   = REPO_ROOT / "blog"
CONTENT    = REPO_ROOT / "content"
TOPICS_CSV = CONTENT / "topics.csv"
SITEMAP    = REPO_ROOT / "sitemap.xml"
SITE_URL   = "https://gwsautomate.com"

# --- layout template ---
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} | GWS Automate</title>
  <meta name="description" content="{meta_desc}" />
  <style>
    body {{ font-family: system-ui, -apple-system, Arial, sans-serif; line-height:1.65; margin:40px auto; max-width:820px; color:#111; }}
    h1 {{ font-size:32px; margin:.2rem 0 1rem }}
    h2 {{ font-size:22px; margin:1.6rem 0 .5rem }}
    p  {{ margin:.6rem 0 }}
    ul {{ margin:.4rem 0 .8rem 1.2rem }}
    pre{{ background:#f4f4f4; padding:12px; border-radius:8px; overflow:auto }}
    .muted{{ color:#555; font-size:.9rem }}
    a  {{ color:#2563eb; text-decoration:none }}
    a:hover{{ text-decoration:underline }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p class="muted"><em>Published: {date} · Author: GWS Automate</em></p>

  {body}

  <h2>Next Steps</h2>
  <p>{cta_text} — <a href="https://itautomator.gumroad.com/l/google-workspace-automation-starter" target="_blank">Starter Pack</a>
  or <a href="https://itautomator.gumroad.com/l/google-workspace-automation-pro" target="_blank">Pro Pack</a>.</p>

  <p><a href="/blog/">← Back to Blog</a></p>
</body>
</html>
"""

# --- curated copy library so sections read naturally (no repetition) ---
SECTION_COPY = {
  "inbox-zero-classifier": {
    "Introduction": "Classify by sender/subject, label important items, and auto-archive low-value mail.",
    "Why automate Inbox Zero": "Automation prevents distraction and lets teams focus on action-able messages.",
    "How the classifier works": "Apps Script scans recent threads, applies labels (Action, Read Later, Notifications), archives newsletters.",
    "Starter rules & labels": "Begin with obvious patterns (alerts, newsletters); whitelist key senders; iterate weekly.",
    "Scheduling & maintenance": "Run every 10–15 minutes; review label counts; keep a changelog of rule changes.",
    "Results & pitfalls": "Expect 60–80% faster triage. Watch for over-aggressive archiving and misclassified alerts."
  },
  "onboarding": {
    "The problem with manual onboarding": "Steps are spread across Admin, Groups and Gmail; it’s slow and error-prone.",
    "Why Apps Script + Admin SDK": "Native to Workspace, secure via OAuth, and easy to maintain in a Sheet.",
    "What this automation does": "Creates users, assigns org units, adds groups, and applies Gmail defaults consistently.",
    "Script outline": "Core calls: AdminDirectory.Users.insert and AdminDirectory.Members.insert. Keep rules in a Sheet.",
    "Common pitfalls": "Missing Admin SDK scopes, bad orgUnitPath (must start with '/'), misspelled group addresses.",
    "Results": "Typically a 70–80% time reduction and far fewer access mistakes."
  },
  "offboarding": {
    "Risks of manual offboarding": "Delays leave access open; automation ensures immediate lock-down and transfer.",
    "Suspend & secure": "Suspend, reset sign-in cookies, revoke tokens to cut off access right away.",
    "Drive transfer": "Transfer ownership to a manager/service account; verify shared drives and quotas.",
    "Groups & aliases cleanup": "Remove from groups, shared inboxes, aliases; document any residual access.",
    "Archive & retention policy": "Apply consistent retention/legal hold before deletion to meet compliance."
  }
}

# --- helpers to render sections nicely ---
def render_section(slug: str, heading: str) -> str:
    lib = SECTION_COPY.get(slug, {})
    return lib.get(heading, f"This section explains: {heading}.")

def load_topics():
    with open(TOPICS_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def choose_next(topics):
    """Pick the first topic whose target file doesn't exist yet."""
    for t in topics:
        slug = t["slug"].strip()
        out  = BLOG_DIR / f"{slug}.html"
        if not out.exists():
            return t, out
    return None, None

def make_post_html(t):
    slug = t["slug"].strip()
    title = t["title"].strip()
    meta_desc = (t.get("summary") or title)[:155].replace('"','')
    cta_text  = t.get("cta_text") or "Want ready-to-use scripts and templates?"
    sections  = [s.strip() for s in (t.get("sections") or "").split("|") if s.strip()]

    parts = []
    if t.get("summary"):
        parts.append(f"<p>{html.escape(t['summary'])}</p>")
    for h in sections:
        parts.append(f"<h2>{h}</h2>\n<p>{render_section(slug, h)}</p>")

    return HTML_TEMPLATE.format(
        title=title,
        meta_desc=meta_desc,
        date=datetime.date.today().strftime("%B %d, %Y"),
        body="\n\n".join(parts),
        cta_text=cta_text
    )

def update_sitemap(slug: str):
    url = f"{SITE_URL}/blog/{slug}.html"
    if not SITEMAP.exists():
        base = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{SITE_URL}/</loc><priority>1.0</priority></url>
  <url><loc>{SITE_URL}/blog/</loc><priority>0.6</priority></url>
</urlset>"""
        SITEMAP.write_text(base, encoding="utf-8")
    xml = SITEMAP.read_text(encoding="utf-8")
    if url not in xml:
        xml = xml.replace(
            "</urlset>",
            f'  <url><loc>{url}</loc><priority>0.8</priority></url>\n</urlset>'
        )
        SITEMAP.write_text(xml, encoding="utf-8")

# build /blog/index.html automatically (newest first, de-duplicate by title)
TITLE_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
PARA_RE  = re.compile(r"<p[^>]*>(.*?)</p>",  re.IGNORECASE | re.DOTALL)
def strip_tags(s: str) -> str: return re.sub(r"<[^>]+>", "", s)

def human_date(path: pathlib.Path) -> str:
    ts = datetime.datetime.fromtimestamp(path.stat().st_mtime)
    return ts.strftime("%b %d, %Y")

def update_blog_index():
    posts, seen = [], set()
    for p in BLOG_DIR.glob("*.html"):
        if p.name.lower() == "index.html": continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        m  = TITLE_RE.search(txt)
        title = strip_tags(m.group(1)).strip() if m else p.stem.replace("-", " ").title()
        if title.lower() in seen:  # skip duplicates by title
            continue
        seen.add(title.lower())
        m2 = PARA_RE.search(txt)
        snippet = strip_tags(m2.group(1)).strip() if m2 else ""
        posts.append({
            "name": p.name, "title": title, "snippet": snippet,
            "date": human_date(p), "mtime": p.stat().st_mtime
        })
    posts.sort(key=lambda x: x["mtime"], reverse=True)
    links = "\n".join(
        f'''    <li>
      <a href="/blog/{p["name"]}">{html.escape(p["title"])}</a>
      <div class="muted">{p["date"]} — {html.escape(p["snippet"][:140])}</div>
    </li>''' for p in posts
    )
    idx = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Blog | GWS Automate</title>
  <meta name="description" content="Guides and tutorials for automating Google Workspace (Apps Script, Admin SDK, Gmail).">
  <style>
    body{{font-family:system-ui,-apple-system,Arial,sans-serif;line-height:1.65;margin:40px auto;max-width:820px;color:#111}}
    h1{{font-size:28px;margin-bottom:16px}}
    ul{{padding-left:20px}} li{{margin-bottom:14px}}
    a{{color:#2563eb;text-decoration:none}} a:hover{{text-decoration:underline}}
    .muted{{color:#555;font-size:.9rem}}
  </style>
</head>
<body>
  <h1>GWS Automate Blog</h1>
  <ul>
{links}
  </ul>
  <p><a href="/index.html">← Back to Home</a></p>
</body>
</html>"""
    (BLOG_DIR / "index.html").write_text(idx, encoding="utf-8")

def main():
    BLOG_DIR.mkdir(parents=True, exist_ok=True)
    topics = load_topics()
    topic, out_path = choose_next(topics)
    if not topic:
        print("No new topics to post — add rows to content/topics.csv"); return
    html_post = make_post_html(topic)
    out_path.write_text(html_post, encoding="utf-8")
    update_sitemap(topic["slug"].strip())
    update_blog_index()
    print(f"Generated: blog/{out_path.name}")

if __name__ == "__main__":
    main()
