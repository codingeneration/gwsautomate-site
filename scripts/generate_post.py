#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv, datetime, html, pathlib, re, sys

# ---------- Paths ----------
REPO_ROOT  = pathlib.Path(__file__).resolve().parents[1]
BLOG_DIR   = REPO_ROOT / "blog"
CONTENT    = REPO_ROOT / "content"
TOPICS_CSV = CONTENT / "topics.csv"
SITEMAP    = REPO_ROOT / "sitemap.xml"
SITE_URL   = "https://gwsautomate.com"  # change if needed

# ---------- HTML Layout ----------
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} | GWS Automate</title>
  <meta name="description" content="{meta_desc}" />
  <style>
    :root {{ --ink:#111; --muted:#555; --brand:#2563eb; --bg:#f7f7f8; }}
    body {{ font-family: system-ui, -apple-system, Arial, sans-serif; color:var(--ink); line-height:1.65; margin: 40px auto; max-width: 820px }}
    h1 {{ font-size:32px; margin:.2rem 0 1rem }}  h2 {{ font-size:22px; margin:1.6rem 0 .6rem }}
    p {{ margin:.6rem 0 }}  ul {{ margin:.4rem 0 .8rem 1.2rem }}
    pre {{ background:#f4f4f4; padding:12px; border-radius:8px; overflow:auto }}
    a {{ color:var(--brand); text-decoration:none }}  a:hover {{ text-decoration:underline }}
    .muted {{ color:var(--muted); font-size:.9rem }} .card {{ background:var(--bg); padding:14px 16px; border-radius:10px }}
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

# ---------- Curated copy library (prevents repetition) ----------
SECTION_COPY = {
  "inbox-zero-classifier": {
    "Introduction":
      "Classify by sender/subject, label important items, and auto-archive low-value mail so your inbox stays focused.",
    "Why automate Inbox Zero":
      "Automation prevents distractions and keeps your attention on action-able messages instead of newsletters and alerts.",
    "How the classifier works":
      "Apps Script scans recent threads, applies labels (Action, Read Later, Notifications), and archives newsletters automatically.",
    "Starter rules & labels":
      "Begin with obvious patterns (alerts, newsletters). Whitelist key senders. Iterate rules weekly based on misses.",
    "Scheduling & maintenance":
      "Run every 10–15 minutes on a time trigger. Review label counts and maintain a changelog of changes.",
    "Results & pitfalls":
      "Expect 60–80% faster triage. Watch for over-aggressive archiving and misclassified alerts, and tune rules accordingly."
  },
  "onboarding": {
    "The problem with manual onboarding":
      "Steps are spread across Admin, Groups and Gmail; it’s slow, inconsistent, and easy to miss key access.",
    "Why Apps Script + Admin SDK":
      "Native to Workspace, secure via OAuth, fast to deploy, and easy to maintain with a Google Sheet as the source of truth.",
    "What this automation does":
      "Creates users, assigns org units, adds mandatory groups, and applies Gmail defaults in a single, repeatable flow.",
    "Script outline":
      "Use AdminDirectory.Users.insert and AdminDirectory.Members.insert. Read rows from a Sheet and validate inputs.",
    "Common pitfalls":
      "Missing Admin SDK scopes, bad orgUnitPath (must start with '/'), and misspelled group addresses. Start with dry runs.",
    "Results":
      "Typically a 70–80% time reduction and far fewer access mistakes; scales well for MSPs and internal IT teams."
  },
  "offboarding": {
    "Risks of manual offboarding":
      "Delays leave access open; automation ensures immediate lock-down and consistent data handling.",
    "Suspend & secure":
      "Suspend the user, reset sign-in cookies, and revoke tokens to cut off access right away.",
    "Drive transfer":
      "Transfer ownership to a manager or service account; verify shared drives and quotas before deletion.",
    "Groups & aliases cleanup":
      "Remove the account from groups, shared inboxes, and aliases; document any residual access that needs attention.",
    "Archive & retention policy":
      "Apply consistent retention/legal hold policies prior to deletion to meet compliance requirements."
  }
}

# Accept common slug & heading variants
SLUG_ALIASES = {
  "google-workspace-onboarding-automation": "onboarding",
  "google-workspace-offboarding-automation": "offboarding",
  "inboxzero": "inbox-zero-classifier",
  "inbox_zero_classifier": "inbox-zero-classifier",
}
HEADING_ALIASES = {
  # onboarding
  "the problem with manual onboarding": "The problem with manual onboarding",
  "why apps script + admin sdk": "Why Apps Script + Admin SDK",
  "why apps script": "Why Apps Script + Admin SDK",
  "what this automation does": "What this automation does",
  "script outline": "Script outline",
  "common pitfalls": "Common pitfalls",
  "results": "Results",
  # inbox zero
  "introduction": "Introduction",
  "why automate inbox zero": "Why automate Inbox Zero",
  "how the classifier works": "How the classifier works",
  "starter rules & labels": "Starter rules & labels",
  "scheduling & maintenance": "Scheduling & maintenance",
  "results & pitfalls": "Results & pitfalls",
  # offboarding
  "risks of manual offboarding": "Risks of manual offboarding",
  "suspend & secure": "Suspend & secure",
  "drive transfer": "Drive transfer",
  "groups & aliases cleanup": "Groups & aliases cleanup",
  "archive & retention policy": "Archive & retention policy",
}

# ---------- Utilities ----------
def _norm(s: str) -> str:
  return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()

def canonical_slug(slug: str) -> str:
  s = (slug or "").strip().lower()
  return SLUG_ALIASES.get(s, s)

def canonical_heading(h: str) -> str:
  return HEADING_ALIASES.get(_norm(h), h)

def load_topics():
  if not TOPICS_CSV.exists():
    print(f"[error] topics.csv not found at {TOPICS_CSV}", file=sys.stderr)
    sys.exit(1)
  with open(TOPICS_CSV, newline="", encoding="utf-8") as f:
    return list(csv.DictReader(f))

def choose_next(topics):
  """Pick the first topic whose target blog file doesn't exist yet."""
  for t in topics:
    slug = canonical_slug(t.get("slug",""))
    if not slug:
      continue
    out = BLOG_DIR / f"{slug}.html"
    if not out.exists():
      return t, out
  return None, None

def render_section(slug: str, heading: str) -> str:
  cslug = canonical_slug(slug)
  chead = canonical_heading(heading)
  lib = SECTION_COPY.get(cslug, {})
  if chead in lib:
    return lib[chead]
  # graceful default (no title repetition)
  return f"This section covers {heading.lower()} with practical steps and pitfalls to avoid."

def make_post_html(t: dict) -> str:
  slug      = canonical_slug(t.get("slug",""))
  title     = (t.get("title") or slug.replace("-", " ").title()).strip()
  meta_desc = ((t.get("summary") or title)[:155]).replace('"','')
  cta_text  = t.get("cta_text") or "Want ready-to-use scripts and templates?"
  sections  = [s.strip() for s in (t.get("sections") or "").split("|") if s.strip()]

  parts = []
  if t.get("summary"):
    parts.append(f'<p class="card">{html.escape(t["summary"])}</p>')
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
    xml = xml.replace("</urlset>", f"  <url><loc>{url}</loc><priority>0.8</priority></url>\n</urlset>")
    SITEMAP.write_text(xml, encoding="utf-8")

# ---- Blog index helpers ----
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
    m   = TITLE_RE.search(txt)
    title = strip_tags(m.group(1)).strip() if m else p.stem.replace("-", " ").title()
    if title.lower() in seen:
      continue  # de-dup by title
    seen.add(title.lower())
    m2 = PARA_RE.search(txt)
    snippet = strip_tags(m2.group(1)).strip() if m2 else ""
    posts.append({"name": p.name, "title": title, "snippet": snippet,
                  "date": human_date(p), "mtime": p.stat().st_mtime})
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

# ---------- Main ----------
def main():
  BLOG_DIR.mkdir(parents=True, exist_ok=True)
  CONTENT.mkdir(parents=True, exist_ok=True)

  topics = load_topics()
  topic, out_path = choose_next(topics)
  if not topic:
    print("No new topics to post — add rows to content/topics.csv")
    return

  slug = canonical_slug(topic.get("slug",""))
  html_post = make_post_html(topic)
  out_path.write_text(html_post, encoding="utf-8")
  update_sitemap(slug)
  update_blog_index()
  print(f"Generated: blog/{out_path.name}")

if __name__ == "__main__":
  main()
