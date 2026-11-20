#!/usr/bin/env python3
"""Point every public page at the site's real address.

The pages, sitemap and share tags used to name innovatorsleague.com, a domain this
project does not own. This script rewrites those references to SITE_BASE. It is
idempotent: run it again with a new base if the site ever moves to its own domain.

    python3 scripts/set_site_url.py                 # use the default base below
    python3 scripts/set_site_url.py https://example.org

Email addresses and workflow bot identities are left alone on purpose.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE = "https://paleofaire.github.io/innovators-league"
OLD_HOSTS = ["innovatorsleague.com", "www.innovatorsleague.com"]
TARGETS = sorted(ROOT.glob("*.html")) + sorted((ROOT / "transformation").glob("*.html")) + [
    ROOT / "sitemap.xml", ROOT / "robots.txt", ROOT / "config.js",
    ROOT / "structured-data.js", ROOT / "sector-landing.js",
]


def rewrite(text: str, base: str, previous: list) -> str:
    base = base.rstrip("/")
    bare = re.sub(r"^https?://", "", base)
    for old in previous:
        # Full URLs first: https://old/ and https://old (no path) both become base + "/"
        text = re.sub(r"https?://" + re.escape(old) + r"/", base + "/", text)
        text = re.sub(r"https?://" + re.escape(old) + r"(?![\w.-])", base + "/", text)
        # Visible mentions without a scheme. Skip email addresses and anything already inside a URL or host.
        text = re.sub(r"(?<![@/\w.-])" + re.escape(old) + r"(?![\w.-])", bare, text)
    return text


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE
    previous = sorted(OLD_HOSTS, key=len, reverse=True)
    changed = 0
    for path in TARGETS:
        if not path.exists():
            continue
        before = path.read_text(encoding="utf-8")
        after = rewrite(before, base, previous)
        if after != before:
            path.write_text(after, encoding="utf-8")
            changed += 1
    print(f"site base: {base} | files rewritten: {changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
