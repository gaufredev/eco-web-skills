---
name: eco-web
description: Build sustainable, eco-friendly websites optimized for low carbon emissions, minimal resource usage, and high scores on EcoGrader/EcoIndex. Use when the user wants to build a green website, optimize a site for sustainability, reduce page weight/carbon footprint, score well on eco-grading tools, or apply web sustainability best practices. Triggers on 'eco website', 'green website', 'sustainable web', 'carbon footprint', 'EcoGrader', 'EcoIndex', 'web sustainability', 'low-carbon site', or when environmental impact of a website is discussed.
---

# Eco-Friendly Web Design & Development

This skill provides comprehensive guidance for building websites that minimize environmental impact while maintaining excellent user experience. It synthesizes best practices from EcoGrader, EcoIndex, the Sustainable Web Design Model (SWDMv4), W3C Web Sustainability Guidelines, and leading practitioners.

## How Eco-Scoring Tools Work

### EcoGrader (ecograder.com)
Scores websites on three pillars:
1. **Performance** (heavily weighted) — page load speed, data transfer, script efficiency
2. **User Experience** — accessibility, layout stability, redirects, responsiveness
3. **Green Hosting** — binary 0 or 100, checked against the Green Web Foundation database

### EcoIndex (ecoindex.fr)
Measures three technical metrics per page:
- **DOM complexity** — number of DOM elements
- **HTTP requests** — number of network requests
- **Page weight** — total transferred bytes
Grades from A (best) to G (worst). Lower values on all three = better grade.

### Carbon Calculation — Sustainable Web Design Model v4
The SWDMv4 formula estimates gCO2e per page view across three system segments:

| Segment | Energy share | Operational kWh/GB | Embodied kWh/GB |
|---------|-------------|-------------------|-----------------|
| Data centers | 22% | 0.055 | 0.012 |
| Networks | 24% | 0.059 | 0.013 |
| User devices | 54% | 0.080 | 0.081 |

- Global grid carbon intensity: **494 gCO2e/kWh** (Ember 2022)
- Green hosting can mitigate **~14%** of estimated emissions
- Returning visitors with cached assets transfer less data

- Energy per GB in SWDMv4: about **0.3 kWh** across the whole chain (the table above summed, operational + embodied). Older articles quote ~0.5 kWh/GB or more; don't mix the two.

**Case study, with its caveat** (Danny van Kooten): removing a 20 KB JavaScript dependency from the Mailchimp for WordPress plugin, installed on about 2 million sites, was estimated by the author at ~59,000 kg CO2/month. That is his own back-of-envelope estimate; use it to show how a tiny change multiplies across many sites, not as a measured saving.

**Website bloat trend**: the median home page is about 2.9 MB on desktop (HTTP Archive Web Almanac 2025, +8% in a year); the median WordPress home page was about 3.0 MB (Web Almanac 2024).

### What lighter websites don't do — say this honestly

Checked against sources in 2026 (see "Honest limits" below for the details). Claims that go too far undermine the whole message, so a page or footer built with this skill should not make them:
- The grams per visit are **model estimates**. The SWD authors say the model probably overestimates; network studies (Mytton et al. 2024, Journal of Industrial Ecology) show networks use most of their energy whether or not one more megabyte goes through. Use grams to **compare pages**, not as exact savings.
- "Static uses 60× less server energy" is only half true: in a UCLouvain thesis (Jungers 2025) WordPress *with a good page cache* used about as little energy as the static site. The real difference is in requests a cache can't answer (bots trying the login page, admin, cron) — and in security and maintenance.
- Deleting files doesn't close data centres: storage is ~5% of data-centre electricity (IEA). Clean up for security and simplicity, not for a big energy claim.
- "Static" ≠ light: static sites built with heavy JS frameworks (Next.js, Nuxt) are about as heavy as WordPress in the median (Web Almanac 2024).
- If an AI assistant did the work, disclose its energy too (an AI site conversion was estimated at ~1.4 kWh; six months of AI work adding pages and features to a seven-language site ~18 kWh, mostly long sessions re-reading their own context — keep sessions short and use ready-made skills; estimates from token counts, half to double either way). Show build vs running: building is once, running comes back every year — at 10,000 visits/month a 3 MB page costs ~106 kWh/yr in visits alone (SWD), a 0.3 MB page ~11.

### Speed = Sustainability + Good Business

Eco choices aren't just environmental — they're good business: BBC lost **10% of users** per extra second of load time. Pinterest: 40% faster → **15% more signups**. eBay: every **100ms** improvement affects conversion. 50% of users would abandon animations/video for faster loading.

---

## The Eco-Web Checklist — Sorted by Effort

Organized from "do it in 5 minutes" to "requires architectural decisions." Pick the level that fits your project. Even just the quick wins make a real difference.

**Page weight targets**: < 500 KB is good. < 200 KB is excellent. < 14 KB is the holy grail (fits in one TCP round-trip — see Level 2).

---

### LEVEL 1: Quick Wins (minutes, no design changes)

These require zero design decisions. Just do them.

**Add an eco-friendly footnote** — this costs nothing and spreads awareness. A footnote on someone else's website is what got the author of this skill interested in eco-web in the first place. One site saves very little on its own; the point is visibility — when many sites do even a little of this and say so, it changes what people expect from a website. It's the most powerful thing per effort spent. See the "Eco-Friendly Statement" section below for the full template.

**Images — strip the invisible bloat**:
- **Strip EXIF/metadata** from all photos (camera settings, GPS, thumbnails) — `exiftool -all=`, Sharp's `withMetadata(false)`, Squoosh. Saves 10-50 KB per image for zero visual change
- Compress existing images more aggressively (TinyPNG, Squoosh) — often 30-60% smaller with no visible difference
- Add `loading="lazy"` to all below-fold images (one HTML attribute)
- Add `fetchpriority="high"` on the hero/LCP image (one HTML attribute). **Important**: do NOT combine with `decoding="async"` on the LCP image — async decoding delays paint and conflicts with fetchpriority, hurting LCP score. Use `decoding="async"` only on non-LCP images
- **Preload the LCP image**: `<link rel="preload" as="image" href="hero.avif" type="image/avif">` in `<head>` — tells the browser to fetch it immediately before parsing the full DOM
- Run SVGs through **SVGO** to strip editor metadata bloat

**Fonts — trim the fat (keep the design)**:
- Audit loaded font weights vs CSS — remove weights not used in any `font-weight` declaration (dead weight downloads)
- Check for loaded font families never referenced in any `font-family` rule
- Add `font-display: swap` (or better: `optional` — see Level 2) to prevent invisible text during load
- Switch from TTF/OTF to **WOFF2** (up to 97% smaller)
- **Check which `@font-face` is actually applied**, not just which files load. On one WordPress site a speed plugin preloaded 28 Google font files no rule used and inlined `@font-face` rules pointing at full TTFs: ~490 KB of fonts per page that no text on the page used

**Korean (CJK) fonts — the biggest single item on Korean sites**:
- Hangul fonts are huge: Pretendard 1.3.9 Regular is **748 KB** per weight as a full woff2, the variable version **~2.0 MB** — more than a whole light website. Two weights = 1.5 MB before any text shows
- Lightest: system fonts (`-apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif`) — 0 KB, and they look native on each device
- If the brand font is required: use a **dynamic subset** (Pretendard ships one: 92 `unicode-range` pieces per weight; the browser downloads only the pieces a page needs) and load only the weights actually used

**Caching & compression**:
- Set `Cache-Control: public, max-age=31536000, immutable` for static assets with hashed filenames. **Don't forget AVIF**: `.htaccess` cache rules often list `jpg|jpeg|webp|png` but miss `avif` — add `image/avif` to both `ExpiresByType` and `FilesMatch` rules
- Enable **Brotli** compression on the server (7-13% better than gzip on JS/CSS)
- Use ETags for dynamic content

**Content hygiene**:
- **Tighten `robots.txt`** — about half of all web traffic is automated (Imperva's yearly Bad Bot Report puts bots near 50% of requests). Block aggressive crawlers you don't need. Decide AI crawlers on purpose: blocking them saves requests, allowing them lets AI search tools quote and link the site — some sites allow them only on chosen pages
- **Lightweight 404 pages** — keep error pages minimal; they still transfer data
- Compress and optimize PDFs and downloadable files

**Declare your hosting**:
- Add a **`carbon.txt`** file to your domain root — machine-readable sustainability declaration (GWF standard)
- Check if your host is already green: Green Web Foundation's **Green Web Check** (free)

---

### LEVEL 2: Easy Optimizations (hours, minimal design impact)

Small code changes or build step additions. Shouldn't affect the look of the site.

**The 14 KB Rule** (TCP Slow Start):
- On a new connection, the server sends only ~10 TCP packets before waiting for acknowledgment
- 10 packets × 1,460 usable bytes = **~14 KB** in the first round-trip
- If your critical HTML + inline CSS fits in 14 KB, the page renders after **one single round-trip**
- Exceeding 14 KB adds a full extra round-trip (~300-1000ms on mobile, ~612ms on satellite)
- Inline critical CSS, defer the rest — this alone can hit the 14 KB window

**Images — format & delivery upgrades**:
- **AVIF-first pipeline**: Always use a 3-tier `<picture>` stack: AVIF → WebP → JPEG. AVIF is 30-50% smaller than WebP, ~95% browser support (Chrome, Firefox, Safari 16.4+). WebP covers remaining edge cases. Example:
  ```html
  <picture>
    <source srcset="image.avif" type="image/avif">
    <source srcset="image.webp" type="image/webp">
    <img src="image.jpg" alt="..." width="800" height="600" loading="lazy" decoding="async">
  </picture>
  ```
- **Conversion tools**: `avifenc` (from `brew install libavif`) for AVIF, `cwebp` (from `brew install webp`) for WebP. Resize first with `sips --resampleWidth 800`, then convert. Quality flags: `avifenc --min 20 --max 35 --speed 6` and `cwebp -q 80`
- **Real-world results**: The author's own site (julianquintart.com) went from **16.6 MB → 249 KB** (98.5% reduction) by resizing images to display dimensions and converting to AVIF/WebP. Profile images (800px wide): 19-32 KB AVIF. Activity photos (600px wide): 22-53 KB AVIF
- Serve at exact display dimensions — never rely on CSS to downscale. A 4032×3024 photo displayed at 600px is wasting 97% of its pixels
- **Avoid GIFs entirely** — use short `<video>` loops (MP4/WebM, 80-90% smaller) or CSS animations
- **Favicons**: Convert simple favicon PNGs to inline SVG data URIs (`<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,...">`) — eliminates an HTTP request and reduces ~17KB PNG to <1KB inline SVG

**Fonts — smarter loading**:
- Subset fonts to only needed character ranges (`unicode-range`)
- Consider **Variable Fonts** — one file replaces multiple weight files
- When auditing Google Fonts, check if similar-looking system fonts exist — many have near-identical system equivalents (e.g., Instrument Sans ≈ San Francisco via `system-ui`, JetBrains Mono ≈ SF Mono via `ui-monospace`). Suggest the swap when the visual difference is negligible
- If custom fonts are needed: max 2 weights, 1 family (or 1 variable font file)
- **Self-host fonts** — cross-site browser cache partitioning (since 2020) means Google Fonts CDN is now strictly slower than self-hosting. The "shared cache" benefit is dead. Download the files, host them yourself
- Upgrade from `font-display: swap` to **`font-display: optional`** — renders immediately with fallback, only uses custom font if already in cache. Best for LCP, prevents CLS entirely
- `preload` critical font files: `<link rel="preload" href="/fonts/Main.woff2" as="font" type="font/woff2" crossorigin>`
- Use **`size-adjust`** CSS descriptor to match fallback font metrics to custom font — prevents layout shift during swap: `@font-face { font-family: "MyFont-fallback"; size-adjust: 105%; src: local("Arial"); }`
- **Never use icon fonts** — accessibility problems (screen readers read them as text), and the entire font file loads even if you use only 3 icons. Always use inline SVGs for icons instead

**Code — build-step wins**:
- Minify all CSS and JS in production
- Tree-shake unused code (dead code elimination)
- Code-split: load only what the current page needs
- Remove unused CSS (PurgeCSS, UnCSS)

**HTTP requests — trim the obvious**:
- Use inline SVGs instead of multiple icon files
- Self-host critical third-party assets when possible

**Resource hints** (tell the browser what's coming):
- `preconnect` = full connection (DNS + TCP + TLS). Use for origins on the critical path, needed within first 5 seconds. Saves hundreds of ms. But: each unused preconnect wastes ~3KB (cert overhead), and Chrome closes unused ones after 10 seconds — don't overdo it
- `dns-prefetch` = DNS lookup only. Lighter than preconnect, use for non-critical external origins: `<link rel="dns-prefetch" href="https://cdn.example.com">`
- `preload` = fetch a specific resource early without executing it. Use for fonts, critical images, or resources discovered late in parsing: `<link rel="preload" href="/fonts/Main.woff2" as="font" type="font/woff2" crossorigin>`
- Common mistake: adding `crossorigin` to everything. Only use it when the request uses CORS mode. Wrong `crossorigin` = browser opens a duplicate connection, wasting the preconnect entirely
- Best practice: reduce third-party origins first, then preconnect the remaining essential ones

**Embed facades** (huge win if you have embeds):
- YouTube embed loads ~1-3 MB; a static thumbnail facade is ~10-30 KB
- Same for Google Maps, social media widgets — show placeholder, load on click
- **Self-host YouTube thumbnails**: YouTube CDN (`i.ytimg.com/vi/.../maxresdefault.jpg`) serves 1280×720 JPEGs with only 2-hour cache TTL. Download, resize to display dimensions (~640px), convert to AVIF/WebP, and self-host. Result: 391 KiB → 57 KiB (AVIF) + you control cache headers (1 year). Lighthouse flags YouTube CDN thumbnails for both "image delivery" and "cache lifetimes"

**Use native HTML instead of JS components**:
- `<details>/<summary>` for accordions/toggles
- `<dialog>` for modals
- `<datalist>` for autocomplete inputs
- `<meter>` and `<progress>` for indicators
- CSS `:target` for tab panels and anchored navigation
- Replace JS animations with CSS (`transition`, `animation`, `@keyframes`)

**Warning: animations cost more than bytes suggest.** Hey Low tested with GreenFrame: same data transfer, **52% power difference** (129 mWh vs 25 mWh CPU). EcoGrader showed both versions as similar because it measures data transfer. Data transfer is a useful proxy but misses CPU-intensive effects. For the full picture, measure with **GreenFrame** (greenframe.io) which tracks actual CPU and energy consumption.

**Dark mode — the science** (easy to add, real savings on OLED):

Energy savings on OLED are **proportional to pixel brightness — it's a gradient, not binary**:
- **Pure black (#000)** = pixel completely OFF = maximum savings
- **Dark gray (#1a1a1a)** = pixel very dim = still significant savings
- **Any darker shade saves energy** — the darker, the better
- **LCD screens**: zero benefit regardless of shade (backlight always on)

Real numbers (Mobile Enerlytics research):
- At full brightness: **5.6% to 44.7%** battery savings depending on activity
- At 38% brightness: **1.8% to 23.5%** savings
- Example: reading The Verge in dark mode at 38% brightness = **23.5% saved**
- Scale impact: 1M iPhones on dark mode for a year ≈ **144,000 kg CO2** prevented (≈ 31 cars) — *unverified secondary figure; check the source before quoting it publicly*
- **Blue pixels** use ~25% more energy than red/green at any brightness — prefer warmer palettes — *unverified secondary figure; check before quoting*
- Keep it in proportion: the phone's screen energy per page is tiny next to making the phone. Offer dark mode for comfort and battery, not as a climate claim

**No-JS dark mode toggle** (zero extra bytes):
Uses the checkbox hack — `:checked` pseudo-selector + general sibling combinator (`~`):
```html
<body>
  <input id="color-mode" type="checkbox" name="color-mode">
  <label for="color-mode">Toggle dark mode</label>
  <div class="color-scheme-wrapper">
    <!-- site content -->
  </div>
</body>
```
```css
:root { --bg: white; --text: black; }
@media (prefers-color-scheme: dark) {
  :root { --bg: black; --text: white; }
}
#color-mode:checked ~ .color-scheme-wrapper { --bg: black; --text: white; }
@media (prefers-color-scheme: dark) {
  #color-mode:checked ~ .color-scheme-wrapper { --bg: white; --text: black; }
}
.color-scheme-wrapper { min-height: 100vh; background: var(--bg); color: var(--text); }
```
Respects OS preference by default, checkbox toggles override. No JavaScript needed. (Source: endtimes.dev)

**Zero-weight visual effects** — use CSS & SVG tricks instead of heavy assets. See the dedicated "Zero-Weight Visual Effects" section below for full code examples (SVG displacement filters for hand-printed text, text-shadow halos, box-decoration-break, wavy underlines, clip-path, blend modes, CSS gradients, backdrop-filter). Key insight: system font + SVG filter = unique visual identity at ~0.5 KB instead of 50-200 KB for a custom display font.

---

### LEVEL 3: Moderate Effort (design-aware decisions)

These may require design discussion or stakeholder buy-in.

**Fonts — the hard conversation**:
- Prefer **system font stacks** — zero download cost, but requires design agreement
  - Sans: `system-ui, -apple-system, BlinkMacSystemFont, sans-serif` (SF on Mac, Segoe UI on Windows, Roboto on Android)
  - Mono: `ui-monospace, 'SF Mono', Menlo, monospace` (SF Mono on Mac, Cascadia/Consolas on Windows)
- Dropping Google Fonts entirely saves ~100-300 KB per page but changes the visual identity
- **But**: pair with zero-weight CSS/SVG visual effects (Level 2) to keep a distinctive look even with system fonts — this makes the system fonts conversation much easier

**Images — question necessity**:
- Ask: does each image add real value? Replace decorative images with CSS gradients, SVGs, or nothing
- SVG for icons and illustrations instead of PNG/JPG
- Consider whether video is truly necessary, or would an image suffice

**Video strategy**:
- Never autoplay
- Use facade/thumbnail + click-to-load pattern
- Keep videos short, compress heavily
- Host on optimized platforms (adaptive bitrate)

**Reduce third-party scripts**:
- Eliminate unnecessary analytics, trackers, ads, social widgets
- Each third-party script = extra DNS lookup + connection + download + execution
- Remove tracking/advertising scripts that add weight without user value

**UX & design for sustainability**:
- **Streamline user journeys** — fewer pages visited = less data transferred
- **Clear navigation** and site search — help users find content fast
- **Avoid layout shifts** (CLS) — layout recalculations waste CPU
- **No dark patterns** — deceptive UI leads to wasted page views
- **Accessible design** (WCAG) — users with assistive tech shouldn't need extra page loads
- **Avoid infinite scroll** — pagination is more intentional and lighter
- **Minimize redirects** — each redirect = extra round trip

**DOM complexity**:
- Flatten nested `<div>` structures — use semantic HTML (`<main>`, `<section>`, `<article>`)
- Target: < 1,500 DOM elements per page

**Content strategy**:
- Write **concise, clear copy** — less content to render, faster comprehension
- Audit and remove outdated/unused pages — less to crawl, host, and serve
- Use **pagination** over loading all content at once
- **SEO optimization** — findability reduces wasted browsing energy
- **Set a carbon budget** — target < 0.5g CO2 per page view, < 0.2g for lightweight ones. Measure with websitecarbon.com

---

### LEVEL 4: Architectural Choices (project setup / migration)

These are best decided at project start. Retrofitting is harder but possible.

**Green hosting**:
- Choose a host verified by the [Green Web Foundation](https://www.thegreenwebfoundation.org/)
- Green hosting = 100 points on EcoGrader's hosting score (binary: green or not)
- Browse verified providers: Green Web Directory at `app.greenweb.org/directory/`
- Check from the command line: `curl -s https://api.thegreenwebfoundation.org/api/v3/greencheck/<domain>` → `"green": true/false` and the provider
- Look for low **PUE** (Power Usage Effectiveness) — 1.1-1.2 is excellent (industry avg ~1.67)
- Recommended providers (Europe): **Infomaniak** (Swiss, PUE < 1.1, server heat fed into district heating in Geneva), **Hetzner** (Germany, hydropower), **1984hosting** (Iceland, geothermal/hydro power, cold climate reduces cooling)
- **Greenwashing warning**: "listed as green" usually means the company buys renewable power or certificates to *match* its yearly use (Google, Amazon), not that your server runs on sun or wind. It supports grid growth but say it that way. "The most eco-friendly energy is the one that's never used" — reduce data first, then pick green hosting
- **Korea**: a host that really runs on renewable power is hard to find. The grid is still mostly coal, gas and nuclear, and Korean data-centre operators (Kakao, Samsung SDS) told a 2025 NGO survey that renewable power is hard to procure in Korea. Naver is going furthest so far: first Korean internet company in RE100 (2022; 60% by 2030, 100% by 2040), three PPAs for solar and small hydro, and in April 2026 agreed to become the first Korean RE100 member to invest directly in a power plant (buying 30% of a wind farm under construction in Yeongyang, 25-year contract, ~180 GWh/yr for its data centres from 2028; still being completed in August 2026). For 2024 its renewable share was 6.8% (RE100 achievement rate 5.3%); 2025 figures not found. Kakao joined RE100 in 2023 with the same targets. Re-check these before quoting — they move every year

**Server location — know your audience first**:
- Put the site **near most of its visitors**. Measured example: a Korean company site on a Singapore server (SiteGround / Google Cloud asia-southeast1) took ~1.2 s for the home page HTML from Seoul (~216 ms per round trip); a test copy on a CDN edge in Seoul took ~0.04 s
- Energy: a longer path crosses more network equipment, but the bigger factor is usually the electricity mix where the server runs. Speed is the clearer win
- **Global audience → a CDN** (copies on servers in many countries): faster, shorter paths, less work for the origin server. **Mostly-Korean audience → a host or CDN edge in Korea** does the same more simply
- Test any CDN from the audience's real networks first: some global CDNs serve Korean ISPs from abroad (2026 user reports of KT traffic routed via the US on Cloudflare). Amazon CloudFront and Naver Cloud's Global Edge served from Seoul in tests

**Static-first architecture**:
- Static Site Generators (Astro, Hugo, Eleventy, Next.js static export) eliminate server processing per request
- Pre-render everything possible at build time
- Use ISR (Incremental Static Regeneration) for semi-dynamic content
- Consider static hosting (Netlify, Vercel, Cloudflare Pages) — no server processing per request
- **Kirby CMS** — PHP flat-file CMS, no database. Content stored as text files (timeless format). €99 one-time license. Fast out of the box, matches static speed with caching. Headless capable

**Progressive Web App (PWA)**:
- Cache assets on device → dramatically reduces repeat data transfers
- Offline-first patterns reduce unnecessary network requests

**Server-side rendering** over client-side when dynamic content is needed:
- SSR sends ready HTML → less JS processing on user device
- Less CPU on user devices = less energy consumed

**Framework choice** (if you need one):
- Prefer lightweight options: Astro (partial hydration = minimal JS), Svelte, Preact
- Use vanilla JS over heavy frameworks for simple sites
- Defer non-critical JS (`defer`, `async`, dynamic `import()`)
- Audit bundle size regularly (`bundlephobia`, `webpack-bundle-analyzer`)

**CDN**:
- Use a CDN to serve from geographically close edge nodes when the audience is spread out (see "Server location" above — test it from the audience's networks)
- Implement **service workers** for cache-first strategies

**WordPress → static**: most small business and organisation sites change a few times a year and don't need a database. Converting them keeps the design, removes plugins, logins and updates, and usually cuts weight 60–70% because the conversion is also the moment to fix fonts, images, video embeds and trackers. Measured: a creative agency site 2,219 → 727 KB per page (server folder 3.1 GB → 134 MB); a company site 1,324 → 517 KB; a lean WordPress site 669 → 195 KB on its home page. Keep a CMS for shops, member accounts, bookings or daily publishing — then page cache + few plugins + automatic updates. In Korea many small sites are on hosted builders (Cafe24, imweb) that can't be converted the same way, or on Gnuboard (PHP, same plugin risks as WordPress). See the companion skill `wp-to-static`.

---

## Quick Reference: Eco-Score Optimization Targets

| Metric | Poor | Acceptable | Good | Excellent |
|--------|------|-----------|------|-----------|
| Page weight | > 2 MB | < 1 MB | < 500 KB | < 200 KB |
| HTTP requests | > 80 | < 50 | < 25 | < 15 |
| DOM elements | > 3000 | < 1500 | < 800 | < 500 |
| Largest Contentful Paint | > 4s | < 2.5s | < 1.5s | < 1s |
| CO2 per page view | > 1g | < 0.5g | < 0.2g | < 0.1g |
| EcoIndex grade | F-G | D-E | B-C | A |

## Tech Stack Recommendations for Green Sites

**Best choices for minimal footprint:**
- **SSG**: Astro (partial hydration = minimal JS), Hugo (Go-based, blazing fast builds), Eleventy
- **CSS**: Vanilla CSS with custom properties, or Tailwind (purges unused styles)
- **Hosting**: Cloudflare Pages, Netlify, Vercel (edge, green-certified options available) for global audiences; for a Korean audience test that they actually serve from Korea, or use Amazon CloudFront / Naver Cloud Global Edge with a Seoul edge; for a European audience Infomaniak or Hetzner
- **Images**: Sharp (Node.js), Squoosh CLI for build-time optimization
- **Carbon estimation**: **CO2.js** (Green Web Foundation's open-source JS library, uses SWDMv4 + grid intensity data from Electricity Maps)
- **Monitoring**: Ecograder, EcoIndex, Lighthouse, WebPageTest, websitecarbon.com, LeafScore, Green Web Check, **GreenFrame** (measures actual CPU/energy, not just bytes)

## When Building with This Skill

1. Start with semantic HTML — get the content structure right before adding anything else
2. Style with minimal CSS — system fonts, CSS custom properties, no framework overhead unless justified
3. Add JS only when HTML/CSS genuinely cannot accomplish the interaction
4. Optimize all assets at build time, not runtime
5. Test with Lighthouse Performance score (target 90+) and EcoGrader
6. Every byte matters — question every dependency, every image, every script

## Eco-Friendly Statement — Always Include (Level 1 Quick Win!)

This is the single highest-impact-per-effort action in this entire skill. A simple footnote about eco-friendly web choices on someone else's site is what sparked the author's interest in sustainable web development in the first place. It costs nothing to add, and it plants a seed — the person who reads it might go down the same rabbit hole, or ask their own web agency. One website saves very little; many websites doing a little and saying so change what people expect from the web. That's where the bigger effect is.

**Rules learned from real sites:**
- **Only claim what was measured for that page.** A home page's "A+, cleaner than 95%" is the home page's result; rate every other page on its own. Re-rate after big content changes.
- Rate from measured bytes, no API key needed: `curl -s "https://api.websitecarbon.com/data?bytes=<compressed transfer bytes>&green=0"` (use `green=1` only if the Green Web Check says green). Python's urllib gets a 403 from this API; curl works.
- **Never embed the Website Carbon badge script** — it loads a third-party script on every page and breaks a "no trackers" claim. Link to the result page instead.
- **No green-hosting claim by default** — hosts change and the line silently becomes false. If it's checked green, say "hosted on servers the Green Web Foundation lists as green", linking to the check, not "powered by renewable energy".
- Measure weight the same way every time: Playwright (Chromium) with the cache disabled, scroll to the bottom so lazy images load, and sum CDP `Network.loadingFinished` `encodedDataLength` (the compressed bytes actually transferred).

When building any website or tool, always add an eco-friendly statement that explains the lightweight choices made. Include it in:
- **A visible footer/footnote on the website itself** — this is the most important placement
- **The app's help/about section** (if it has one)
- **The README** (if it's an open-source project)

The statement should follow this structure:
1. **Title**: "Lighter Code, Faster App, Greener Web" (or adapted to context)
2. **Educational hook**: explain that websites use energy and the web has a real carbon footprint — most people don't know this
3. **Dual benefit**: emphasize that lighter code is both **faster for the user** and **better for the planet**
4. **Specific choices**: list what the app intentionally avoids (e.g., no Google Fonts, no frameworks, no tracking, inline SVG favicon) with a brief explanation of why each matters
5. **Links**: point to [Website Carbon Calculator](https://www.websitecarbon.com) and [Green Web Foundation](https://www.thegreenwebfoundation.org)

Adapt the tone and details to each project — don't copy-paste the same text verbatim, but always cover these points.

### Practical Footnote with Real Numbers

Always end the eco statement with a concrete, relatable footnote. Calculate the actual savings for the project and express them as an everyday equivalent. Follow this process:

1. **Calculate what was removed** — list each removed asset and its approximate size (e.g., Google Fonts ~300 KB, external favicon ~16 KB, framework JS ~150 KB)
2. **Sum the total KB saved per visit**
3. **Multiply by 1,000 visits** to get total data saved
4. **Convert to CO2 using the SWDMv4 model:**
   - Energy per GB: ~0.3 kWh (data centers + networks + devices)
   - CO2 per kWh: ~494 g (global average grid intensity)
   - Formula: `(total_KB_saved × 1000) / 1,048,576 × 0.3 × 494 = grams CO2 saved`
5. **Express as a relatable equivalent:**
   - ~8 g CO2 = 1 smartphone charge
   - ~21 g CO2 = boiling water for 1 cup of tea
   - ~150 g CO2 = 1 km driven by car
   - ~1,000 g CO2 = 1 load of laundry

Example footnote tone: *"This might not seem like a lot — but every byte counts. Just by [specific changes] (~X KB saved per visit), if 1,000 people use this app, we save the equivalent of [relatable comparison]. (Based on the SWDMv4 model)"*

Link to the SWDMv4 methodology: https://sustainablewebdesign.org/estimating-digital-emissions/

## Zero-Weight Visual Effects — CSS & SVG Tricks That Replace Heavy Assets

These techniques achieve rich, distinctive visual aesthetics without loading any external files. They're the secret weapon for making eco-sites look intentional and crafted rather than plain.

**Case study: endtimes.dev** — A site about the 14 KB rule that practices what it preaches. Uses system fonts only (Helvetica Neue stack), zero custom font files, yet looks like hand-printed letterpress. Every effect below is pure CSS/SVG.

### SVG Displacement Filters (hand-printed / distressed text)
Inline SVG filters using `feTurbulence` + `feDisplacementMap` can make plain system fonts look like letterpress, risograph, or hand-drawn text — zero font files needed.

```html
<svg class="hidden" xmlns="http://www.w3.org/2000/svg">
  <filter id="rough-text">
    <!-- Pass 1: large-scale wobble (letterpress misalignment) -->
    <feTurbulence baseFrequency="0.01 0.02" numOctaves="2" result="t0"/>
    <feDisplacementMap in="SourceGraphic" in2="t0" scale="4" result="d0"/>
    <feComposite in="SourceGraphic" in2="d0" operator="atop" result="0"/>
    <!-- Pass 2: fine-grain roughness (ink bleed on paper) -->
    <feTurbulence baseFrequency="1" numOctaves="2" result="t1"/>
    <feDisplacementMap in="0" in2="t1" scale="1" result="d1"/>
    <feComposite in="0" in2="d1" operator="atop" result="1"/>
    <!-- Slight offset for print misregistration feel -->
    <feOffset dx="-3" dy="-3" in="1"/>
  </filter>
</svg>
```
Apply via CSS: `filter: url(#rough-text)`. Use different filter IDs with varying `scale` values for small vs large screens. Cost: ~500 bytes of inline SVG vs ~50-200 KB for a custom display font.

Tuning guide:
- `baseFrequency`: lower = larger warps. `0.01 0.02` gives gentle wobble
- `scale`: controls displacement intensity. `4` for noticeable, `1` for subtle grain
- `numOctaves`: more = more detail in the noise pattern
- `feOffset dx/dy`: simulates print misregistration (negative values = up-left shift)

### Text-Shadow Halo (descender-aware underlines)
An 8-directional 1px text-shadow in the background color creates a "knockout" gap around letters, so custom underlines don't clash with descenders (g, y, p, q):

```css
a {
  text-decoration: none;
  box-shadow: inset 0 -0.3em var(--link-color);  /* the underline */
  text-shadow:
    1px 0 var(--bg), 0 1px var(--bg), 1px 1px var(--bg),
    -1px 0 var(--bg), 0 -1px var(--bg), -1px -1px var(--bg),
    1px -1px var(--bg), -1px 1px var(--bg);
}
```
This replaces `text-decoration-skip-ink` (which can't be styled) with a fully controllable colored underline that weaves behind letter descenders. Zero bytes of external assets.

### Box-Decoration-Break (multi-line highlight boxes)
For title text that wraps across multiple lines with a solid background on each line independently:

```css
h1 > span {
  background: var(--highlight);
  padding: 0.64rem;
  box-decoration-break: clone;
  -webkit-box-decoration-break: clone;
}
```
Each wrapped line gets its own background box. Used on endtimes.dev for the orange title block.

### Wavy Underlines (native CSS)
```css
a { text-decoration: underline wavy var(--accent-color); }
```
One CSS line for a playful, hand-drawn feel. No SVG, no JS, no images.

### SVG Mask-Image for Decorative Elements (zero-request patterns)
Replace decorative images (dividers, borders, patterns) with inline SVG data URIs used as CSS masks. Example — a zigzag `<hr>` divider (practicalbetterments.com):

```css
hr {
  border: 0;
  height: 16px;
  background: var(--link);
  --mask: url("data:image/svg+xml,...zigzag SVG pattern...");
  mask-image: var(--mask);
  -webkit-mask-image: var(--mask);
}
```
URL-encode the SVG pattern directly in CSS — zero HTTP requests, ~300 bytes. Works for zigzags, waves, dots, any repeating pattern.

### CSS-Only Dark Mode Toggle (near-zero JS)
Hidden checkbox + CSS sibling selector swaps all theme variables without a framework (practicalbetterments.com):

```html
<input type="checkbox" id="alt">
<div id="wrapper">...entire page...</div>
```
```css
:root { --base: #0f0e17; --text: #a7a9be; }
#alt:checked ~ * { --base: #FDFEFF; --text: #333; }
@media (prefers-color-scheme: light) {
  :root { --base: #FDFEFF; --text: #333; }
  #alt:checked ~ * { --base: #0f0e17; --text: #a7a9be; }
}
```
Only ~15 lines of JS for `localStorage` persistence. No framework, no theme library.

### Other zero-weight CSS effects worth considering
- `clip-path` for shaped sections and reveals
- `mix-blend-mode` for image/text overlays without Photoshop
- CSS `gradient` backgrounds for decorative elements instead of images
- `backdrop-filter: blur()` for frosted glass effects
- `@keyframes` for animations that would otherwise be GIFs
- CSS `counter()` for styled ordered lists without JS

**Key insight**: The most eco-friendly "custom font" is a system font + an SVG filter. It achieves a unique visual identity at ~0.5 KB instead of 50-200 KB.

## Inspiration — Eco-Friendly Sites That Prove It Works

- **lowww.directory** (https://lowww.directory/) — curated gallery of 21+ low-carbon websites with CO2 stats. Browse for design inspiration
- **heylow.world** (https://heylow.world/) — eco web agency with an excellent footer model (see below)
- **endtimes.dev** — practices what it preaches: 14 KB pages, system fonts, SVG filters for visual identity
- **practicalbetterments.com** — same author, variable fonts (woff2-variations), SVG mask-image `<hr>`, CSS-only dark mode toggle, zero tracking scripts
- **Organic Basics** (https://organicbasics.com/) — proof that a full Shopify e-commerce store can be fast

### Design Lessons from Low-Carbon Sites

These sites prove that lightweight ≠ ugly. Common patterns from sites scoring 90%+ reduction:

**Be Beau** (0.046g, 93% reduction) — warm beige palette (#F6F3EE), large display fonts (3-5rem), generous whitespace, SVG illustrations instead of photos, only 3 font weights (WOFF2), subtle CSS scale transforms on hover. Feels premium and luxurious.

**Vraiment Vraiment** (0.013g, 98% reduction) — no custom fonts at all, text-based navigation, strategic whitespace, minimal DOM. Proves that the lightest sites rely on typography hierarchy and spacing, not imagery.

**Headless Horse** (0.074g, 88% reduction) — WebP images, strong conceptual branding (the name/concept does the heavy lifting), sparse layout, minimal JS. Memorable through concept, not through weight.

**Gaîté Lyrique** (0.173g, 73% reduction) — a cultural venue with events and exhibitions, yet still light. CDN with aggressive image params (`?width=1280&quality=80`), thumbnail-based navigation (progressive disclosure — details load on dedicated pages, not all at once), reading mode toggle.

**Key takeaways**:
1. **Whitespace is free** — generous spacing makes sites feel premium with zero bytes
2. **SVG illustrations > photos** — vector art is tiny and scales perfectly
3. **Progressive disclosure** — show thumbnails/summaries, load full content on dedicated pages
4. **Strong branding/concept** — a memorable name, color, or idea replaces the need for heavy visuals
5. **Warm muted palettes** — beige, cream, sage — feel intentional and sophisticated, not "missing design"
6. **Large typography** — big, bold text is visually impactful and weighs almost nothing

### Hey Low's Footer — The Gold Standard for Eco Statements

Hey Low (heylow.world) has the best eco footer we've found. It shows 4 cards:
1. **Eco Design score**: "95.6 out of 100" with a visual gauge + link to Environmental Declaration
2. **Weight comparison**: "74% lighter compared to industry average websites" (470 KB vs 2,484 KB average)
3. **Renewable energy**: "Powered by renewable energies" with wind turbine icons
4. **Privacy**: "We don't collect any personal data, we don't use cookies"

Plus memberships: Design Declares, Climate Action Tech, Clean Creatives, Creatives For Climate.

When building eco statements for websites, this 4-card pattern is an excellent template to follow — it's visual, specific, and credible.

## Honest limits — sources

For the "What lighter websites don't do" list near the top:
- Sustainable Web Design model v4: https://sustainablewebdesign.org/estimating-digital-emissions/
- Mytton et al. 2024, network energy and data: https://doi.org/10.1111/jiec.13512
- Jungers, UCLouvain master's thesis 2025 (WordPress with/without cache vs static; at most 20 req/s uncached WordPress, ~27 W CPU at 16 req/s, static up to 7,350 req/s): https://thesis.dial.uclouvain.be/bitstreams/7c67ba6c-4f78-4aa6-b574-65eeaea33a2a/download
- IEA, Energy and AI (2025) — storage ~5% of data-centre electricity; AI servers about half of the growth to 2030: https://www.iea.org/reports/energy-and-ai/energy-demand-from-ai
- Web Almanac 2024 sustainability chapter (CMS and framework medians): https://almanac.httparchive.org/en/2024/sustainability
- AI coding energy from token counts: https://www.simonpcouch.com/blog/2026-01-20-cc-impact/
- Rough scale check: if 10% of active WordPress sites went static, ~5–160 GWh/yr saved — real, but ≤0.03% of the data-centre growth expected by 2030. The case for light sites is speed, security, privacy and visibility first; energy second.

A worked public example of all of this (Korean + English, with measured before/after numbers): https://julianquintart.com/eco-web/en/

## Related Skills

- **`frontend-eco-design`** — for design-focused guidance: aesthetic direction, typography choices, imagery alternatives, site inspiration. Use when building the visual side. This is the default design skill.
- **`frontend-design`** — for unconstrained design when eco isn't a requirement.
- **`privacy-web`** — removing trackers/third-party scripts is both lighter AND more private. The three web skills (eco, design, privacy) reinforce each other.
- **`wp-to-static`** — converting a live WordPress site to static pages on the same host, keeping the design.
