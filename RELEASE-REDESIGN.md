# Release: site redesign

**Released:** 14 November 2026 · **Live at:** https://bikefit.doniwirawan.xyz
**Commits:** `df6768a` to `2f3141d` on `main` (11 commits, 24 files in `web/`)
**Previous release:** `v1.0.0` (13 July 2026)

Every page of the site was redesigned: the landing page, the analyzer, the guides, and the privacy and terms pages. What the analyzer measures and grades is unchanged, with one exception: the hip-at-top reference was wrong and is now corrected (see [Accuracy](#accuracy)). The desktop app opens `web/app.html` directly, so it gets the redesign too.

## Highlights

- **One visual system across every page.** It lives in `web/base.css`: one typeface, one brand colour, one header, one footer.
- **Colour means something.** The logo blue marks actions, links and focus. Green, amber and red only ever mean a grade.
- **A sample report for every bike type.** The landing page and the analyzer step through six bike types: road endurance, road race, TT / triathlon, gravel, MTB, and city / hybrid. Each figure is drawn from that bike's real geometry, and every number shown is the angle the figure actually draws.
- **Easier to use on a phone.** Every control is at least 44px. The header controls wrap to a second row on small screens, and nothing scrolls sideways.
- **The privacy promise holds again.** The Ko-fi badge used to load an image from ko-fi.com on every visit. It is now a plain text link.

## Visual system

| | Before | After |
|---|---|---|
| Typeface | IBM Plex Sans + Mono, 6 files (141 KB) | Mona Sans variable, 1 file (82 KB), self-hosted |
| Display type | Plex, normal width | Mona Sans stretched wide and heavy for headlines and numbers |
| Accent | Blue, also used for labels and tints | Logo blue only, for actions, links and focus |
| Dark theme | Blue-black | Neutral graphite |
| Header | Different on each page | Identical everywhere: Analyzer, Guides, GitHub, theme, language |
| Footer | Three different layouts, one of them four columns | One shared footer |
| CSS framework | Open Props | None. Tokens are in `base.css` |

## What changed by page

### Landing (`index.html`)
- The sample report now leads the page as the product image. Each row shows the reading, a worded grade, and a range bar with the target band's edges labelled.
- The report is a carousel over six bike types. It advances every 5 seconds and holds while you hover over it or focus it. It has a pause button, stops when you pick a bike, and starts paused under reduced motion. Hovering a row lights up that limb and its angle arc on the figure.
- Removed: eyebrow labels above headings, the fake browser window, the icon card grid, the chip row, the glowing call-to-action and the four-column footer.
- "How it works" is an ordered list, and "What a good fit looks like" is a reference list with ranges. Neither is a card grid any more.

### Analyzer (`app.html`)
- Same layout and controls, restyled: a segmented Analysis / Report switch, a larger drop zone, metric cards with wide numerals, and band-edge labels on every range bar.
- The sample report uses the same six-bike carousel. Choosing a bike type jumps the sample to that bike.
- Each metric card's source tag shows whether the target comes from a research paper or a fitter's rule of thumb.
- Grade colours in the report follow the light/dark theme. The downloadable image keeps its fixed colours.
- Every element ID that the analysis script and the desktop build rely on is unchanged.

### Guides and legal pages
- These use a single reading column with a larger heading scale. Dates and read times carry small icons.
- The guides index is a plain list: no icon tiles, and the meta line sits under each title.
- How-it-works: the bike-type chip row is gone, reliability is shown in words rather than grade colours, and the callouts are neutral.
- Privacy and terms now honour `?lang=`, so a shared Indonesian link opens in Indonesian.
- On the English-only guides, the language switch's "ID" option links to the Indonesian articles listed on /blog.

## Copy

- Em dashes are gone from all user-facing text, in English and Indonesian (about 360 of them).
- Small supporting lines now carry icons that say what kind of fact they are: a camera for the view, a clock for read time, a lock for privacy, a document for a target from a paper.
- Fixed a contradiction: the home page said "Open source" in one place and "source-available" in another. It now says source-available everywhere.

## Accuracy

- **Hip at the top of the stroke.** The reference was "85–110°" with no source, and it did not fit what the tool measures (shoulder–hip–knee at top dead centre). It is now **about 55–65° on a road bike**, from Burt (2014). That is the one published recommendation that uses the same three-point angle; it is tabled in the [Holmes-method paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC9219349/) the tool already cites. The line stays informational and is never graded. This change covers the analyzer, the Python engine, the how-it-works guide, the README and `files/bikefit-research-ranges.md`.
- **Sample figures.** The old figure's angles did not match its own labels. Each new figure is solved from bike geometry and realistic body proportions, so the knee, torso and elbow angles it draws are exactly the ones quoted. The shoulder and hip values are measured off the drawing.

## Accessibility

- Text contrast meets WCAG AA (at least 4.5:1) in both themes, including text on grade pills.
- Every interactive control has at least a 44px target. Focus rings use the brand colour.
- Grades are always shown in words as well as colour.
- The carousel has a pause control, holds on hover and focus, and starts paused under `prefers-reduced-motion`.
- The drop zone works from the keyboard (Enter or Space).

## For developers

- **New files:**
  - `web/samples.js`: slide data and carousel logic, shared by both pages.
  - `web/fonts/mona-sans-latin-var.woff2` and its licence `MONA-SANS-OFL.txt`.
  - `tools/sample_figures/`: the generator that drew the six figures.
  - `PRODUCT.md`, `DESIGN.md` and `.impeccable/`: the design record.
- **Removed files:** `web/open-props.min.css` and the six IBM Plex `.woff2` files.
- **Changing a sample figure:** edit `tools/sample_figures/bikes.json`, then regenerate the SVGs and `samples.js` (see the note at the top of `integrate.py`).
- **Design rules:** `DESIGN.md` holds the tokens, the type ramp and the component rules. Read it before adding UI.

## Known issues

- The saved reports in `out_fit_vid1/` and `out_fit_vid4/` still print the old 85–110° hip reference. They are outputs from earlier runs; rerun the engine to refresh them.
- The hip reference comes from a fitter's book, not a peer-reviewed study. No study was found for this exact angle.
- A real clip has not yet been run through the restyled analyzer's results screen on the live site.

## Verification

- Every route returns 200 on production: `pwsh -File deploy.ps1 -VerifyOnly`.
- Screenshots were checked at 1440px and 390px wide, in light and dark, and the pages logged no console errors in headless Chrome.
- A separate design review returned **ship** after 8 fixes and one regression fix.
