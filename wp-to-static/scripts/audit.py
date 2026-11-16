#!/usr/bin/env python3
"""Load every page in headless Chromium, scroll to the bottom, and record what
it downloads: bytes on the wire, request count, DOM size, EcoIndex grade.
Also writes used.txt, the local files any page actually requested.

Usage: <venv>/bin/python -I audit.py <base_url> <site_dir> [--mobile]
"""
import collections
import os
import sys
from urllib.parse import unquote, urlparse

from playwright.sync_api import sync_playwright

Q_DOM = [0, 47, 75, 159, 233, 298, 358, 417, 476, 537, 603, 674, 753, 843, 949, 1076, 1237, 1459, 1801, 2479, 594601]
Q_REQ = [0, 2, 15, 25, 34, 42, 49, 56, 63, 70, 78, 86, 95, 105, 117, 130, 147, 170, 205, 281, 3920]
Q_KB = [0, 1.37, 144.7, 319.53, 479.46, 631.97, 783.38, 937.91, 1098.62, 1265.47, 1448.32, 1648.27,
        1876.08, 2142.06, 2465.37, 2866.31, 3401.59, 4155.73, 5400.08, 8037.54, 223212.26]


def quantile(qs, v):
    for i in range(1, len(qs)):
        if v < qs[i]:
            return i - 1 + (v - qs[i - 1]) / (qs[i] - qs[i - 1])
    return len(qs) - 1


def ecoindex(dom, req, kb):
    score = 100 - 5 * (3 * quantile(Q_DOM, dom) + 2 * quantile(Q_REQ, req) + quantile(Q_KB, kb)) / 6
    grade = next(g for t, g in [(80, "A"), (70, "B"), (55, "C"), (40, "D"), (25, "E"), (10, "F"), (-1, "G")] if score > t)
    return round(score), grade


def pages(site):
    for root, _, files in os.walk(site):
        if "index.html" in files and "/wp-" not in root:
            yield "/" + os.path.relpath(root, site).replace(".", "").strip("/") + "/"


def main(base, site, mobile):
    base = base.rstrip("/")
    used = set()
    rows = []
    totals = collections.Counter()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(**(p.devices["iPhone 13"] if mobile else {"viewport": {"width": 1440, "height": 900}}))
        for path in sorted(set(pages(site))):
            path = path.replace("//", "/")
            page = ctx.new_page()
            cdp = ctx.new_cdp_session(page)
            cdp.send("Network.enable")
            cdp.send("Network.setCacheDisabled", {"cacheDisabled": True})
            sizes, kinds = {}, {}
            cdp.on("Network.loadingFinished", lambda e: sizes.__setitem__(e["requestId"], e["encodedDataLength"]))
            cdp.on("Network.responseReceived", lambda e: kinds.__setitem__(e["requestId"], (e["response"]["url"], e["type"])))
            page.goto(base + path, wait_until="load")
            page.wait_for_timeout(2000)
            for _ in range(30):
                if page.evaluate("window.scrollY + innerHeight >= document.body.scrollHeight - 5"):
                    break
                page.mouse.wheel(0, 800)
                page.wait_for_timeout(150)
            page.wait_for_timeout(1500)
            dom = page.evaluate("document.getElementsByTagName('*').length")
            by_type = collections.Counter()
            for rid, n in sizes.items():
                url, kind = kinds.get(rid, ("", "Other"))
                by_type[kind] += n
                rows.append(f"{path}\t{kind}\t{n}\t{url}")
                u = urlparse(url)
                if u.netloc == urlparse(base).netloc:
                    used.add(unquote(u.path).lstrip("/"))
            kb = sum(sizes.values()) / 1024
            score, grade = ecoindex(dom, len(sizes), kb)
            top = ", ".join(f"{k} {v / 1024:.0f}" for k, v in by_type.most_common(4))
            print(f"{path:58} {kb:7.0f} KB {len(sizes):3} req {dom:5} dom  {grade} {score:3}  [{top}]", flush=True)
            totals["kb"] += kb
            totals["n"] += 1
            page.close()
        browser.close()
    print(f"average {totals['kb'] / totals['n']:.0f} KB over {totals['n']} pages")
    with open("requests.tsv", "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")
    with open("used.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(used)) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], "--mobile" in sys.argv)
