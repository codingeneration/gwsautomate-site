#!/usr/bin/env python3
import pathlib, re

GA_ID = "G-4HY7P3F737"  # <<-- PUT YOUR GA4 MEASUREMENT ID HERE

SNIPPET = f"""
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_ID}');
</script>
""".strip()

ROOT = pathlib.Path(".")
HTML_FILES = list(ROOT.glob("*.html")) + list((ROOT / "blog").glob("*.html"))

def has_ga(html: str) -> bool:
    return (GA_ID in html) or ("googletagmanager.com/gtag/js?id=" in html)

def inject(html: str) -> str:
    if has_ga(html):
        return html
    # insert before closing </head>
    return re.sub(r"</head>", SNIPPET + "\n</head>", html, flags=re.IGNORECASE, count=1)

def main():
    changed = 0
    for f in HTML_FILES:
        txt = f.read_text(encoding="utf-8", errors="ignore")
        if "</head>" not in txt.lower():
            continue  # skip odd files
        new = inject(txt)
        if new != txt:
            f.write_text(new, encoding="utf-8")
            changed += 1
            print(f"Injected GA into: {f}")
    print(f"Done. Files updated: {changed}")

if __name__ == "__main__":
    main()
