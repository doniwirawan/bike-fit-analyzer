# Fonts

IBM Plex Sans and IBM Plex Mono, latin subsets, woff2 only.

Self-hosted deliberately. A Google Fonts (or any CDN) `<link>` would make every page load
fetch from a third party, which contradicts what `/privacy` promises — see the "Links out"
section there. These files are served from this domain and nothing else is requested.

Licence: SIL Open Font License 1.1 — https://github.com/IBM/plex/blob/master/LICENSE.txt
Source: the @fontsource/ibm-plex-sans and @fontsource/ibm-plex-mono packages.

Weights: 400, 600, 700. There is no 800; base.css maps `font-weight:700 800` onto the 700
file so the extrabold headings synthesise from it rather than from a faux-bold of 400.
