#!/usr/bin/env python3
"""Assemble the static example.com site from the crawled HTML.

Usage: python3 -I build.py <raw_dir> <out_dir>

- Drops the removed projects from the Work grid and rebuilds the project
  prev/next links from the remaining grid order.
- Replaces the contact form with a plain mailto link.
- Strips WordPress-only <head> tags, the dead Universal Analytics tag and
  scripts no page uses (Revolution Slider, comment-reply).
- Rewrites internal URLs to root-relative (canonical / og: / JSON-LD stay
  absolute for SEO).
- Writes assets.txt: every local asset the pages reference, for fetch_assets.sh.
"""
import datetime
import os
import re
import sys
from urllib.parse import unquote

DOMAIN = "example.com"
EMAIL = "hello@example.com"
# Pages nothing links to: the theme's empty blog placeholder and a broken shortcode page.
SKIP_PAGES = {"blog", "online-marketing"}
REMOVED = {"old-project-1", "old-project-2"}  # slugs to drop

WP_HEAD_PATTERNS = [
    r'<link[^>]+rel=["\']https://api\.w\.org/["\'][^>]*>\s*',
    r'<link[^>]+rel=["\']EditURI["\'][^>]*>\s*',
    r'<link[^>]+rel=["\']wlwmanifest["\'][^>]*>\s*',
    r'<link[^>]+rel=["\']shortlink["\'][^>]*>\s*',
    r'<link[^>]+rel=["\']pingback["\'][^>]*>\s*',
    r'<link[^>]+type=["\'](?:application|text)/(?:json\+oembed|xml\+oembed|json)["\'][^>]*>\s*',
    r'<link[^>]+type=["\']application/rss\+xml["\'][^>]*>\s*',
    r'<meta[^>]+name=["\']generator["\'][^>]*>\s*',
    # Universal Analytics stopped collecting data in 2023.
    r'<script[^>]+src=["\']https://www\.googletagmanager\.com/gtag/js[^>]*>\s*</script>\s*',
    r'<script>\s*window\.dataLayer[^<]*</script>\s*',
    r'<!-- Global site tag \(gtag\.js\)[^>]*-->\s*',
    r'<script[^>]+src=["\'][^"\']*/(?:rs6|rbtools|comment-reply)\.min\.js[^"\']*["\'][^>]*>\s*</script>\s*',
]

PROTECT = re.compile(
    r'<link[^>]+rel=["\'](?:canonical|alternate)["\'][^>]*>'
    r'|<meta[^>]+(?:property|name)=["\'](?:og:|twitter:)[^>]*>'
    r'|<script[^>]+type=["\']application/ld\+json["\'][^>]*>.*?</script>',
    re.S | re.I,
)

# Stop at ?, & and #: "?ver=" and share-link "&amp;" tails are not part of the path.
ASSET_RE = re.compile(r'/(?:wp-content|wp-includes)/[^"\'\s<>()\\,?&#]+')


def in_wp_dir(path, site):
    """True for files under wp-content/, wp-includes/ … of the site. Checks the
    path *inside* the site folder only, so a project path like ~/wp-sites/ is fine."""
    rel = os.path.relpath(path, site)
    return rel.split(os.sep)[0].startswith("wp-")


def page_url(root, site):
    """URL path of the folder holding an index.html ("/" for the site root)."""
    rel = os.path.relpath(root, site)
    return "/" if rel == "." else "/" + rel.replace(os.sep, "/").strip("/") + "/"


def div_end(html: str, start: int) -> int:
    """Index just past the </div> that closes the <div> opening at start."""
    depth = 0
    for m in re.compile(r'<div\b|</div>').finditer(html, start):
        depth += 1 if m.group(0) == '<div' else -1
        if depth == 0:
            return m.end()
    raise ValueError("unbalanced div")


def drop_removed_items(html: str) -> str:
    for m in reversed(list(re.finditer(r'<div class="portfolio-item ', html))):
        end = div_end(html, m.start())
        slug = re.search(rf'href="https://{DOMAIN}/work/([^/"]+)/"', html[m.start():end])
        if slug and slug.group(1) in REMOVED:
            html = html[:m.start()] + html[end:]
    return html


def grid_order(work_html: str) -> list:
    slugs = re.findall(rf'<div class="photo"> <a href="https://{DOMAIN}/work/([^/"]+)/"', work_html)
    return list(dict.fromkeys(slugs))


def fix_nav(html: str, slug: str, order: list) -> str:
    """Previous = next tile in the grid, Next = previous tile (as on the live site)."""
    if slug not in order:
        print(f"warning: work/{slug}/ is not in the Work grid; prev/next links left as they were")
        return html
    i = order.index(slug)
    targets = {"previous": order[i + 1] if i + 1 < len(order) else None,
               "next": order[i - 1] if i > 0 else None}
    for cls, target in targets.items():
        def repl(m, target=target):
            if target is None:
                return ""
            return re.sub(r'href="[^"]*"', f'href="https://{DOMAIN}/work/{target}/"', m.group(0))
        html = re.sub(rf'<a class="{cls} (?:pc|mobile)-only" href="[^"]*">.*?</a>', repl, html)
    return html


def fix_contact(html: str) -> str:
    """Mail text only: the form, office address and map are gone."""
    old_text = (f'<p>Write us an e-mail via the form,<br /> or just send us an e-mail directly at<br /> {EMAIL}</p>'
                f'<p>양식에 맞춰 메일을 쓰시거나 {EMAIL}으로 직접 메일을 보내주십시오.</p>')
    if old_text not in html:
        raise ValueError("contact text not found")
    html = html.replace(old_text, (
        f'<p>Send us an e-mail at<br /> 여기로 메일을 보내주십시오<br /> <a href="mailto:{EMAIL}">{EMAIL}</a></p>'))
    office = html.find('<h4>Office.</h4>')
    start = html.rfind('<div class="wpb_text_column', 0, office)
    if office < 0 or start < 0:
        raise ValueError("office block not found")
    html = html[:start] + html[div_end(html, start):]
    start = html.find('<div class="wpb_column vc_column_container vc_col-sm-8">')
    if start < 0:
        raise ValueError("map/form column not found")
    return html[:start] + html[div_end(html, start):]


GREEN_CHECK = "https://www.thegreenwebfoundation.org/green-web-check/?url=example.com"
ECO_NOTE = (
    '<div class="container eco-note" style="padding-bottom:24px;font-size:12px;line-height:1.6;color:#777">'
    '<p style="margin:0">Built light: static pages, no database, no trackers, and videos that load only when you press play.</p>'
    # Add a green-hosting line only if the Green Web Check says green, and word it as
    # "servers the Green Web Foundation lists as green" with a link to {GREEN_CHECK}.
    # Hosts change; a stale green claim is worse than none.
    '<p style="margin:0">가볍게 만든 웹사이트입니다. 데이터베이스와 추적 도구 없이 정적 페이지로 운영되며, 영상은 재생할 때만 불러옵니다.</p></div>'
)


def fix_404(html: str) -> str:
    """Site-styled 404: own wording, links back into the site, kept out of search."""
    old = re.search(r'<p class="error-text">.*?</div>', html, re.S)
    if not old:
        raise ValueError("404 text not found")
    text = ('<p class="error-text">Page not found</p>'
            '<p>This page doesn’t exist or has moved.<br /> 요청하신 페이지가 없거나 이동되었습니다.</p>'
            '<p>Go to the <a href="/">home page</a>, see our <a href="/work/">work</a>'
            ' or <a href="/contact/">get in touch</a>.</p></div>')
    html = html[:old.start()] + text + html[old.end():]
    return html.replace("<title>", '<meta name="robots" content="noindex" />\n<title>', 1)


def fix_footer(html: str) -> str:
    """Drop the social links (Instagram is down, Facebook unused in Korea) and the
    mobile-menu search, which needs WordPress; keep the copyright year current."""
    html = re.sub(r'<ul class="social-networks textual">.*?</ul>', "", html, flags=re.S)
    html = re.sub(r'<form role="search".*?</form>', "", html, flags=re.S)
    i = html.rfind("</footer>")
    if i < 0:
        raise ValueError("footer not found")
    html = html[:i] + ECO_NOTE + html[i:]
    year = datetime.date.today().year
    return html.replace(
        "© Copyright 2020.",
        f'© Copyright <span id="copyright-year">{year}</span>.'
        '<script>document.getElementById("copyright-year").textContent=new Date().getFullYear()</script>')


def rewrite_urls(text: str) -> str:
    for scheme in ("https:", "http:", ""):
        text = text.replace(f"{scheme}//{DOMAIN}/", "/")
        text = text.replace(f'{scheme}//{DOMAIN}"', '/"')
        esc = scheme.replace("/", "\\/")
        text = text.replace(f"{esc}\\/\\/{DOMAIN}\\/", "\\/")
    return text


def rewrite_html(html: str) -> str:
    for pat in WP_HEAD_PATTERNS:
        html = re.sub(pat, "", html, flags=re.I)
    saved = []

    def stash(m):
        saved.append(m.group(0))
        return f"\x00{len(saved) - 1}\x00"

    html = rewrite_urls(PROTECT.sub(stash, html))
    return re.sub(r"\x00(\d+)\x00", lambda m: saved[int(m.group(1))], html)


def write_extras(out):
    """Copy extras/ (.htaccess, robots.txt) and write sitemap.xml."""
    extras = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extras")
    for name in os.listdir(extras):
        with open(os.path.join(extras, name), "rb") as src, open(os.path.join(out, name), "wb") as dst:
            dst.write(src.read())
    urls = sorted(page_url(root, out) for root, _, files in os.walk(out)
                  if "index.html" in files and not in_wp_dir(root, out))
    entries = "".join(f"<url><loc>https://{DOMAIN}{u}</loc></url>\n" for u in urls)
    with open(os.path.join(out, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + entries + "</urlset>\n")


def main(raw, out):
    # Clear old pages only: fetched assets and root extras (naver*.html,
    # google*.html verification files) live in the same tree.
    for root, _, files in os.walk(out):
        for name in files:
            if (name == "index.html" or (name == "404.html" and root == out)) and not in_wp_dir(root, out):
                os.remove(os.path.join(root, name))
    work = open(os.path.join(raw, "work/index.html"), encoding="utf-8").read()
    order = grid_order(drop_removed_items(work))
    assets = set()
    for root, _, files in os.walk(raw):
        for name in files:
            if not name.endswith(".html"):
                continue
            src = os.path.join(root, name)
            rel = os.path.relpath(src, raw)
            if rel.split(os.sep)[0] in SKIP_PAGES:
                continue
            html = open(src, encoding="utf-8").read()
            parts = rel.split(os.sep)
            if rel == "work/index.html":
                html = drop_removed_items(html)
            elif parts[0] == "work" and len(parts) == 3:
                html = fix_nav(html, parts[1], order)
            elif rel == "404.html":
                html = fix_404(html)
            elif rel == "contact/index.html":
                html = fix_contact(html)
            html = rewrite_html(fix_footer(html))
            leftover = [s for s in REMOVED if f"/work/{s}/" in html]
            if leftover:
                raise ValueError(f"{rel} still links to {leftover}")
            assets.update(unquote(a) for a in ASSET_RE.findall(html.replace("\\/", "/")) if "*" not in a)
            dst = os.path.join(out, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w", encoding="utf-8") as f:
                f.write(html)
    write_extras(out)
    with open("assets.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(a.lstrip("/") for a in assets)) + "\n")
    print(f"{len(order)} projects, {len(assets)} asset refs")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
