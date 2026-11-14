# Fonts

Mona Sans (GitHub), one variable woff2: `mona-sans-latin-var.woff2`.

Self-hosted deliberately. A Google Fonts (or any CDN) `<link>` would make every page load
fetch from a third party, which contradicts what `/privacy` promises (see the "Links out"
section there). This file is served from this domain and nothing else is requested.

Licence: SIL Open Font License 1.1, copy in `MONA-SANS-OFL.txt`.
Source: `fonts/webfonts/variable/MonaSansVF[wdth,opsz,wght].woff2` from github/mona-sans v2.0.27.

How it was cut down (308 KB to 84 KB), with fonttools:

    fonttools varLib.instancer MonaSansVF[wdth,opsz,wght].woff2 wght=400:800 wdth=100:125 opsz=drop
    pyftsubset <that> --unicodes=<Basic Latin, Latin-1, general punctuation, ° ± × − arrows>
      --layout-features=kern,liga,calt,tnum,lnum,case,ss01,ss02,ss03 --flavor=woff2

`base.css` declares it once with `font-weight:400 800` and `font-stretch:100% 125%`; the wide,
heavy display type is the same file at `font-stretch:118%`.
