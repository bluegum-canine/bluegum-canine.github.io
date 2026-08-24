# Bluegum Dog Training — website

Static site for **Mark Rabel · Dog Training & Behaviour**, Co. Sligo.
Hosted on GitHub Pages at `bluegumdogtraining.com`.

No framework, no build tooling, no dependencies. Plain Python 3.

---

## How it works

Page content lives as body fragments in `_src/`. `build.py` wraps each one in
the shared shell — head, nav, footer, structured data — and writes finished
HTML to the repo root, which is what GitHub Pages serves.

```bash
python3 build.py
```

That's the whole workflow. Edit a fragment, run the build, commit, push.
GitHub Pages publishes within a minute or two.

```
_src/                 ← EDIT HERE. Body content only.
  index.html
  services.html
  method.html
  about.html
  contact.html
  classes.html        ← <!--EVENTS--> is replaced from data/events.json
  problems/*.html
data/events.json      ← the classes calendar
assets/css/site.css   ← all styling
assets/fonts/         ← self-hosted woff2 (see GDPR note below)
assets/img/
build.py              ← shell, nav, SEO metadata, brand constants
*.html                ← GENERATED. Do not edit; your changes get overwritten.
```

## Adding or changing a class

Edit `data/events.json` and rebuild. Entries render newest-first in file
order, so put them in the order you want them shown.

```json
{
  "day": "14",
  "month": "Jan",
  "title": "Everyday obedience — six-week block",
  "when": "Tuesdays 7–8pm, from 14 January",
  "venue": "Community hall, Boyle",
  "desc": "Recall, settle, loose-lead walking and a reliable stop.",
  "price": "€120",
  "state": "open"
}
```

`state` is one of `open`, `few` or `full`, and controls the colour and the
status line. An empty `[]` shows a "no dates yet" message instead — which is
what ships, deliberately, so no one turns up to a class that doesn't exist.
Worked examples are in `data/events.example.json`.

## Things that still need a real answer

These are placeholders, marked so they can't be published by accident:

- **Prices.** Every service shows `Price to confirm`. Search `_src/` for that
  string.
- **Email.** Still `newmark22@gmail.com`. Change `EMAIL` in `build.py` once
  `mark@bluegumdogtraining.com` exists.
- **Trading name.** The site is built as *Bluegum Dog Training* with Mark
  Rabel as the face. If that changes, `BRAND` in `build.py` is the one edit.
- **Booking calendar.** `_src/contact.html` has a placeholder block where a
  Cal.com embed goes.
- **Testimonials.** Nothing invented. Add real ones after the first clients.

## Notes on some decisions

**Fonts are self-hosted rather than loaded from Google Fonts.** Loading them
from Google's CDN sends every Irish visitor's IP address to Google, which a
German court found unlawful under GDPR in 2022. Self-hosting sidesteps the
question entirely and is faster. Licences are OFL and travel with the files.

**No dark mode.** The warm paper tone is the identity, carried over from the
brochure. Inverting it would leave nothing recognisable behind.

**The stylesheet URL carries a content hash** (`site.css?v=…`), regenerated on
each build, so a redeploy is never served against a cached copy of the old CSS.

**Structured data** (`LocalBusiness` JSON-LD in `build.py`) feeds Google's
local results. Keep it in step with the Google Business Profile — conflicting
details in the two places is worse than having neither.

## Deploying

Push to `main`. GitHub Pages builds from the repo root, with `.nojekyll` set so
files are served exactly as committed. `CNAME` holds the custom domain.

DNS at the registrar needs four `A` records for the apex, and a `CNAME` for
`www`:

```
@    A      185.199.108.153
@    A      185.199.109.153
@    A      185.199.110.153
@    A      185.199.111.153
www  CNAME  squirreleater.github.io
```

## Visibility

The site is built with `PRIVATE = True` in `build.py`. That puts a `noindex`
robots meta on all 20 pages, writes a `robots.txt` that refuses the scrapers
while still letting real search engines crawl (they must be able to read the
noindex), and skips `sitemap.xml` entirely. It is obscurity, not a lock —
anyone with the link can open it.

`CNAME` is parked as `CNAME.disabled` because `bluegumdogtraining.com` still
points at GoDaddy. A live `CNAME` file makes GitHub redirect the `github.io`
URL to the custom domain, which would take the site offline until the DNS is
changed. To go live: point the domain's A records at GitHub Pages, rename the
file back to `CNAME`, set `PRIVATE = False`, and rebuild.
