#!/usr/bin/env python3
"""Pull the assets listed in assets.txt from the server into <out_dir>,
then follow url() references inside fetched CSS until nothing new appears.

Usage: python3 -I fetch_assets.py <out_dir>
"""
import os
import posixpath
import re
import subprocess
import sys
from urllib.parse import unquote

HOST = "myhost"  # your SSH alias
DOMAIN = "example.com"
DOCROOT = "www/example.com/public_html/"
# Copied whole: the theme's JS lazy-loads files that no page names directly.
WHOLE_DIRS = ["wp-content/themes/kalium/assets/"]
CSS_URL = re.compile(r'url\(\s*["\']?([^"\')]+)["\']?\s*\)')


def rsync(paths, out):
    listing = os.path.join(out, ".files-from")
    with open(listing, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(paths)) + "\n")
    # Exit 23 = some listed files don't exist on the server; reported below.
    r = subprocess.run(["rsync", "-a", "--files-from", listing, f"{HOST}:{DOCROOT}", out],
                       stderr=subprocess.DEVNULL)
    if r.returncode not in (0, 23):
        raise RuntimeError(f"rsync failed with exit {r.returncode}")
    os.remove(listing)


def css_refs(out, css_path):
    path = os.path.join(out, css_path)
    text = open(path, encoding="utf-8", errors="ignore").read()
    # SiteGround's combined CSS uses absolute URLs: make them root-relative so
    # icon fonts get fetched here and load in local preview (no cross-origin).
    local = re.sub(rf"(?:https?:)?//{re.escape(DOMAIN)}/", "/", text)
    if local != text:
        with open(path, "w", encoding="utf-8") as f:
            f.write(local)
        text = local
    refs = set()
    for raw in CSS_URL.findall(text):
        ref = raw.split("?")[0].split("#")[0]
        if not ref or ref.startswith(("data:", "http:", "https:", "//")):
            continue
        if ref.startswith("/"):
            path = posixpath.normpath(ref.lstrip("/"))
        else:
            path = posixpath.normpath(posixpath.join(posixpath.dirname(css_path), ref))
        refs.add(unquote(path))
    return refs


def main(out):
    os.makedirs(out, exist_ok=True)
    for d in WHOLE_DIRS:
        os.makedirs(os.path.join(out, d), exist_ok=True)
        subprocess.run(["rsync", "-a", f"{HOST}:{DOCROOT}{d}", os.path.join(out, d)], check=True)
    wanted = {l.strip() for l in open("assets.txt", encoding="utf-8") if l.strip()}
    done, scanned = set(), set()
    while wanted - done:
        batch = wanted - done
        rsync(batch, out)
        done |= batch
        for p in sorted(done - scanned):
            scanned.add(p)
            if p.endswith(".css") and os.path.exists(os.path.join(out, p)):
                wanted |= css_refs(out, p)
    missing = sorted(p for p in done if not os.path.exists(os.path.join(out, p)))
    with open("missing.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(missing) + "\n")
    print(f"{len(done)} assets requested, {len(missing)} missing (see missing.txt)")


if __name__ == "__main__":
    main(sys.argv[1])
