#!/usr/bin/env python3
"""Delete files under wp-content/ and wp-includes/ that no page uses.

Usage: python3 -I prune.py <site_dir> [--apply]

Kept: anything referenced from the HTML (src, srcset, lightbox links, inline
JSON), anything a kept stylesheet points at with url(), and anything listed in
used-*.txt (used-desktop.txt / used-mobile.txt: files the browser requested in
audit.py runs, which covers what scripts load on their own). Without --apply it
only reports; --apply refuses to run without any used-*.txt.
"""
import glob
import os
import posixpath
import re
import sys
import unicodedata
from urllib.parse import unquote

# Stop at ?, & and #: "?ver=" and share-link "&amp;" tails are not part of the path.
ASSET_RE = re.compile(r'/(?:wp-content|wp-includes)/[^"\'\s<>()\\,?&#]+')
CSS_URL = re.compile(r'url\(\s*["\']?([^"\')]+)["\']?\s*\)')
TOP = ("wp-content/", "wp-includes/")


def in_wp_dir(path, site):
    """True for files under wp-content/, wp-includes/ … of the site. Checks the
    path *inside* the site folder only, so a project path like ~/wp-sites/ is fine."""
    rel = os.path.relpath(path, site)
    return rel.split(os.sep)[0].startswith("wp-")


def nfc(path):
    return unicodedata.normalize("NFC", path)


def html_refs(site):
    refs = set()
    for root, _, files in os.walk(site):
        if in_wp_dir(root, site):
            continue
        for name in files:
            if name.endswith(".html"):
                text = open(os.path.join(root, name), encoding="utf-8").read().replace("\\/", "/")
                refs.update(unquote(r).lstrip("/") for r in ASSET_RE.findall(text))
    return refs


def css_refs(site, css):
    text = open(os.path.join(site, css), encoding="utf-8", errors="ignore").read()
    out = set()
    for raw in CSS_URL.findall(text):
        ref = raw.split("?")[0].split("#")[0]
        if not ref or ref.startswith(("data:", "http:", "https:", "//")):
            continue
        path = posixpath.normpath(ref.lstrip("/") if ref.startswith("/") else posixpath.join(posixpath.dirname(css), ref))
        out.add(unquote(path))
    return out


def main(site, apply):
    keep = html_refs(site)
    used_files = glob.glob("used-*.txt")
    if apply and not used_files:
        sys.exit("No used-*.txt here: run audit.py (desktop and --mobile) from this folder first, "
                 "or files loaded only by scripts get deleted.")
    for f in used_files:
        keep.update(l.strip() for l in open(f, encoding="utf-8") if l.strip().startswith(TOP))
    todo = [k for k in keep if k.endswith(".css")]
    while todo:
        css = todo.pop()
        if not os.path.exists(os.path.join(site, css)):
            continue
        for ref in css_refs(site, css) - keep:
            keep.add(ref)
            if ref.endswith(".css"):
                todo.append(ref)
    keep_nfc = {nfc(k) for k in keep}
    missing = sorted(k for k in keep if k.startswith(TOP) and "*" not in k and not os.path.exists(os.path.join(site, k)))
    drop, freed = [], 0
    for top in TOP:
        for root, _, files in os.walk(os.path.join(site, top)):
            for name in files:
                rel = os.path.relpath(os.path.join(root, name), site)
                if nfc(rel) not in keep_nfc:
                    drop.append(rel)
                    freed += os.path.getsize(os.path.join(site, rel))
    print(f"keep {len(keep)} refs, drop {len(drop)} files ({freed / 1e6:.0f} MB)")
    if missing:
        print("referenced but missing:", *missing[:20], sep="\n  ")
    if apply:
        for rel in drop:
            os.remove(os.path.join(site, rel))
        for top in TOP:
            for root, dirs, files in os.walk(os.path.join(site, top), topdown=False):
                if not os.listdir(root):
                    os.rmdir(root)


if __name__ == "__main__":
    main(sys.argv[1], "--apply" in sys.argv)
