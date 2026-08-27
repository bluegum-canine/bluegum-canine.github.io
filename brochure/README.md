# Brochure

Six-panel A4 landscape tri-fold, two pages. Page 1 is the outside — method
flap, back cover, front cover. Page 2 is the inside. Fold twice.

    python3 brochure/build_brochure.py

Needs `pymupdf`, `fonttools`, `brotli` and `pillow`.

## Why the generator lives here

The previous brochure generator was written in a scratch directory. That
directory was cleaned, and the only surviving artefacts were PDFs nobody
could edit — which is why the old brochures still said MARK RABEL, "forty
years" and the retired strapline months after the website had moved on.
Anything that produces a deliverable belongs in the repo.

## Things the script handles that are easy to get wrong

- **Fonts.** The site's faces are woff2, which a PDF cannot embed, so they
  are converted at build time. Fraunces is variable and is pinned to a
  static instance — embed the variable font and the PDF renders it at its
  default weight, not the one the site uses.
- **Overflow.** Every text and image block checks the panel's remaining
  height and raises rather than silently clipping. The build prints the
  headroom left in each of the six panels.
- **Letter-spaced labels.** Spacing is faked by inserting spaces between
  characters, which makes long labels wide enough to wrap mid-word. They
  are measured and shrunk to fit on one line instead.
- **Photographs** are centre-cropped to the target aspect, never stretched.
  Watch which image goes in a wide slot: a picture with a face near the top
  and another near the bottom loses both.
- **Colour.** Uses the site's contrast-corrected palette — #8A4E20 for
  accent text on paper, not the decorative #A8642C, which measures under
  4:1 against this background.
