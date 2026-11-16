#!/usr/bin/env python3
"""Local preview server for the static site: threaded, HTTP/1.1, with Range
support so background videos play (Safari refuses video without it).

Usage: python3 -I serve.py <site_dir> [port]
"""
import functools
import gzip
import http.server
import io
import os
import re
import sys


GZIP_TYPES = {"text/html", "text/css", "text/javascript", "application/javascript",
              "application/json", "image/svg+xml", "text/plain", "application/xml", "text/xml"}


class Handler(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css",
        ".svg": "image/svg+xml", ".webp": "image/webp", ".avif": "image/avif",
        ".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf",
        ".mp4": "video/mp4", ".webm": "video/webm", ".json": "application/json",
        ".html": "text/html; charset=utf-8",
    }

    def send_head(self):
        self._remaining = None  # never carry a byte count over to the next request
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        if os.path.isdir(path) and os.path.isfile(os.path.join(path, "index.html")) and self.path.split("?")[0].endswith("/"):
            path = os.path.join(path, "index.html")
        ctype = self.guess_type(path)
        if (not rng and os.path.isfile(path) and "gzip" in self.headers.get("Accept-Encoding", "")
                and ctype.split(";")[0] in GZIP_TYPES):
            # Like SiteGround: compress text responses so measured weights are realistic.
            with open(path, "rb") as fh:
                body = gzip.compress(fh.read(), 6)
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return io.BytesIO(body)
        if not rng or os.path.isdir(path) or not os.path.isfile(path):
            return super().send_head()
        m = re.match(r"bytes=(\d*)-(\d*)$", rng.strip())
        size = os.path.getsize(path)
        if not m or (m.group(1) == "" and m.group(2) == ""):
            return super().send_head()
        if m.group(1) == "":
            start, end = max(0, size - int(m.group(2))), size - 1
        else:
            start = int(m.group(1))
            end = min(int(m.group(2)), size - 1) if m.group(2) else size - 1
        if start >= size or start > end:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return None
        f = open(path, "rb")
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        self._remaining = end - start + 1
        return f

    def copyfile(self, source, outputfile):
        remaining = getattr(self, "_remaining", None)
        if remaining is None:
            return super().copyfile(source, outputfile)
        self._remaining = None
        while remaining > 0:
            chunk = source.read(min(65536, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)

    def end_headers(self):
        if not self.headers.get("Range"):
            self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def log_message(self, fmt, *args):
        if args and str(args[1]).startswith(("4", "5")):
            sys.stderr.write(f"{args[1]} {args[0]}\n")


def main():
    site = os.path.abspath(sys.argv[1])
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
    handler = functools.partial(Handler, directory=site)
    http.server.ThreadingHTTPServer.daemon_threads = True
    http.server.ThreadingHTTPServer.request_queue_size = 256  # default 5 resets parallel loads
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as srv:
        print(f"Serving {site} on http://127.0.0.1:{port}", flush=True)
        srv.serve_forever()


if __name__ == "__main__":
    main()
