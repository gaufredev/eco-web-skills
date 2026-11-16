#!/usr/bin/env python3
"""Design-neutral weight reductions, run on the built site after build.py
and fetch_assets.py.

Usage: python3 -I eco.py <site_dir>

1. YouTube embeds become click-to-play previews (self-hosted thumbnail + the
   play button each embed showed before); the player loads only on click.
   The video.js / Vimeo scripts they needed are dropped.
2. Every uploaded JPG/PNG gets a WebP sibling (`image.jpg.webp`, kept only if
   clearly smaller) and HTML/CSS references point at it. Social-preview tags
   keep the original for compatibility.
3. Unused font preloads go (Roboto is never applied; the line icon font is
   only needed on hover in the Work grid). Icon elements stop carrying the
   Font Awesome class, which pulled an 80 KB font for no visible glyph.
"""
import html as htmllib
import json
import os
import re
import subprocess
import sys
import urllib.request
from urllib.parse import unquote

DOMAIN = "example.com"
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache", "youtube")
# Images whose WebP wasn't worth keeping, so later runs don't re-encode them.
# Kept outside the site folder: prune.py would delete marker files inside it.
NO_WEBP = os.path.join(HERE, "cache", "no-webp.txt")
POSTERS = "wp-content/uploads/video-posters"

PROTECT = re.compile(
    r'<link[^>]+rel=["\'](?:canonical|alternate|image_src|icon|shortcut icon|apple-touch-icon(?:-precomposed)?)["\'][^>]*>'
    r'|<meta[^>]+name=["\']msapplication-TileImage["\'][^>]*>'
    r'|<meta[^>]+(?:property|name)=["\'](?:og:|twitter:)[^>]*>'
    r'|<script[^>]+type=["\']application/ld\+json["\'][^>]*>.*?</script>',
    re.S | re.I,
)
IMG_RE = re.compile(r'((?:https://' + re.escape(DOMAIN) + r')?/wp-content/uploads/[^"\'\s()<>,;]+?\.(?:jpe?g|png))(?![\w.])', re.I)

# Any attribute order (WordPress's own oEmbed puts title/width/height before src),
# www or not, youtube.com or youtube-nocookie.com.
IFRAME_RE = re.compile(
    r'<iframe\b[^>]*?\bsrc="https?://(?:www\.)?youtube(?:-nocookie)?\.com/embed/([\w-]{11})[^"]*"[^>]*>\s*</iframe>', re.I)
VIDEOJS_RE = re.compile(r'<video[^>]*data-vsetup="[^"]*?(?:youtu\.be|watch\?v=)\\?/?([\w-]{11})[^"]*"[^>]*></video>')
VIDEO_SCRIPTS = re.compile(
    r'<script[^>]+src="[^"]*/(?:video-js/video|vimeo/player|kalium-videojs-youtube-js)\.min\.js[^"]*"[^>]*></script>\s*')
DROP_PRELOADS = re.compile(
    r'<link rel="preload" as="font" href="(?:https://fonts\.gstatic\.com/[^"]+|[^"]*/linea\.woff)" crossorigin/>\s*')

YT_PLAY = ('<svg class="ytf__play" viewBox="0 0 68 48" width="68" height="48" aria-hidden="true">'
           '<path d="M66.5 7.7c-.8-2.9-2.5-5.4-5.4-6.2C55.8.1 34 0 34 0S12.2.1 6.9 1.6C4 2.3 2.3 4.8 1.5 7.7 0 13 0 24 0 24'
           's0 11 1.5 16.3c.8 2.9 2.5 5.4 5.4 6.2C12.2 47.9 34 48 34 48s21.8-.1 27.1-1.6c2.9-.8 4.6-3.3 5.4-6.2'
           'C68 35 68 24 68 24s0-11-1.5-16.3z" fill="#f00"/><path d="M45 24 27 14v20z" fill="#fff"/></svg>')
VJS_PLAY = ('<svg class="ytf__play" viewBox="0 0 48 48" width="48" height="48" aria-hidden="true">'
            '<circle cx="24" cy="24" r="22.5" fill="rgba(0,0,0,.25)" stroke="#fff" stroke-width="2"/>'
            '<path d="M19 15.5 33 24l-14 8.5z" fill="#fff"/></svg>')
FACADE_HEAD = """<style>.ytf,.ytf-frame{position:absolute;inset:0;width:100%;height:100%;border:0;padding:0;margin:0}
.ytf{display:block;background:#000;cursor:pointer;overflow:hidden}
.ytf img{width:100%;height:100%;object-fit:cover;display:block}
.ytf__play{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);transition:opacity .2s}
.ytf--yt .ytf__play path:first-child{fill-opacity:.85}.ytf--yt:hover .ytf__play path:first-child{fill-opacity:1}
.ytf--vjs:hover .ytf__play{opacity:.8}
.ytf__title{position:absolute;left:0;right:0;top:0;padding:14px 16px 28px;color:#fff;font:500 16px/1.3 Roboto,Arial,sans-serif;text-align:left;
background:linear-gradient(rgba(0,0,0,.6),transparent);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ytf:focus-visible{outline:2px solid #fff;outline-offset:-4px}</style>
<script>document.addEventListener("click",function(e){var b=e.target.closest(".ytf");if(!b)return;var f=document.createElement("iframe");
f.src="https://www.youtube-nocookie.com/embed/"+b.dataset.yt+"?autoplay=1&rel=0";f.className="ytf-frame";f.title=b.getAttribute("aria-label");
f.allow="autoplay; encrypted-media; picture-in-picture; fullscreen";f.allowFullscreen=true;b.replaceWith(f);f.focus()})</script>
"""


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def youtube_meta(vid):
    """Title and a local JPG thumbnail for a video, cached across builds.
    Returns (title, None) when no thumbnail can be fetched."""
    os.makedirs(CACHE, exist_ok=True)
    meta_path = os.path.join(CACHE, vid + ".json")
    if not os.path.exists(meta_path):
        try:
            meta = json.loads(fetch(f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"))
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump({"title": meta["title"]}, f, ensure_ascii=False)
        except Exception as e:  # private, removed or embedding disabled: no title, try the thumbnail anyway
            print(f"warning: no oEmbed data for video {vid} ({e})")
    title = json.load(open(meta_path, encoding="utf-8"))["title"] if os.path.exists(meta_path) else ""
    jpg = os.path.join(CACHE, vid + ".jpg")
    if not os.path.exists(jpg):
        for size in ("maxresdefault", "sddefault", "hqdefault"):
            try:
                data = fetch(f"https://i.ytimg.com/vi/{vid}/{size}.jpg")
            except Exception:
                continue
            with open(jpg + ".part", "wb") as f:
                f.write(data)
            os.replace(jpg + ".part", jpg)
            break
    return title, (jpg if os.path.exists(jpg) else None)


def poster(site, vid, jpg):
    rel = f"{POSTERS}/{vid}.webp"
    out = os.path.join(site, rel)
    if not os.path.exists(out):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        subprocess.run(["cwebp", "-quiet", "-q", "78", "-resize", "1280", "0", "-metadata", "none", jpg, "-o", out + ".part"],
                       check=True)
        os.replace(out + ".part", out)
    return "/" + rel


def facade(site, vid, style):
    """Click-to-play markup, or None (embed left as it was) when no thumbnail exists."""
    title, jpg = youtube_meta(vid)
    if jpg is None:
        print(f"warning: no thumbnail for video {vid}; its embed is left unchanged")
        return None
    src = poster(site, vid, jpg)
    label = htmllib.escape(f"Play video: {title}" if title else "Play video", quote=True)
    overlay = (f'<span class="ytf__title">{htmllib.escape(title)}</span>{YT_PLAY}' if style == "yt" and title
               else YT_PLAY if style == "yt" else VJS_PLAY)
    return (f'<button type="button" class="ytf ytf--{style}" data-yt="{vid}" aria-label="{label}">'
            f'<img src="{src}" alt="" width="1280" height="720" loading="lazy" decoding="async">{overlay}</button>')


_no_webp = None


def no_webp():
    global _no_webp
    if _no_webp is None:
        _no_webp = set(open(NO_WEBP, encoding="utf-8").read().split("\n")) if os.path.exists(NO_WEBP) else set()
    return _no_webp


def remember_no_webp(path):
    no_webp().add(path)
    os.makedirs(os.path.dirname(NO_WEBP), exist_ok=True)
    with open(NO_WEBP, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(p for p in no_webp() if p)) + "\n")


def webp_for(site, ref):
    """Path of a usable WebP sibling for an uploaded image ref, or None."""
    path = unquote(ref.split(DOMAIN, 1)[-1]).lstrip("/")
    src = os.path.join(site, path)
    out = src + ".webp"
    if os.path.exists(out) and os.path.getsize(out) == 0:
        os.remove(out)  # empty marker from an older version of this script
        remember_no_webp(path)
    if path in no_webp():
        return None
    if not os.path.exists(out):
        if not os.path.exists(src):
            return None
        encode(src, out)
        if os.path.getsize(out) > 0.9 * os.path.getsize(src):
            os.remove(out)  # not worth it; remember so the next build doesn't retry
            remember_no_webp(path)
            return None
    return ref + ".webp"


def encode(src, out):
    """JPEGs lossy. PNGs both ways: lossless keeps logos and line art exact and
    wins unless the PNG is really a photo (e.g. a screenshot of one)."""
    # Write to .part files and rename at the end: an interrupted run must never
    # leave a half-written .webp that later runs would trust.
    base = ["cwebp", "-quiet", "-mt", "-metadata", "none"]
    lossy = out + ".part"
    subprocess.run([*base, "-q", "82", "-alpha_q", "100", src, "-o", lossy], check=True)
    if src.lower().endswith(".png"):
        lossless = out + ".lossless.part"
        subprocess.run([*base, "-lossless", "-z", "9", src, "-o", lossless], check=True)
        if os.path.getsize(lossless) <= 1.3 * os.path.getsize(lossy):
            os.replace(lossless, lossy)
        else:
            os.remove(lossless)
    os.replace(lossy, out)


def rewrite_images(site, text):
    saved = []

    def stash(m):
        saved.append(m.group(0))
        return f"\x00{len(saved) - 1}\x00"

    text = PROTECT.sub(stash, text)
    text = IMG_RE.sub(lambda m: webp_for(site, m.group(1)) or m.group(1), text)
    return re.sub(r"\x00(\d+)\x00", lambda m: saved[int(m.group(1))], text)


def process_html(site, path):
    html = open(path, encoding="utf-8").read()
    has_video = bool(IFRAME_RE.search(html) or VIDEOJS_RE.search(html))
    html = IFRAME_RE.sub(lambda m: facade(site, m.group(1), "yt") or m.group(0), html)
    html = VIDEOJS_RE.sub(lambda m: facade(site, m.group(1), "vjs") or m.group(0), html)
    has_video = has_video and "ytf ytf--" in html
    if has_video:
        # The theme loads YouTube's iframe API for any .video-youtube wrapper.
        html = html.replace('class="image-placeholder video video-youtube"', 'class="image-placeholder video"')
        html = VIDEO_SCRIPTS.sub("", html)
        html = html.replace("</head>", FACADE_HEAD + "</head>", 1)
    html = DROP_PRELOADS.sub("", html)
    html = re.sub(r'class="fa (flaticon-[\w-]+)"', r'class="\1"', html)
    html = rewrite_images(site, html)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def main(site):
    for root, _, files in os.walk(site):
        for name in files:
            path = os.path.join(root, name)
            # Generated pages only; root extras like naver*.html stay byte for byte.
            if name in ("index.html", "404.html") and not os.path.relpath(path, site).split(os.sep)[0].startswith("wp-"):
                process_html(site, path)
            elif name.endswith(".css") and "siteground-optimizer-assets" in path:
                css = open(path, encoding="utf-8").read().replace(f"https://{DOMAIN}/", "/")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(rewrite_images(site, css))
    left = [n for r, _, fs in os.walk(site) for n in fs
            if n.endswith(".html") and IFRAME_RE.search(open(os.path.join(r, n), encoding="utf-8").read())]
    print("pages still embedding YouTube directly:", left or "none")


if __name__ == "__main__":
    main(sys.argv[1])
