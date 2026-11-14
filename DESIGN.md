---
name: Bike Fit Analyzer
description: Measured joint angles from a phone clip, graded green, amber or red, entirely on the rider's device.
colors:
  accent: "#2d4fe0"
  accent-ink: "#ffffff"
  accent-soft: "#edf1fe"
  ground: "#f4f5f7"
  card: "#ffffff"
  ink: "#0d1015"
  muted: "#545d6b"
  line: "#e1e4ea"
  grid: "#eceef2"
  grade-green: "#15803d"
  grade-amber: "#b45309"
  grade-red: "#d1282a"
  grade-gray: "#6b7280"
  grade-ink: "#ffffff"
  figure: "#0e131b"
  accent-dark: "#8299ff"
  accent-ink-dark: "#101114"
  accent-soft-dark: "#1f2440"
  ground-dark: "#141517"
  card-dark: "#1c1e21"
  ink-dark: "#eef0f2"
  muted-dark: "#a3a8b0"
  line-dark: "#2d3035"
  grid-dark: "#232529"
  grade-green-dark: "#3fb950"
  grade-amber-dark: "#e3a33b"
  grade-red-dark: "#f26b5b"
  grade-gray-dark: "#8d929a"
  grade-ink-dark: "#101114"
  figure-dark: "#0f1012"
typography:
  display:
    fontFamily: "Mona Sans, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
    fontSize: "clamp(2.5rem, 5.6vw, 4.4rem)"
    fontWeight: 800
    lineHeight: 0.98
    letterSpacing: "-0.035em"
    fontVariation: "\"wdth\" 118"
  headline:
    fontFamily: "Mona Sans, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
    fontSize: "clamp(1.7rem, 3.4vw, 2.6rem)"
    fontWeight: 800
    lineHeight: 1.04
    letterSpacing: "-0.03em"
    fontVariation: "\"wdth\" 118"
  numeral:
    fontFamily: "Mona Sans, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
    fontSize: "1.7rem"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.02em"
    fontFeature: "\"tnum\""
    fontVariation: "\"wdth\" 118"
  numeral-hero:
    fontFamily: "Mona Sans, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
    fontSize: "clamp(2.6rem, 5vw, 3.4rem)"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.02em"
    fontFeature: "\"tnum\""
    fontVariation: "\"wdth\" 118"
  title:
    fontFamily: "Mona Sans, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
    fontSize: "1.12rem"
    fontWeight: 700
    lineHeight: 1.3
  body:
    fontFamily: "Mona Sans, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.55
  prose:
    fontFamily: "Mona Sans, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
    fontSize: "1.06rem"
    fontWeight: 400
    lineHeight: 1.7
  label:
    fontFamily: "Mona Sans, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
    fontSize: "0.74rem"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.02em"
rounded:
  inner: "8px"
  sm: "9px"
  button: "12px"
  card: "14px"
  panel: "18px"
  pill: "999px"
spacing:
  gutter: "20px"
  container: "1160px"
  reading: "720px"
  row: "22px"
  section: "clamp(56px, 8vw, 104px)"
  tap: "44px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.accent-ink}"
    rounded: "{rounded.button}"
    padding: "0 22px"
    height: "48px"
  button-primary-hover:
    backgroundColor: "color-mix(in srgb, #2d4fe0 88%, #0d1015)"
  button-ghost:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.button}"
    padding: "0 22px"
    height: "48px"
  button-small:
    rounded: "{rounded.sm}"
    padding: "0 14px"
    height: "44px"
  segmented-switch:
    backgroundColor: "{colors.card}"
    rounded: "10px"
    padding: "2px"
  segmented-option-active:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.ground}"
    rounded: "{rounded.inner}"
    height: "44px"
  grade-pill:
    backgroundColor: "{colors.grade-green}"
    textColor: "{colors.grade-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "3px 9px"
  card:
    backgroundColor: "{colors.card}"
    rounded: "{rounded.card}"
  panel:
    backgroundColor: "{colors.card}"
    rounded: "{rounded.panel}"
    padding: "clamp(18px, 3vw, 30px)"
  band-inverted:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.ground}"
    rounded: "{rounded.panel}"
    padding: "clamp(28px, 5vw, 52px)"
---

# Design System: Bike Fit Analyzer

## Overview

**Creative North Star: "The Measured Report"**

The product's own graded report is the hero, the proof and the visual vocabulary. Every surface, from the landing page to the analyzer to the guides, reads like a page from a consumer sports-health report at Strava, Whoop or Apple Health craft: a cool near-white ground, near-black ink, hairline rules, big expanded numerals, and colour that only ever means something. It is played straight. The category standard, done carefully, is the identity.

Density is calm and list-shaped. Information sits in hairline-ruled rows and spec lists rather than in grids of boxed cards, so a page scans the way a report does: label on the left, measured value on the right. One typeface, Mona Sans, carries both voices: normal width for reading and interface text, stretched to 118% and set heavy for display lines and the numbers that matter.

The system refuses the SaaS template kit outright: no eyebrow labels over headings, no icon tiles, no chip rows, no glow gradients, no fake browser chrome, no four-column link footer. Dark theme is a faithful mirror on a graphite ground, not a separate mood.

**Key Characteristics:**
- Light base with an explicit dark theme, reachable by OS preference or the header toggle.
- Colour has two jobs: the logo blue for action, links and focus; green, amber and red for grades.
- Mona Sans variable, self-hosted: expanded heavy for display and numerals, normal width for text.
- Hairline lists over card grids; one elevated surface on the whole site.
- 44px minimum tap targets everywhere, because the rider is often mid-session beside a trainer.

## Colors

A neutral cool-grey report palette with a single brand blue and a reserved three-step grade scale.

### Primary
- **Logo Blue** (`accent`; dark `accent-dark`): the only brand colour. Primary buttons, inline links, focus rings, the dropzone outline and the analyzer progress fill. The dark variant lifts to a periwinkle so it holds contrast on graphite, and its ink (`accent-ink-dark`) flips to near-black.
- **Blue Wash** (`accent-soft`): the faint tint behind "your result" badges; never a surface fill on its own.

### Grades
- **Dialled Green** (`grade-green`), **Borderline Amber** (`grade-amber`), **Fix-It Red** (`grade-red`), **Not Graded Gray** (`grade-gray`): the four grade fills, used for grade pills, verdict dots, legend swatches and the target zone on range bars. Each has a brighter dark-theme counterpart.
- **Grade Ink** (`grade-ink`; dark `grade-ink-dark`): text on a grade fill. White in light theme, near-black in dark, because the dark grade hues are too bright to carry white text.

### Neutral
- **Cool Paper** (`ground`): page background; also the header background so the header reads as part of the page, separated only by a hairline.
- **Card White** (`card`): reports, panels, tables, segmented-switch troughs.
- **Report Ink** (`ink`): text, range-bar markers, the active segment and the inverted closing band.
- **Quiet Slate** (`muted`): secondary text, targets, captions, footer copy.
- **Hairline** (`line`): every border and list rule.
- **Grid Grey** (`grid`): inner row dividers, range-bar tracks, hover fills, inline code.
- **Camera Black** (`figure`): the sample figure's frame. It stays dark in both themes because it depicts a camera frame, not a surface.

### Named Rules
**The Two Jobs Rule.** Colour is either the brand blue (act, follow, focus) or a grade (green, amber, red, gray). Anything else is neutral. Reliability notes, view tags and "beta" markers are words and weight, never a grade hue, so a colour on this site always means a measurement.

**The Never Alone Rule.** A grade is never colour only: every pill carries a word ("dialled", "borderline", "fix it") and every number sits beside its target.

## Typography

**Display Font:** Mona Sans, variable, at `font-stretch: 118%` (with system-ui fallback)
**Body Font:** Mona Sans at normal width (with system-ui, -apple-system, Segoe UI, Roboto)
**Label/Mono Font:** ui-monospace stack, only for inline code in guides

**Character:** One family, two voices. Stretched and heavy it gives measured numbers the athletic weight of a training report; at normal width it is a plain, readable UI sans. The font is a self-hosted latin subset (weight 400 to 800, width 100 to 125), because a font CDN would contradict the privacy promise that nothing third-party loads.

### Hierarchy
- **Display** (800, clamp 2.5 to 4.4rem, 0.98, wide): the landing H1 only. Analyzer and legal H1s use the same treatment one step down (clamp 1.7 to 2.4rem and 2 to 3rem).
- **Headline** (800, clamp 1.7 to 2.6rem, 1.04, wide): section headings and the closing band.
- **Numeral** (800, 1.7rem, wide, tabular): every measured angle and target goal. **Numeral Hero** (clamp 2.6 to 3.4rem) is reserved for the knee reading, the largest number on the page.
- **Title** (700, about 1.1rem): list-row headings, FAQ questions, panel headings (800 at 1.25rem in the analyzer).
- **Body** (400, 1rem, 1.55): interface text. **Prose** (1.06rem, 1.7) inside the 720px reading column for guides and legal.
- **Label** (700, 0.72 to 0.85rem, +0.02em): pills, segmented options, field labels. Never uppercase.

### Named Rules
**The Wide Numbers Rule.** Display lines and measured numerals are set at 118% width and weight 800; everything a rider reads as sentences stays at normal width. Pills inside a numeral block reset to 100%.

**The Tabular Rule.** Every number that can be compared (values, targets, table cells, timers) uses tabular figures.

## Layout

A centred 1160px container with a 20px safe-area-aware gutter; reading pages narrow to a 720px column. Sections are separated by generous vertical space (clamp 56 to 104px) rather than by boxes. The landing hero is a two-column grid (text 0.92fr, report 1.08fr) that collapses to one column under 920px; secondary sections use a 5:7 split collapsing under 860px, and two-column spec and guide lists collapse under 760px.

Lists are the default content shape: rows of about 22px vertical padding, separated by a hairline top border, with the label left and the value right. Wide tables scroll inside their own bordered wrapper so a phone never scrolls the page sideways.

The header holds the wordmark, nav links and two segmented switches (theme, language). Under 640px nav labels hide to icons; under 520px the controls drop to a full-width second row and the GitHub link leaves the header (the footer still has it). One shared footer closes every page.

**The 44px Rule.** Every interactive control, including nav links, switch segments, footer links and FAQ summaries, has a 44px minimum hit area; primary buttons are 48px.

## Elevation & Depth

Flat by default (`--shadow: none`). Depth comes from tonal layering: card white on cool paper, separated by hairlines. There is exactly one elevated object.

### Shadow Vocabulary
- **Report lift** (`0 1px 2px rgb(13 16 21 / .05), 0 18px 40px -18px rgb(13 16 21 / .22)`; dark: `0 1px 0 rgb(255 255 255 / .04) inset, 0 24px 60px -24px rgb(0 0 0 / .75)`): the landing hero's sample report, and nothing else.

### Named Rules
**The One Lifted Report Rule.** Only the sample report floats. Every other card, panel, table and post sits flat with a hairline.

## Shapes

Soft, consistent rounding without going pillowy: 14px for cards, reports, tables and figures; 18px for analyzer panels and the inverted call-to-action band; 12px for buttons; 9px for small buttons and nav hover fills; 8px for inner segments and metric-row hover. Pills, range-bar tracks and grade dots are fully round. Borders are always 1px hairlines; the only heavier stroke is the analyzer dropzone's 2px dashed outline in a blue mix. Blockquotes use a 1px ink rule on the left, not a coloured bar.

## Components

### Buttons
Confident and plain: solid fill, bold label, no gradients.
- **Shape:** gently rounded (12px), 48px tall, 22px side padding, weight 700.
- **Primary:** logo blue fill with its ink; hover mixes 12% ink into the blue. Press nudges down 1px.
- **Ghost:** card fill, ink text, hairline border that darkens on hover.
- **Small:** 44px tall, 9px radius, 0.82rem.
- **On the inverted band:** primary flips to ground fill and ink text.
- **Focus:** a 2px blue outline offset 3px, shared by every focusable element.

### Segmented Switches
Theme (system, light, dark as icons) and language (EN, ID) in the header; Analysis/Report tabs and view selection in the analyzer use the same form.
- **Style:** card trough with a hairline border and 2 to 3px inner padding; options are transparent muted text.
- **Selected:** the option fills with ink and its text flips to the ground colour.

### Grade Pills
- **Style:** fully round, grade fill, grade ink, 0.72rem weight 700, a word inside ("dialled", "borderline", "fix it").
- Verdict dots and legend swatches use the same fills at 10 to 12px.

### Cards / Containers
- **Corner Style:** 14px (cards, tables, posts), 18px (analyzer panels).
- **Background:** card white on cool paper.
- **Shadow Strategy:** none; see the One Lifted Report Rule.
- **Border:** 1px hairline.
- **Internal Padding:** 14 to 22px for cards, clamp 18 to 30px for panels.

### Inputs / Fields
- **Style:** the bike-type select is 46px tall, card fill, hairline border, 11px radius; hover darkens the border.
- **Dropzone:** 2px dashed blue-mix outline at 16px radius over a 4% blue wash; hover or drag-over strengthens both to full blue and 9%.

### Navigation
- **Header:** wordmark (logo at 30px plus name, weight 700) left; muted 600-weight nav links right, ink on hover with a grid-grey fill, ink for the current page.
- **Footer:** one shared footer with a short about line, a single wrapping row of links, and a full-width hairline above the legal line, whose text keeps an 820px measure.

### Sample Report (signature)
The product card that leads the landing page: the figure on top in its camera-black frame, a verdict line with a grade dot, then metric rows. Each row has a name, a target, a wide numeral with its grade pill, and a range bar (grid-grey track, green target zone at 55% mix, ink marker). Focusing or hovering a row dims the other limbs on the figure to 25%. On first view the markers settle once into place (1.1s, `cubic-bezier(.16,1,.3,1)`). Both motions are off under reduced motion; the analyzer's metric cards reuse the same range bar.

### Inverted Band
An ink-filled block with ground-coloured text that closes the landing page and ends each guide: wide headline, one line, one flipped button.

## Do's and Don'ts

### Do:
- **Do** use the logo blue only for primary action, links and focus.
- **Do** keep green, amber, red and gray for grades, and pair every grade with a word.
- **Do** set display lines and measured numbers in Mona Sans at 118% width, weight 800, tabular figures.
- **Do** build content as hairline-ruled lists with the value on the right before reaching for a card.
- **Do** give every control a 44px minimum target and let header controls wrap to a second row under 520px.
- **Do** keep the sample figure dark in both themes with the figure token.
- **Do** self-host every font and asset; a CDN load breaks the privacy promise.
- **Do** switch off all animation and transitions under reduced motion.

### Don't:
- **Don't** add eyebrow labels, icon tiles, chip rows, glow gradients or fake browser chrome.
- **Don't** give any surface other than the sample report a drop shadow.
- **Don't** colour reliability notes, tags or "beta" markers with a grade hue; use words and weight.
- **Don't** use a second display face or uppercase-tracked labels.
- **Don't** add a multi-column link footer; there is one shared footer.
