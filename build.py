#!/usr/bin/env python3
"""Build the Bluegum Canine site.

Content lives as body fragments in _src/. This script wraps each one in the
shared shell (head, nav, footer, structured data) and writes the finished
HTML to the repo root, which is what GitHub Pages serves.

    python3 build.py

No dependencies, no toolchain. Edit a fragment, run this, commit.
"""
import datetime
import hashlib
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "_src")

# --------------------------------------------------------------- identity
# One place to change the trading name. See online-presence-plan.md,
# "Decision 0" — if the name changes, this is the edit.
BRAND = "Bluegum Canine"
# First name only, deliberately. The business is the brand; the person is the
# face. This feeds the footer, the About title, the meta descriptions and the
# LocalBusiness founder field, so it is the single edit for all of them.
PERSON = "Mark"
# The domain the business will launch on. Registered at Blacknight on
# 24 Aug 2026 along with bluegumcanine.com, which forwards here — .ie leads
# because to a local buyer it reads as *here*. Not yet pointed at GitHub and
# deliberately so: SERVE_ORIGIN below is what canonical and og:url actually
# use, and it stays on github.io until launch. See Decisions D-18.
DOMAIN = "https://bluegumcanine.ie"
PHONE_DISPLAY = "085 738 6848"
PHONE_E164 = "+353857386848"
# wa.me takes digits only — a leading + makes the link fail rather than
# open a chat, so the WhatsApp link uses this and tel: uses the E.164 form.
PHONE_WA = PHONE_E164.lstrip("+")
# On every page, in the footer and in the LocalBusiness structured data.
# Live since 25 Aug 2026 — Titan mailbox at Blacknight, sending and receiving
# both tested. MX, SPF and DKIM are published; DMARC is still to be added.
# Matches the primary domain deliberately: mark@bluegumcanine.com would work
# too, but mixing the two across the site invites mistyping.
EMAIL = "mark@bluegumcanine.ie"
AREA = "Sligo, the North West & beyond"

# --------------------------------------------------------------- milestones
# The site was written from a future vantage point: it described the Master
# Trainer certificate as held and the practice as trading, neither of which
# was true when the pages were first built. Rather than write it twice and
# have to remember to come back, the two dates are declared here and the
# copy around them is chosen at build time. Rebuild after either date and
# the tense corrects itself.
#
# Anything asserting the certificate or a client caseload goes through a
# token below — do not hard-code either claim into a fragment.
CERT_DATE = datetime.date(2026, 12, 18)   # last day at Highland Canine
CLIENTS_FROM = datetime.date(2027, 1, 1)  # first client dogs taken

TODAY = datetime.date.today()
QUALIFIED = TODAY >= CERT_DATE
TRADING = TODAY >= CLIENTS_FROM

# About — the paragraph that carries the programme itself.
CERT_STATUS = (
    "The certificate is dated 18 December 2026."
    if QUALIFIED else
    "I am on the programme as I write this. It finishes on 18 December 2026 "
    "and the certificate is dated that day, so if you are reading this before "
    "then, take it as work in progress rather than a qualification I already "
    "hold."
)
# Homepage — the short About panel.
CERT_SENTENCE = (
    "Master Trainer, Highland Canine School for Dog Trainers, North Carolina "
    "&mdash; six months residential, 960 hours on campus, completed December "
    "2026."
    if QUALIFIED else
    "Currently completing the Master Trainer Program at the Highland Canine "
    "School for Dog Trainers, North Carolina &mdash; six months residential, "
    "960 hours on campus, finishing December 2026."
)
# About — the credentials list.
CERT_TAG = ("Completed December 2026." if QUALIFIED
            else "In progress; finishes 18 December 2026.")
# Qualification page — the opening statement of fact.
CERT_LINE = (
    "Certificate dated 18 December 2026."
    if QUALIFIED else
    "The programme finishes on 18 December 2026 and the certificate is dated "
    "that day. Until then this is what I am in the middle of, not something "
    "I have finished."
)
# Homepage — the twelve problems. Before the first client dogs there is no
# caseload to generalise from, so the claim is about the trade, not about me.
CALLS = ("Twelve problems account for most of the calls I get."
         if TRADING else
         "Twelve problems account for most of what people ring a dog trainer "
         "about.")
DOGS = ("Most of the dogs I see are not a first attempt"
        if TRADING else
        "Most dogs that reach a trainer are not a first attempt")
# Used in the meta descriptions, which cannot carry markup.
CRED_META = ("a Master Trainer and full IACP member" if QUALIFIED
             else "a full IACP member completing a Master Trainer programme")

# --------------------------------------------------------------- visibility
# PRIVATE = True builds a site that is reachable by anyone holding the link
# but is kept out of search results. It does three things: puts a noindex
# robots meta on every page, writes a robots.txt that refuses the scrapers
# outright while still letting the real search engines in (they have to be
# able to crawl the page in order to READ the noindex — block them in
# robots.txt and they can end up listing the bare URL instead), and skips
# the sitemap, which exists purely to invite indexing.
#
# This is obscurity, not a lock. Anyone with the URL can open it.
# Set to False on launch day and rebuild.
PRIVATE = True

# Where the build is actually served from, right now. A GitHub *project*
# page lives under a subpath, so BASE prefixes every root-relative link and
# asset — without it each /assets/... and /services.html 404s. The fonts in
# site.css use ../fonts/ relative paths so they survive any BASE.
#
# On launch: SERVE_ORIGIN = DOMAIN, BASE = "", rename CNAME.disabled back.
SERVE_ORIGIN = "https://bluegum-canine.github.io"
BASE = ""

# The origin used for canonical, og:url, og:image and the structured data.
# It has to be somewhere that actually resolves or link previews break, so
# it follows the real serving location rather than the eventual domain.
SITE = SERVE_ORIGIN + BASE

NAV = [
    ("Services", "/services.html"),
    ("The method", "/method.html"),
    ("Common problems", "/problems/"),
    ("Case studies", "/case-studies.html"),
    ("About", "/about.html"),
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
    "url": SITE,
    "telephone": PHONE_E164,
    "email": EMAIL,
    "image": SITE + "/assets/img/og.jpg",
    "priceRange": "€€",
    "address": {
        "@type": "PostalAddress",
        "addressRegion": "Co. Sligo",
        "addressCountry": "IE",
    },
    # Drive-time rings from the base in south Co. Sligo near Boyle, not a
    # fixed region. See the rings on the About page. The counties are
    # the one-to-one catchment; residential, assistance dog and assessment work
    # is taken nationally, hence Ireland on the end.
    "areaServed": [
        {"@type": "AdministrativeArea", "name": n}
        for n in ["County Sligo", "County Leitrim", "County Roscommon",
                  "County Longford", "County Mayo", "County Cavan",
                  "County Westmeath", "County Galway", "County Donegal"]
    ] + [{"@type": "Country", "name": "Ireland"}],
    "knowsAbout": [
        "dog training", "dog behaviour", "puppy training", "recall training",
        "lead pulling", "separation anxiety", "livestock worrying",
        "residential dog training",
    ],
}

# Search engines are deliberately ALLOWED here. They have to fetch the page
# to see the noindex meta tag on it; a blanket Disallow would stop them
# reading it, and Google will then sometimes list the bare URL anyway.
# The bots that are refused outright are the ones that copy content rather
# than index it. All of this is advisory — robots.txt is a request, not a
# fence, and a crawler that ignores it will simply ignore it.
PRIVATE_ROBOTS = """# This site is unfinished and is not to appear in search results.
# Every page also carries <meta name="robots" content="noindex">.

# --- search engines: allowed to crawl, so they can read the noindex ---
User-agent: Googlebot
User-agent: Googlebot-Image
User-agent: Bingbot
User-agent: DuckDuckBot
User-agent: Applebot
User-agent: Slurp
User-agent: Baiduspider
User-agent: YandexBot
Allow: /
Disallow: /_src/

# --- link previews: allowed, so a shared link still shows a card ---
User-agent: facebookexternalhit
User-agent: WhatsApp
User-agent: Twitterbot
User-agent: LinkedInBot
User-agent: TelegramBot
User-agent: Slackbot-LinkExpanding
Allow: /

# --- everything else, including AI training and SEO scrapers ---
User-agent: GPTBot
User-agent: OAI-SearchBot
User-agent: ChatGPT-User
User-agent: ClaudeBot
User-agent: Claude-Web
User-agent: anthropic-ai
User-agent: Google-Extended
User-agent: Applebot-Extended
User-agent: CCBot
User-agent: PerplexityBot
User-agent: Bytespider
User-agent: Amazonbot
User-agent: meta-externalagent
User-agent: cohere-ai
User-agent: Diffbot
User-agent: ImagesiftBot
User-agent: Omgilibot
User-agent: YouBot
User-agent: AhrefsBot
User-agent: SemrushBot
User-agent: MJ12bot
User-agent: DotBot
User-agent: dataforseoBot
User-agent: *
Disallow: /
"""

ROBOTS_META = (
    '<meta name="robots" content="noindex, nofollow, noarchive, nosnippet, '
    'noimageindex">\n'
    '<meta name="googlebot" content="noindex, nofollow, noarchive, nosnippet, '
    'noimageindex">\n'
) if PRIVATE else ""

SHELL = """<!doctype html>
<html lang="en-IE">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{robotsmeta}<title>{title}</title>
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
<link rel="icon" href="/assets/img/logo/logo-mark.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/assets/img/favicon.png" type="image/png">
<link rel="preload" href="/assets/fonts/Fraunces-Variable.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/CrimsonPro-Regular.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/site.css?v={cssv}">
<script type="application/ld+json">{ld}</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>

<header class="masthead">
  <div class="wrap masthead-in">
    <a class="wordmark" href="/">
      <img class="wordmark-mark" src="/assets/img/logo/seal-paper.png"
           width="454" height="454" alt="">
      <span class="wordmark-text">
        <span class="wordmark-name">{brand}</span>
        <span class="wordmark-sub">Behaviour practice &middot; Co. Sligo</span>
      </span>
    </a>
    <details class="navtoggle">
      <summary aria-label="Menu">Menu</summary>
    </details>
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
        <img class="foot-seal" src="/assets/img/logo/seal-moss.png"
             width="454" height="454" loading="lazy" alt="">
        <p class="display foot-name">{brand}</p>
        <p class="label">{person} &middot; Behaviour practice, Co. Sligo</p>
        <p class="foot-note">Calm, methodical training for dogs that have to
           live in the real world.</p>
        <span class="foot-badges">
          <a href="https://highlandcanine.com/" target="_blank" rel="noopener noreferrer"
             aria-label="Highland Canine Training (opens in a new tab)"><img
             class="foot-badge" src="/assets/img/highland.png"
             alt="Highland Canine Training, LLC" width="180" height="37"
             loading="lazy"></a>
          <a href="https://iacpdogs.org/" target="_blank" rel="noopener noreferrer"
             aria-label="International Association of Canine Professionals (opens in a new tab)"><img
             class="foot-badge" src="/assets/img/iacp-logo.png"
             alt="International Association of Canine Professionals" width="180"
             height="54" loading="lazy"></a>
        </span>
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
    <p class="foot-fine">&copy; {year} {brand}. Site built on
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
        canonical=SITE + "/" + out_path.replace("index.html", "").lstrip("/"),
        brand=BRAND, person=PERSON, domain=SITE,
        phone_e164=PHONE_E164, phone_display=PHONE_DISPLAY,
        email=EMAIL, area=AREA, year=2026,
        ld=json.dumps(LD, separators=(",", ":")),
        nav=nav_html(current), footnav=footnav_html(),
        cssv=CSSV, body=body, robotsmeta=ROBOTS_META,
    )
    # Let fragments use {{PHONE}}, {{EMAIL}} etc. without escaping headaches.
    for k, v in [("PHONE", PHONE_DISPLAY), ("PHONE_E164", PHONE_E164),
                 ("PHONE_WA", PHONE_WA),
                 ("EMAIL", EMAIL), ("BRAND", BRAND), ("PERSON", PERSON),
                 ("AREA", AREA),
                 ("CERT_STATUS", CERT_STATUS), ("CERT_SENTENCE", CERT_SENTENCE),
                 ("CERT_TAG", CERT_TAG), ("CERT_LINE", CERT_LINE),
                 ("CALLS", CALLS), ("DOGS", DOGS)]:
        page = page.replace("{{%s}}" % k, v)
    if BASE:
        page = re.sub(r'\b(href|src)="/(?!/)', r'\1="%s/' % BASE.rstrip("/"),
                      page)
    full = os.path.join(ROOT, out_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(page)
    return len(page)



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
    ("reactive-to-other-dogs", "Barking and lunging at other dogs",
     "Barking, lunging and aggression toward other dogs on the lead. Why "
     "\u201creactive\u201d is not a diagnosis, and how the distance is rebuilt."),
    ("resource-guarding", "Guarding food and toys",
     "Growling over the food bowl or guarding toys. Why punishing the growl "
     "is the worst thing you can do, and what works instead."),
    ("barking-at-visitors", "Barking at every visitor",
     "A dog that erupts at the doorbell. Alerting, excitement or fear \u2014 "
     "they look alike and need different plans."),
    ("noise-fear", "Frightened of thunder and fireworks",
     "Shaking, hiding and bolting at storms and bangs. Why you cannot spoil a "
     "frightened dog, and the work that has to be done out of season."),
    ("car-travel", "Refuses to get in the car",
     "A dog that plants itself at the boot or travels badly. Loading, travel "
     "sickness and why the car has come to mean the vet."),
    ("repetitive-behaviour", "Spinning, pacing and chasing shadows",
     "Spinning, tail chasing, fence pacing, shadow and light chasing and lick "
     "sores \u2014 where compulsive behaviour comes from, and why never to use "
     "a laser pen with a dog."),
]


def main():
    global CSSV
    CSSV = css_version()
    pages = [
        ("index.html", "index.html",
         "%s — Dog Training & Behaviour, Co. Sligo" % BRAND,
         "Calm, methodical dog training from Co. Sligo across Connacht and the "
         "midlands. Obedience, recall, reactivity and residential training with "
         "%s, %s." % (PERSON, CRED_META), ""),
        ("services.html", "services.html",
         "Services — %s" % BRAND,
         "Puppy foundations, everyday obedience, behaviour consultation, "
         "one-to-one sessions, residential board-and-train and assistance dog "
         "work, from Co. Sligo.",
         "/services.html"),
        ("method.html", "method.html",
         "The method — %s" % BRAND,
         "Freedom through obedience. A balanced, bespoke approach built on "
         "four steps: teaching, reinforcing, proofing and maintaining.",
         "/method.html"),
        ("about.html", "about.html",
         "About %s — %s" % (PERSON, BRAND),
         "Twenty years working with dogs, and %s at the Highland Canine "
         "School for Dog Trainers, North Carolina - a six-month residential "
         "programme, 960 hours. Full member of the International Association "
         "of Canine Professionals since 2025."
         % ("a Master Trainer certificate" if QUALIFIED
            else "completing the Master Trainer Program"),
         "/about.html"),
        ("qualification.html", "qualification.html",
         "The qualification — %s" % BRAND,
         "960 hours across 34 modules at Highland Canine, North Carolina — a "
         "six-month residential Master Trainer programme. The full module list, "
         "published.",
         "/qualification.html"),
        # SHELVED 24 Aug 2026 — the training-tools page. The source is kept at
        # _src/training-tools.shelved.html. It named prong and electronic
        # collars directly, which invites an argument the business does not
        # need; the balanced-approach section on the method page carries the
        # position without naming hardware. Re-add this entry to publish it.
        ("assistance-dogs.html", "assistance-dogs.html",
         "Assistance dogs and the law — %s" % BRAND,
         "What the law actually says about assistance dogs in Ireland and the "
         "UK, compared with the American rules. Access rights, owner-trained "
         "dogs, and which kinds of dog the legislation names.",
         "/assistance-dogs.html"),
        ("case-studies.html", "case-studies.html",
         "Case studies — %s" % BRAND,
         "Chloe: a stray Doodle with a bite history who would not take food or "
         "play, taught a reliable off-lead recall in seven days. The presenting "
         "problem, the plan, how long it took and where the dog ended up.",
         "/case-studies.html"),
        ("contact.html", "contact.html",
         "Contact — %s" % BRAND,
         "Ring, message on WhatsApp or email. Sligo, Leitrim, Roscommon, "
         "Longford, Mayo and Cavan as standard — residential and assistance "
         "dog work taken from anywhere in Ireland.",
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


    # one page per problem
    for slug, title, desc in PROBLEMS:
        total += render(os.path.join(SRC, "problems", slug + ".html"),
                        "problems/%s.html" % slug,
                        "%s — %s" % (title, BRAND), desc, "/problems/")
        print("  %-28s %s" % ("problems/%s.html" % slug, title))

    # robots + sitemap
    urls = ["/", "/services.html", "/method.html", "/about.html",
            "/qualification.html", "/assistance-dogs.html",
            "/case-studies.html",
            "/contact.html", "/problems/"] + \
           ["/problems/%s.html" % s for s, _, _ in PROBLEMS]
    sitemap = os.path.join(ROOT, "sitemap.xml")
    if PRIVATE:
        # A sitemap is an invitation. Don't publish one, and remove any
        # left behind by an earlier public build.
        if os.path.exists(sitemap):
            os.remove(sitemap)
        with open(os.path.join(ROOT, "robots.txt"), "w") as f:
            f.write(PRIVATE_ROBOTS)
    else:
        with open(sitemap, "w") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            for u in urls:
                f.write("  <url><loc>%s%s</loc></url>\n" % (DOMAIN, u))
            f.write("</urlset>\n")
        with open(os.path.join(ROOT, "robots.txt"), "w") as f:
            f.write("User-agent: *\nAllow: /\nDisallow: /_src/\n\n"
                    "Sitemap: %s/sitemap.xml\n" % DOMAIN)

    print("\n%d pages, %.1f KB of HTML" % (len(pages) + len(PROBLEMS),
                                           total / 1024.0))


if __name__ == "__main__":
    main()
