#!/usr/bin/env python3
"""Pixel-diff every page between two servers (before vs after an eco step, or
live vs local): full page on desktop 1440 and iPhone 13, mobile menu open,
project lightbox open + one arrow step. Flags pages over 0.5 % changed pixels
and writes a -diff.png next to the shot.

Lazy-loaded photos that hadn't arrived yet are the usual false alarm: rerun the
flagged pages only (pass their paths) - the waits are long for that reason.
Selectors are Kalium's (MENU_TOGGLE, LIGHTBOX_LINK): adapt per theme.

Usage: <venv>/bin/python -I compare_shots.py <before_url> <after_url> <site_dir> <out_dir> [desktop paths to redo...]
"""
import os, sys
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright
BEFORE, AFTER, site, out = sys.argv[1:5]
os.makedirs(out, exist_ok=True)
ONLY = ({("desk", x) for x in sys.argv[5:]} | {("phone", x) for x in sys.argv[5:]}) if sys.argv[5:] else None
MENU_TOGGLE, LIGHTBOX_LINK = ".toggle-bars", "a[data-lightbox-gallery]"
paths = ["/404.html"] + sorted(("/" + os.path.relpath(r, site).replace(".", "").strip("/") + "/").replace("//", "/") for r, _, f in os.walk(site) if "index.html" in f and "/wp-" not in r)
def shoot(ctx, base, path, state):
    pg = ctx.new_page(); pg.goto(base + path, wait_until="load"); pg.wait_for_timeout(500)
    for _ in range(40): pg.mouse.wheel(0, 500); pg.wait_for_timeout(200)
    pg.wait_for_timeout(2500); pg.evaluate("scrollTo(0,0)"); pg.wait_for_timeout(700)
    if state == "menu":
        t = pg.locator(MENU_TOGGLE)
        if not (t.count() and t.first.is_visible()): pg.close(); return None
        t.first.click(); pg.wait_for_timeout(1000)
    if state == "lb":
        a = pg.locator(LIGHTBOX_LINK + ":visible")
        if not a.count(): pg.close(); return None
        a.first.click(); pg.wait_for_timeout(1500); pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(1500)
    f = f"{out}/{abs(hash((base,path,state,ctx._n)))}.png"
    pg.screenshot(path=f, full_page=(state == "full"), animations="disabled"); pg.close(); return f
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, opts in {"desk": {"viewport": {"width": 1440, "height": 900}}, "phone": p.devices["iPhone 13"]}.items():
        ctx = b.new_context(**opts); ctx._n = name
        for path in paths:
            for state in ("full", "menu", "lb"):
                if state == "menu" and name == "desk": continue
                if state == "lb" and not path.startswith("/work/") or (state == "lb" and path == "/work/"): continue
                if ONLY and (name, path) not in ONLY: continue
                try: a = shoot(ctx, BEFORE, path, state); c = shoot(ctx, AFTER, path, state)
                except Exception as e: print("ERR", name, state, path, str(e)[:80]); continue
                if not a: continue
                A, C = Image.open(a).convert("RGB"), Image.open(c).convert("RGB")
                if A.size != C.size:
                    print(f"SIZE {name} {state} {path} {A.size} -> {C.size}"); continue
                d = ImageChops.difference(A, C).convert("L").point(lambda v: 255 if v > 40 else 0)
                pct = 100 * sum(d.histogram()[255:]) / (A.size[0] * A.size[1])
                flag = "  <--" if pct > 0.5 else ""
                print(f"{pct:6.2f}% {name:5} {state:4} {path}{flag}", flush=True)
                if pct > 0.5: d.save(c.replace(".png", "-diff.png")); print("      ", a, c)
        ctx.close()
