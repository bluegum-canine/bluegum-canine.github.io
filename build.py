#!/usr/bin/env python3
"""Build the Bluegum Dog Training site.

Content lives as body fragments in _src/. This script wraps each one in the
shared shell (head, nav, footer, structured data) and writes the finished
HTML to the repo root, which is what GitHub Pages serves.

    python3 build.py

No dependencies, no toolchain. Edit a fragment, run this, commit.
The classes page is generated from data/events.json.
"""
import hashlib
import html
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "_src")

# --------------------------------------------------------------- identity
# One place to change the trading name. See online-presence-plan.md,
# "Decision 0" — if the name changes, this is the edit.
BRAND = "Bluegum Dog Training"
PERSON = "Mark Rabel"
DOMAIN = "https://bluegumdogtraining.com"
PHONE_DISPLAY = "085 738 6848"
PHONE_E164 = "+353857386848"
EMAIL = "newmark22@gmail.com"          # TODO: mark@bluegumdogtraining.com
AREA = "Co. Sligo & the North West"

NAV = [
    ("Services", "/services.html"),
    ("The method", "/method.html"),
    ("Common problems", "/problems/"),
    ("About", "/about.html"),
    ("Classes", "/classes.html"),
    ("Contact", "/contact.html"),
]

# --------------------------------------------------------------- structured data
# Feeds Google's local results. Keep this in step with the Google Business
# Profile — conflicting details there and here is worse than neither.
LD = {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "additionalType": "https://schema.org/ProfessionalService",
    "name": BRAND,
    "founder": {"@type": "Person", "name": PERSON},
    "url": DOMAIN,
    "telephone": PHONE_E164,
    "email": EMAIL,
    "image": DOMAIN + "/assets/img/og.jpg",
    "priceRange": "€€",
    "address": {
        "@type": "PostalAddress",
        "addressRegion": "Co. Sligo",
        "addressCountry": "IE",
    },
    "areaServed": [
        {"@type": "AdministrativeArea", "name": n}
        for n in ["County Sligo", "County Leitrim", "County Roscommon",
                  "County Mayo", "County Donegal"]
    ],
    "knowsAbout": [
        "dog training", "dog behaviour", "puppy training", "recall training",
        "lead pulling", "separation anxiety", "livestock worrying",
        "residential dog training",
    ],
}

SHELL = """<!doctype html>
<html lang="en-IE">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{brand}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{domain}/assets/img/og.jpg">
<meta property="og:locale" content="en_IE">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/assets/img/favicon.png" type="image/png">
<link rel="preload" href="/assets/fonts/BigShoulders-Bold.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/CrimsonPro-Regular.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/site.css?v={cssv}">
<script type="application/ld+json">{ld}</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>

<header class="masthead">
  <div class="wrap masthead-in">
    <a class="wordmark" href="/">
      <span class="wordmark-name">{person}</span>
      <span class="wordmark-sub">Dog training &amp; behaviour</span>
    </a>
    <nav class="nav" aria-label="Main">
      {nav}
    </nav>
    <a class="masthead-call" href="tel:{phone_e164}">{phone_display}</a>
  </div>
</header>

<main id="main">
{body}
</main>

<footer class="foot">
  <div class="wrap">
    <div class="foot-grid">
      <div class="foot-brand">
        <p class="display foot-name">{person}</p>
        <p class="label">{brand}</p>
        <p class="foot-note">Calm, methodical training for dogs that have to
           live in the real world.</p>
        <img class="foot-badge" src="/assets/img/iacp.png" alt="Member,
             International Association of Canine Professionals" width="110"
             height="133" loading="lazy">
      </div>
      <div class="foot-col">
        <p class="label">Get in touch</p>
        <ul class="plain">
          <li><a href="tel:{phone_e164}">{phone_display}</a></li>
          <li><a href="mailto:{email}">{email}</a></li>
          <li>{area}</li>
        </ul>
      </div>
      <div class="foot-col">
        <p class="label">Pages</p>
        <ul class="plain">
          {footnav}
        </ul>
      </div>
    </div>
    <p class="foot-fine">Fully insured &middot; a written plan after every
       consultation &middot; an honest assessment, always</p>
    <p class="foot-fine">&copy; {year} {person}. Site built on
       <a href="https://pages.github.com/">GitHub Pages</a>.</p>
  </div>
</footer>
</body>
</html>
"""


def css_version():
    """Short content hash on the stylesheet URL, so a redeploy is never served
    against a browser's cached copy of the old CSS."""
    p = os.path.join(ROOT, "assets", "css", "site.css")
    with open(p, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()[:8]


CSSV = None


def nav_html(current):
    out = []
    for label, href in NAV:
        cur = ' aria-current="page"' if href == current else ""
        out.append('<a href="%s"%s>%s</a>' % (href, cur, label))
    return "\n      ".join(out)


def footnav_html():
    return "\n          ".join(
        '<li><a href="%s">%s</a></li>' % (h, l) for l, h in NAV)


def render(fragment_path, out_path, title, desc, current=""):
    with open(fragment_path) as f:
        body = f.read()
    page = SHELL.format(
        title=html.escape(title), desc=html.escape(desc),
        canonical=DOMAIN + "/" + out_path.replace("index.html", "").lstrip("/"),
        brand=BRAND, person=PERSON, domain=DOMAIN,
        phone_e164=PHONE_E164, phone_display=PHONE_DISPLAY,
        email=EMAIL, area=AREA, year=2026,
        ld=json.dumps(LD, separators=(",", ":")),
        nav=nav_html(current), footnav=footnav_html(),
        cssv=CSSV, body=body,
    )
    # Let fragments use {{PHONE}}, {{EMAIL}} etc. without escaping headaches.
    for k, v in [("PHONE", PHONE_DISPLAY), ("PHONE_E164", PHONE_E164),
                 ("EMAIL", EMAIL), ("BRAND", BRAND), ("PERSON", PERSON),
                 ("AREA", AREA)]:
        page = page.replace("{{%s}}" % k, v)
    full = os.path.join(ROOT, out_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(page)
    return len(page)


# --------------------------------------------------------------- classes page
def build_classes():
    """Render data/events.json into the classes fragment's slot."""
    with open(os.path.join(ROOT, "data", "events.json")) as f:
        events = json.load(f)
    rows = []
    for e in events:
        state = e.get("state", "open")
        cls = {"open": "is-open", "few": "is-few",
               "full": "is-full"}.get(state, "is-open")
        note = {"open": "Places available", "few": "Only a few places left",
                "full": "Full — join the waiting list"}.get(state, "")
        rows.append(
            '<article class="event {cls}">\n'
            '  <p class="event-date"><span class="event-day">{day}</span>'
            '<span class="event-mon">{mon}</span></p>\n'
            '  <div class="event-body">\n'
            '    <h3>{title}</h3>\n'
            '    <p class="event-meta">{when} &middot; {venue}</p>\n'
            '    <p>{desc}</p>\n'
            '    <p class="event-status">{note} &middot; {price}</p>\n'
            '  </div>\n'
            '</article>'.format(
                cls=cls, day=e["day"], mon=e["month"],
                title=html.escape(e["title"]), when=html.escape(e["when"]),
                venue=html.escape(e["venue"]), desc=html.escape(e["desc"]),
                note=note, price=html.escape(e.get("price", ""))))
    if not rows:
        rows = ['<p class="empty">No dates are up yet. Ring or email and '
                'I will let you know as soon as the first classes are '
                'scheduled.</p>']
    src = os.path.join(SRC, "classes.html")
    with open(src) as f:
        frag = f.read()
    tmp = os.path.join(SRC, "_classes.built.html")
    with open(tmp, "w") as f:
        f.write(frag.replace("<!--EVENTS-->", "\n".join(rows)))
    return tmp


# --------------------------------------------------------------- problems
PROBLEMS = [
    ("pulling-on-the-lead", "Pulling on the lead",
     "How to stop a dog pulling on the lead — why it happens, why the usual "
     "fixes stall, and what actually works."),
    ("recall", "Poor recall",
     "A dog that will not come back. Why recall breaks down, and how to "
     "rebuild it so you can let your dog off the lead again."),
    ("nervous-around-people", "Nervous around people",
     "Barking, hiding or shrinking when visitors call. What fear-based "
     "behaviour actually is, and how it is changed."),
    ("velcro-dogs", "The velcro dog",
     "A dog that follows you room to room and cannot settle alone. "
     "Over-attachment, separation anxiety, and the difference between them."),
    ("destructive-behaviour", "Destructive at home",
     "Chewing, digging and damage while you are out — what it usually means "
     "and how to fix it properly."),
    ("livestock-worrying", "Livestock worrying",
     "The most serious problem a dog can have in the west of Ireland. What "
     "the law says, and what training can and cannot do."),
]


def main():
    global CSSV
    CSSV = css_version()
    pages = [
        ("index.html", "index.html",
         "%s — Dog Training & Behaviour, Co. Sligo" % PERSON,
         "Calm, methodical dog training in Co. Sligo and the North West. "
         "Obedience, recall, reactivity and residential training with "
         "%s — Master Trainer, IACP member." % PERSON, ""),
        ("services.html", "services.html",
         "Services — %s" % BRAND,
         "Puppy foundations, everyday obedience, behaviour consultation, "
         "one-to-one sessions and residential board-and-train in Co. Sligo.",
         "/services.html"),
        ("method.html", "method.html",
         "The method — %s" % BRAND,
         "Freedom through obedience. A balanced, bespoke approach built on "
         "four steps: teaching, reinforcing, proofing and maintaining.",
         "/method.html"),
        ("about.html", "about.html",
         "About %s — %s" % (PERSON, BRAND),
         "Forty years working with dogs, formalised with a Master Trainer "
         "certificate from Highland Canine, North Carolina. IACP member.",
         "/about.html"),
        ("contact.html", "contact.html",
         "Contact — %s" % BRAND,
         "Ring, message on WhatsApp or email. Serving Co. Sligo, Leitrim, "
         "Roscommon, Mayo and Donegal.",
         "/contact.html"),
        ("problems/index.html", "problems/index.html",
         "Common problems — %s" % BRAND,
         "Pulling on the lead, poor recall, nervousness, velcro dogs, "
         "destruction at home and livestock worrying. Every one is workable.",
         "/problems/"),
    ]

    total = 0
    for src_name, out, title, desc, cur in pages:
        total += render(os.path.join(SRC, src_name), out, title, desc, cur)
        print("  %-28s %s" % (out, title[:52]))

    # classes, generated from the events file
    tmp = build_classes()
    total += render(tmp, "classes.html", "Classes & events — %s" % BRAND,
                    "Upcoming group classes, workshops and events in Co. Sligo "
                    "and the North West.", "/classes.html")
    os.remove(tmp)
    print("  %-28s %s" % ("classes.html", "Classes & events"))

    # one page per problem
    for slug, title, desc in PROBLEMS:
        total += render(os.path.join(SRC, "problems", slug + ".html"),
                        "problems/%s.html" % slug,
                        "%s — %s" % (title, BRAND), desc, "/problems/")
        print("  %-28s %s" % ("problems/%s.html" % slug, title))

    # robots + sitemap
    urls = ["/", "/services.html", "/method.html", "/about.html",
            "/classes.html", "/contact.html", "/problems/"] + \
           ["/problems/%s.html" % s for s, _, _ in PROBLEMS]
    with open(os.path.join(ROOT, "sitemap.xml"), "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u in urls:
            f.write("  <url><loc>%s%s</loc></url>\n" % (DOMAIN, u))
        f.write("</urlset>\n")
    with open(os.path.join(ROOT, "robots.txt"), "w") as f:
        f.write("User-agent: *\nAllow: /\nDisallow: /_src/\n\n"
                "Sitemap: %s/sitemap.xml\n" % DOMAIN)

    print("\n%d pages, %.1f KB of HTML" % (len(pages) + 1 + len(PROBLEMS),
                                           total / 1024.0))


if __name__ == "__main__":
    main()
