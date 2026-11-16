#!/usr/bin/env python3
"""Second round of design-neutral weight cuts, run after eco.py (first used on a
Kalium agency site: CSS 80–128 KB -> 23–31 KB gzipped per page).

Usage:
  python3 -I slim.py <site_dir>                    # HTML cuts + install purged CSS from cache/
  python3 -I slim.py <site_dir> --purge <doms_dir> # first regenerate the purged CSS
                                                   # (<doms_dir> from snapshot_doms.py)

1. WordPress's emoji loader goes (inline settings, module script, styles, and the
   wp-emoji-release.min.js it fetches). Browsers draw emoji natively.
2. Revolution Slider leftovers go when no page has a slider (no rs-module).
3. Images lazy-loaded by lazysizes (Kalium and many other themes bundle it) get
   `data-sizes="auto"`: lazysizes measures the real column width, so a 665 px
   column stops downloading the 1536 px file on 1x screens. Retina screens still
   get the large file. Skipped automatically when the theme has no lazysizes.
4. Unused CSS rules are removed from every stylesheet the pages link under
   wp-content/ or wp-includes/ (whole theme + WooCommerce + sliders + icon sets).
   PurgeCSS keeps any rule whose class/id/tag appears in the built HTML, in the
   site's JS (classes scripts toggle), or in post-JS DOM snapshots (desktop,
   tablet, mobile; menu open; lightbox open). Originals stay in
   cache/css-original/ and every purge starts from them, so it can be rerun.
   Check with compare_shots.py afterwards: pixel diff every page before/after.
"""
import glob
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(HERE, "cache", "css-original")
PURGED = os.path.join(HERE, "cache", "css-purged")

CUTS = [
    re.compile(r'<style id="wp-emoji-styles-inline-css">.*?</style>\s*', re.S),
    re.compile(r'<script id="wp-emoji-settings" type="application/json">.*?</script>\s*', re.S),
    re.compile(r'<script type="module">\s*/\*! This file is auto-generated \*/\s*var e="script#wp-emoji-settings".*?</script>\s*', re.S),
    re.compile(r'<script[^>]*>\s*window\._wpemojiSettings.*?</script>\s*', re.S),  # older WP versions
    re.compile(r'<script[^>]*src="[^"]*wp-emoji-release\.min\.js[^"]*"[^>]*></script>\s*'),
]
REV_CUTS = [
    re.compile(r'<script type="text/javascript">\s*function setREVStartSize\(e\)\{.*?</script>\s*', re.S),
    re.compile(r'<style id="rs-plugin-settings-inline-css">.*?</style>\s*', re.S),
]
SIZES_RE = re.compile(r'data-sizes="(?:auto, )?\(max-width: \d+px\) 100vw, \d+px"')
CSS_LINK = re.compile(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href="(/wp-(?:content|includes)/[^"?]+\.css)')

# Classes built at runtime by string concatenation are invisible to PurgeCSS.
# Broad on purpose: a few KB kept is cheap, a missing state rule is a visible bug.
SAFELIST_STANDARD = [r"^is-", r"^has-", r"^lazy", r"^nivo", r"^fluidbox", r"^lg-", r"^ytf", r"^mobile-menu",
                     r"^menu-", r"^toggle-bars", r"^sticky", r"^header-block", r"^site-header", r"^fullscreen-menu",
                     r"^top-menu", r"^sidebar-menu", r"^go-to-top", r"^portfolio-", r"^isotope", r"^packery",
                     r"^animate", r"^wow", r"^fade", r"^slide", r"^in-viewport", r"^visible", r"^hidden", r"^show",
                     r"^active", r"^current", r"^open", r"^opened", r"^closed", r"^hover", r"^loaded", r"^loading",
                     r"^pp_", r"^mfp-", r"^fancybox", r"^swiper", r"^owl-", r"^slick"]
SAFELIST_GREEDY = [r"lightbox", r"nivo", r"fluidbox", r"lazy", r"menu", r"sticky", r"header", r"prettyPhoto"]


def pages(site):
    return [p for p in glob.glob(os.path.join(site, "**/*.html"), recursive=True) if "/wp-" not in p]


def slim_html(path, drop_rev, lazysizes):
    html = original = open(path, encoding="utf-8").read()
    for cut in CUTS + (REV_CUTS if drop_rev else []):
        html = cut.sub("", html)
    if lazysizes:
        html = SIZES_RE.sub('data-sizes="auto"', html)
    if html != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
    return "wp-emoji" in html


def stylesheets(site):
    found = set()
    for p in pages(site):
        found.update(CSS_LINK.findall(open(p, encoding="utf-8").read()))
    return sorted(f.lstrip("/") for f in found if os.path.exists(os.path.join(site, f.lstrip("/"))))


def purge(site, doms):
    sheets = stylesheets(site)
    for rel in sheets:
        dst = os.path.join(ORIG, rel)
        if not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(site, rel), dst)
    shutil.rmtree(PURGED, ignore_errors=True)
    js = [p for pat in ("wp-content/**/*.js", "wp-includes/**/*.js")
          for p in glob.glob(os.path.join(site, pat), recursive=True)]
    content = [os.path.join(doms, "*.html"), os.path.join(site, "**/*.html")] + sorted(js)
    rx = lambda pats: "[" + ",".join(f"/{p}/" for p in pats) + "]"
    for rel in sheets:
        out = os.path.dirname(os.path.join(PURGED, rel))
        os.makedirs(out, exist_ok=True)
        cfg = os.path.join(out, "purgecss.config.cjs")
        with open(cfg, "w") as f:
            f.write("module.exports = {content: %s, css: [%s], output: %s, keyframes: false, fontFace: false, "
                    "variables: false, safelist: {standard: %s, greedy: %s}}\n"
                    % (repr(content), repr(os.path.join(ORIG, rel)), repr(out),
                       rx(SAFELIST_STANDARD), rx(SAFELIST_GREEDY)))
        subprocess.run(["npx", "--yes", "purgecss@6", "--config", cfg], check=True, cwd=out)
        os.remove(cfg)


def main(site, doms=None):
    all_html = "".join(open(p, encoding="utf-8").read() for p in pages(site))
    drop_rev = "rs-module" not in all_html
    lazysizes = any("lazySizes" in open(p, encoding="utf-8", errors="ignore").read()
                    for p in glob.glob(os.path.join(site, "wp-content/themes/**/*.js"), recursive=True))
    if doms:
        purge(site, doms)
    left = [p for p in pages(site) if slim_html(p, drop_rev, lazysizes)]
    print(f"RevSlider leftovers removed: {drop_rev}; lazysizes data-sizes=auto: {lazysizes}")
    print("pages still loading emoji code:", left or "none")
    n = 0
    for root, _, files in os.walk(PURGED):
        for name in files:
            if name.endswith(".css"):
                src = os.path.join(root, name)
                shutil.copy2(src, os.path.join(site, os.path.relpath(src, PURGED)))
                n += 1
    print(f"purged stylesheets installed: {n}")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[args.index("--purge") + 1] if "--purge" in args else None)
