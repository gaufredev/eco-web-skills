#!/usr/bin/env python3
"""Snapshot every page's DOM after its scripts ran, in several states (desktop,
tablet, mobile; scrolled; menu open; lightbox open; grid hover), for slim.py --purge.
Selectors below are Kalium's: adapt MENU_TOGGLE / LIGHTBOX_LINK / GRID_LINK per theme.

Usage: <venv>/bin/python -I snapshot_doms.py http://localhost:8766 site <out_dir>
"""

import os, sys
from playwright.sync_api import sync_playwright
base, site, out = sys.argv[1], sys.argv[2], sys.argv[3]
MENU_TOGGLE, LIGHTBOX_LINK, GRID_LINK = ".toggle-bars", "a[data-lightbox-gallery]", ".portfolio-item a, .thumb a"
os.makedirs(out, exist_ok=True)
paths = ["/404.html"] + sorted("/" + os.path.relpath(r, site).replace(".", "").strip("/") + "/" for r, _, f in os.walk(site) if "index.html" in f and "/wp-" not in r)
paths = [p.replace("//", "/") for p in paths]
n = 0
def snap(pg, tag):
    global n; n += 1
    open(os.path.join(out, f"{n:04d}-{tag}.html"), "w").write(pg.content())
with sync_playwright() as p:
    b = p.chromium.launch()
    views = {"d1920": {"viewport": {"width": 1920, "height": 1080}}, "d1280": {"viewport": {"width": 1280, "height": 800}},
             "t1024": {"viewport": {"width": 1024, "height": 768}}, "t768": {"viewport": {"width": 768, "height": 1024}, "has_touch": True},
             "m": p.devices["iPhone 13"]}
    for vk, opts in views.items():
        ctx = b.new_context(**opts)
        for path in paths:
            pg = ctx.new_page(); pg.goto(base + path, wait_until="load"); pg.wait_for_timeout(600)
            for _ in range(25):
                pg.mouse.wheel(0, 900); pg.wait_for_timeout(80)
            pg.wait_for_timeout(500); snap(pg, vk + "-scrolled")
            pg.mouse.wheel(0, -400); pg.wait_for_timeout(400); snap(pg, vk + "-up")
            pg.evaluate("scrollTo(0,0)"); pg.wait_for_timeout(400)
            t = pg.locator(MENU_TOGGLE)
            if t.count() and t.first.is_visible():
                t.first.click(); pg.wait_for_timeout(800); snap(pg, vk + "-menu"); t.first.click(force=True); pg.wait_for_timeout(500)
            a = pg.locator(LIGHTBOX_LINK + ":visible")
            if a.count() and vk in ("d1280", "m"):
                a.first.scroll_into_view_if_needed(); a.first.click(); pg.wait_for_timeout(1200); snap(pg, vk + "-lb")
                pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(900); snap(pg, vk + "-lb2"); pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
            g = pg.locator(GRID_LINK).first
            if vk == "d1280" and g.count():
                try: g.hover(timeout=2000); pg.wait_for_timeout(500); snap(pg, vk + "-hover")
                except Exception: pass
            pg.close()
        ctx.close()
    b.close()
print(n, "snapshots")
