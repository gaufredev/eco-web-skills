#!/bin/bash
# Crawl HTML pages of example.com (assets are pulled from the server separately).
cd "$(dirname "$0")"
rm -rf raw && mkdir -p raw
REMOVED='old-project-1|old-project-2'
printf '%s\n' https://example.com/ https://example.com/about/ https://example.com/services/ \
  https://example.com/work/ https://example.com/clients/ https://example.com/contact/ \
  https://example.com/blog/ https://example.com/online-marketing/ > urls-seed.txt
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
wget --recursive --level=inf --no-host-directories --directory-prefix=raw \
  --adjust-extension --restrict-file-names=nocontrol \
  --domains=example.com -e robots=off -U "$UA" --header="Accept: text/html" \
  --exclude-directories=/wp-content,/wp-includes,/wp-admin,/wp-json \
  --reject-regex="\?|/feed/?$|/feed/|xmlrpc|wp-login|/comments/|/embed/?$|/trackback/?$|/($REMOVED)/" \
  --reject='jpg,jpeg,png,gif,webp,svg,ico,pdf,mp4,webm,mov,zip,css,js,woff,woff2,ttf,eot,otf,xml,txt,json' \
  --wait=0.1 --tries=3 --timeout=30 --no-verbose \
  --input-file=urls-seed.txt --output-file=crawl.log --content-on-error
echo "wget exit $?" >> crawl.log
# Same browser headers as the crawl: a bare UA gets the host's bot-filter page instead.
curl -s -A "$UA" -H "Accept: text/html" https://example.com/this-page-does-not-exist-404test/ -o raw/404.html
grep -qi "<footer" raw/404.html || echo "WARNING: raw/404.html has no <footer>; check it is the theme's 404 page, not a bot-filter page" | tee -a crawl.log
echo DONE >> crawl.log
