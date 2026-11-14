# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Home cyclists, English and Indonesian speaking, who want to check their saddle height and overall fit from a phone clip before they change parts or pay a fitter. They ride road, gravel, MTB, TT/triathlon, hybrid, commuter or e-bikes, and usually film on a turbo trainer at home.

## Product Purpose

Bike Fit Analyzer turns 20 to 30 seconds of pedaling video into measured joint angles (knee at the bottom of the stroke, torso, elbow, shoulder/reach; plus knee tracking, hip rock and symmetry from front and rear views) graded green, amber or red against bike-fitting ranges for the chosen bike type, with plain-language advice on what to change. Success is a rider catching an obviously wrong saddle height, and knowing what to ask a fitter, without spending anything.

## Positioning

Free, runs entirely on the rider's own device (the video is never uploaded, no account), and openly honest about the limits of 2D measurement: it says knee is the most reliable reading and reach the least, and that it does not replace a professional 3D fit.

## Operating Context

- Rider films themselves side-on at hip height (or front/rear), on a trainer, then drops or records the clip in the browser.
- Web app at bikefit.doniwirawan.xyz (static, Vercel). Pose detection is MediaPipe Pose in the browser (WebGPU, WASM fallback).
- The same `web/app.html` is the UI of the Windows desktop app (pywebview, YOLO11x-pose). An Android APK is also offered.
- English guides live under `/blog`; Indonesian articles live on doniwirawan.xyz and are linked, not copied.

## Capabilities and Constraints

- Views: side (graded), front and rear (beta, report-only soft flags).
- Saved results and before/after comparison.
- Bilingual EN/ID on one page via a JS toggle with `?lang=` URLs; Indonesian copy must be informal and natural (kamu, pakai), never literal translation.
- Light and dark themes with a toggle.
- Privacy promise (privacy.html): no cookies, no accounts, no third-party loads on a normal visit beyond Vercel's cookieless analytics. Any embed must be click-to-load; fonts and assets are self-hosted.
- Reach/shoulder advice must stay soft and advisory; never a confident "shorten your stem". Saddle height is the trustworthy number.
- JS DOM hooks in app.html must survive any restyle.

## Brand Commitments

- Name: Bike Fit Analyzer. Logo: `web/logo.png` / `logo-64.png`.
- Grades are always green / amber / red.
- Source-available (published on GitHub), not open source: free to read and use, not to build a competing product.
- Maker: Doni Wirawan (Strava, Threads, Ko-fi). Sister project: Ascent Analytics.

## Evidence on Hand

- One real rider post: @paceandpedal_ on Threads (ran a first clip, then raised their saddle). The maker's launch post on Threads.
- Targets: knee and elbow from published research (Holmes method); torso and shoulder are a fitter's rule of thumb. Sources in `files/bikefit-research-ranges.md`.
- No user counts, no accuracy benchmarks, no other testimonials. Front/rear thresholds are validated only against literature and synthetic scenarios, never real footage. Do not fabricate any of these.

## Product Principles

1. Honesty over persuasion: state what 2D video cannot measure as plainly as what it can.
2. Privacy is the product: nothing leaves the device, and the site itself must not contradict that.
3. Saddle height first: the most reliable number leads; soft metrics stay soft.
4. Respect the rider's money: steer toward free adjustments before parts or paid fits.
5. Two languages, both first-class.

## Accessibility & Inclusion

Used on phones next to a trainer, often mid-session: large tap targets, readable at arm's length, WCAG AA contrast in both themes, grades never conveyed by color alone.
