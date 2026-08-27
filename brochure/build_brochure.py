#!/usr/bin/env python3
"""Build the Bluegum Canine tri-fold brochure.

    python3 brochure/build_brochure.py

Six panels over two A4 landscape pages: page 1 is the outside (method flap,
back cover, front cover), page 2 the inside. Fold twice.

This lives in the repo on purpose. The previous brochure generator was
written in a scratch directory, that directory was cleaned, and the only
surviving artefacts were PDFs nobody could edit — which is why the old
brochures still said MARK RABEL and "forty years" long after the site
had stopped.

Needs: pymupdf, fonttools, brotli.  The site's woff2 faces are converted
to ttf at build time, and Fraunces is pinned to a static instance, because
a PDF embedding a variable font renders at its default weight rather than
the one the site uses.
"""
import os, tempfile

import pymupdf
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "assets", "fonts")
IMG = os.path.join(ROOT, "assets", "img")
OUT = os.path.join(ROOT, "brochure", "bluegum-canine-trifold.pdf")
_TMP = tempfile.mkdtemp(prefix="bluegum-brochure-")

# ---------------------------------------------------------------- identity
PHONE = "085 738 6848"
EMAIL = "mark@bluegumcanine.ie"

# ------------------------------------------------------------------ palette
PAPER = (0.949, 0.929, 0.894)
INK = (0.173, 0.157, 0.133)
MOSS = (0.200, 0.239, 0.192)
ACCENT = (0.541, 0.306, 0.125)      # #8A4E20 — accent TEXT on paper, 5.6:1
ACCENT_RULE = (0.659, 0.392, 0.173)  # #A8642C — decoration only
MUTED = (0.392, 0.361, 0.318)        # #645C51 — secondary text, 5.6:1
RULE = (0.812, 0.776, 0.714)

# ------------------------------------------------------------------- layout
PW, PH = 842.0, 595.0          # A4 landscape
PANEL = PW / 3.0
PAD = 30.0
TOP = 44.0
BOT = PH - 40.0


def _ttf(tmp):
    """woff2 -> ttf, with Fraunces pinned to a static weight."""
    paths = {}
    for name in ("CrimsonPro-Regular", "CrimsonPro-Italic", "GeistMono-Regular"):
        f = TTFont(os.path.join(FONTS, name + ".woff2"))
        f.flavor = None
        p = os.path.join(tmp, name + ".ttf")
        f.save(p)
        paths[name] = p
    for wght, label in ((500, "Medium"), (600, "SemiBold")):
        f = TTFont(os.path.join(FONTS, "Fraunces-Variable.woff2"))
        f.flavor = None
        inst = instancer.instantiateVariableFont(f, {"wght": wght, "opsz": 96},
                                                 inplace=False)
        p = os.path.join(tmp, "Fraunces-%s.ttf" % label)
        inst.save(p)
        paths["Fraunces-" + label] = p
    return paths


_CROPS = {}


def _cropped(path, aspect):
    """Return a centre-cropped copy of `path` at the given width/height ratio."""
    key = (path, round(aspect, 3))
    if key in _CROPS:
        return _CROPS[key]
    from PIL import Image
    im = Image.open(path).convert("RGB")
    w, h = im.size
    if w / h > aspect:                     # too wide: trim the sides
        nw = int(round(h * aspect))
        box = ((w - nw) // 2, 0, (w - nw) // 2 + nw, h)
    else:                                  # too tall: trim top and bottom
        nh = int(round(w / aspect))
        box = (0, (h - nh) // 2, w, (h - nh) // 2 + nh)
    out = os.path.join(_TMP, "%s-%s.jpg" % (os.path.splitext(os.path.basename(path))[0],
                                            key[1]))
    im.crop(box).save(out, quality=88)
    _CROPS[key] = out
    return out


class Panel:
    """A column with a cursor, so blocks stack without hand-placed y values."""

    def __init__(self, page, index, fonts):
        self.page = page
        self.x0 = index * PANEL + PAD
        self.x1 = (index + 1) * PANEL - PAD
        self.y = TOP
        self.fonts = fonts

    @property
    def w(self):
        return self.x1 - self.x0

    def _put(self, text, font, size, color, leading, align=0, gap_after=0):
        rect = pymupdf.Rect(self.x0, self.y, self.x1, BOT)
        left = self.page.insert_textbox(
            rect, text, fontname=font, fontfile=self.fonts[font],
            fontsize=size, color=color, align=align, lineheight=leading)
        if left < 0:                      # did not fit; report rather than clip
            raise RuntimeError("overflow in panel at y=%.0f: %r" % (self.y, text[:40]))
        self.y = BOT - left + gap_after

    def label(self, text, color=ACCENT, gap=7):
        """Letter-spaced small caps, shrunk until it sits on one line.

        Spacing is faked by inserting spaces between characters, which makes
        a long label very wide — wide enough to wrap mid-word and read as a
        mistake. So measure it and step the size down instead."""
        spaced = " ".join(text.upper())
        font = pymupdf.Font(fontfile=self.fonts["GeistMono-Regular"])
        size = 6.4
        while size > 4.6 and font.text_length(spaced, size) > self.w:
            size -= 0.2
        if font.text_length(spaced, size) > self.w:   # still too long: no spacing
            spaced, size = text.upper(), 6.4
        self._put(spaced, "GeistMono-Regular", size, color, 1.6, gap_after=gap)

    def heading(self, text, size=19, gap=9, color=MOSS):
        self._put(text, "Fraunces-SemiBold", size, color, 1.12, gap_after=gap)

    def body(self, text, size=8.3, color=INK, gap=7, italic=False):
        f = "CrimsonPro-Italic" if italic else "CrimsonPro-Regular"
        self._put(text, f, size, color, 1.45, gap_after=gap)

    def rule(self, gap=10, color=RULE):
        self.page.draw_line(pymupdf.Point(self.x0, self.y),
                            pymupdf.Point(self.x1, self.y),
                            color=color, width=0.6)
        self.y += gap

    def item(self, num, title, text=None, gap=8):
        y0 = self.y
        self.page.insert_textbox(
            pymupdf.Rect(self.x0, y0, self.x0 + 22, y0 + 14),
            num, fontname="GeistMono-Regular",
            fontfile=self.fonts["GeistMono-Regular"],
            fontsize=6.4, color=ACCENT)
        sub = Panel(self.page, 0, self.fonts)
        sub.x0, sub.x1, sub.y = self.x0 + 26, self.x1, y0
        sub.heading(title, size=10.5, gap=3)
        if text:
            sub.body(text, size=7.8, color=MUTED, gap=0)
        self.y = sub.y + gap

    def image(self, name, height, gap=10):
        """Centre-crop to the target aspect. keep_proportion=False stretches,
        and a stretched photograph of a dog is instantly obvious."""
        if self.y + height > BOT:
            raise RuntimeError("image %s overflows: needs %.0fpt, %.0fpt left"
                               % (name, height, BOT - self.y))
        r = pymupdf.Rect(self.x0, self.y, self.x1, self.y + height)
        self.page.insert_image(r, filename=_cropped(os.path.join(IMG, name),
                                                    r.width / r.height),
                               keep_proportion=False)
        self.y = r.y1 + gap

    def seal(self, name, size, centred=True, gap=12):
        if self.y + size > BOT:
            raise RuntimeError("seal overflows the panel")
        x = self.x0 + (self.w - size) / 2 if centred else self.x0
        r = pymupdf.Rect(x, self.y, x + size, self.y + size)
        self.page.insert_image(r, filename=os.path.join(IMG, name))
        self.y = r.y1 + gap


def build():
    fonts = _ttf(_TMP)
    doc = pymupdf.open()

    # ============================================================= OUTSIDE
    p1 = doc.new_page(width=PW, height=PH)
    p1.draw_rect(pymupdf.Rect(0, 0, PW, PH), color=PAPER, fill=PAPER)

    # --- flap: the method -------------------------------------------------
    a = Panel(p1, 0, fonts)
    a.label("The method")
    a.heading("Two principles", 22, gap=12)
    a.rule()
    a.item("01", "Freedom through obedience",
           "A dog that will recall, settle and walk on a loose lead is a dog "
           "that gets to come with you. Obedience is not about control — it is "
           "what buys a dog its liberty.")
    a.rule()
    a.item("02", "Treat the cause, not the symptom",
           "A dog barks, then growls, then shows its teeth, and only then "
           "bites. Punish the growl and the growling stops — but the fear is "
           "untouched, and the next time there is no warning at all.")
    a.rule(gap=12)
    a.body("A balanced approach, said plainly rather than hidden behind a "
           "label. No two dogs arrive with the same history of what has paid "
           "off for them, so the plan is built for the dog in front of me.")
    a.body("Correction is reserved for behaviours with real safety "
           "consequences. Nuisance habits are better solved by changing the "
           "setup — reaching for correction on those is both unkind and "
           "ineffective.", gap=14)
    a.image("plate-hands.jpg", 132)

    # --- back cover: who, and how to reach him ---------------------------
    b = Panel(p1, 1, fonts)
    b.y = TOP - 8
    b.seal("logo/seal-moss.png", 84, gap=12)
    b.heading("Bluegum Canine", 23, gap=5)
    b.label("Behaviour practice", color=MUTED, gap=12)
    b.rule()
    b.body("Twenty years with dogs, formalised in December 2026 with a Master "
           "Trainer certificate from the Highland Canine School for Dog "
           "Trainers, North Carolina — a six-month residential programme, "
           "960 hours across 34 modules.")
    b.body("Taught by Jason Purgason, the school's primary instructor and "
           "current President of the International Association of Canine "
           "Professionals. Full member of the IACP since 2025.", gap=12)
    b.rule()
    b.label("Telephone", gap=3)
    b.heading(PHONE, 15, gap=9)
    b.label("Email", gap=3)
    b.heading(EMAIL, 11, gap=9)
    b.label("Serving", gap=3)
    b.heading("Sligo, and a long way past it", 12.5, gap=7)
    b.body("Fully insured · a written plan after every consultation · an "
           "honest assessment, always", size=7.4, color=MUTED, gap=0)

    # --- front cover ------------------------------------------------------
    c = Panel(p1, 2, fonts)
    c.label("Dog training & behaviour")
    c.image("hero-poster.jpg", 186)
    c.heading("Bluegum Canine", 27, gap=8)
    c.body("Calm, methodical training for dogs that have to live in the real "
           "world.", size=9.5, italic=True, gap=14)
    c.rule(color=ACCENT_RULE, gap=12)
    c.body("Walks you enjoy, a recall you can trust, and a dog that can come "
           "with you.", size=11.5, color=MOSS, italic=True, gap=10)
    c.body("Most dogs have far more in them than their owners expect — "
           "including the ones who have tried before.", color=MUTED, gap=14)
    c.seal("logo/seal-moss.png", 44, gap=9)
    c.label("Co. Sligo, Ireland", color=MUTED)

    # ============================================================== INSIDE
    p2 = doc.new_page(width=PW, height=PH)
    p2.draw_rect(pymupdf.Rect(0, 0, PW, PH), color=PAPER, fill=PAPER)

    d = Panel(p2, 0, fonts)
    d.label("Where most people start")
    d.heading("If you have already tried", 22, gap=12)
    d.body("Most of the dogs I see are not a first attempt. Their owners have "
           "read the books, watched the videos, and very often worked with a "
           "trainer already. That is a good place to start from — it usually "
           "means the groundwork is there and something specific is missing.")
    d.body("Advice that works beautifully for one dog can do very little for "
           "another.", gap=14)
    d.label("What people usually ring about")
    d.rule()
    for n, t, s in (("01", "Pulling on the lead", "Walks that are a battle, not a pleasure."),
                    ("02", "Barking and lunging at other dogs", "The most common call I get."),
                    ("03", "Nervous around people", "Shrinking, barking or hiding when visitors call."),
                    ("04", "Poor recall", "A dog you dare not let off the lead."),
                    ("05", "Guarding food or toys", "Growling over the bowl, stiff over a toy.")):
        d.item(n, t, s, gap=6)
        d.rule(gap=6)
    d.body("Every one of these is workable.", gap=14)
    d.heading("And no dog is too old to learn", 15, gap=7)
    d.body("Learning does not stop with age. Older dogs take on new behaviour "
           "perfectly well, given the steps in order.")

    e = Panel(p2, 1, fonts)
    e.label("Services offered")
    e.heading("How I can help", 22, gap=12)
    e.rule()
    for n, t, s in (("01", "Puppy foundations", "Socialisation, handling and good habits early."),
                    ("02", "Everyday obedience", "Recall, settle, loose lead — earned freedom."),
                    ("03", "Behaviour consultation", "Reactivity, aggression, anxiety, livestock worrying."),
                    ("04", "One-to-one sessions", "At your home, or on ground of your choosing."),
                    ("05", "Residential training", "Board-and-train, for a proper run at it.")):
        e.item(n, t, s, gap=6)
        e.rule(gap=6)
    e.y += 6
    e.label("One thing that explains a lot")
    e.body("Dogs cope well with always. They cope well with never. They cope "
           "very badly with sometimes.")
    e.body("A great deal of training that stalls is really a household that "
           "has not yet agreed the rules. We sort the people out first, and "
           "the dog usually follows without much argument.", gap=14)
    e.image("plate-kneeling.jpg", 104, gap=0)   # centre band holds both faces

    f = Panel(p2, 2, fonts)
    f.label("The stepped approach")
    f.heading("Four steps", 20, gap=8)
    f.body("Every behaviour goes through the same four steps. Skip one and "
           "it will not hold.", gap=9)
    f.rule()
    for n, t, s in (("01", "Teaching", "What the behaviour is. Should take the longest; most often rushed."),
                    ("02", "Reinforcing", "Consistent consequences, until it is reliable not optional."),
                    ("03", "Proofing", "Distance, duration and distraction, until it holds anywhere."),
                    ("04", "Maintaining", "Keeping it there. This is where I teach you, not the dog.")):
        f.item(n, t, s, gap=5)
        f.rule(gap=5)
    f.y += 4
    f.label("How it works")
    f.rule()
    for n, t in (("01", "We talk on the phone first."),
                 ("02", "I assess your dog where the behaviour happens."),
                 ("03", "You get a written plan, and support while you work it.")):
        f.item(n, t, None, gap=6)
    f.y += 4
    f.label("Two things I will say early")
    f.rule()
    f.body("Health before behaviour. A sudden change with no obvious cause "
           "goes to your vet before it comes to me.", gap=6)
    f.body("It often looks worse before it looks better. A behaviour on its "
           "way out tends to spike first — that is where most people give "
           "up.", gap=0)

    # Fold guides, outside the trim. Re-fetch the pages from the document:
    # inserting images invalidates the page handles held from new_page().
    for page in (doc[0], doc[1]):
        for x in (PANEL, PANEL * 2):
            page.draw_line(pymupdf.Point(x, 0), pymupdf.Point(x, 14),
                           color=RULE, width=0.4)
            page.draw_line(pymupdf.Point(x, PH - 14), pymupdf.Point(x, PH),
                           color=RULE, width=0.4)

    for name, pan in (("1 method", a), ("2 back", b), ("3 cover", c),
                      ("4 tried", d), ("5 help", e), ("6 steps", f)):
        print("  panel %-9s ends at y=%3.0f  headroom %3.0fpt" % (name, pan.y, BOT - pan.y))

    doc.set_metadata({"title": "Bluegum Canine — Behaviour Practice",
                      "author": "Bluegum Canine",
                      "subject": "Dog training and behaviour, Co. Sligo"})
    doc.save(OUT, deflate=True, garbage=4)
    doc.close()
    print("wrote %s (%.1f KB)" % (OUT, os.path.getsize(OUT) / 1024.0))


if __name__ == "__main__":
    build()
