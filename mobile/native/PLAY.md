# Publishing to Google Play

## Where this actually stands (20 Jul 2026)

The app exists in the Play Console: **Bike Fit Analyzer**, app ID `4973349918422560877`,
package `xyz.doniwirawan.bikefit`, on the "Doni Wirawan" personal account.

Done:
- App created, package name locked, Free, en-US
- Store listing saved as draft: name, short description, full description, app icon,
  feature graphic, 2 phone screenshots (real 9:16 captures from a live analysis)

Still to do, and why:
- **Upload the AAB.** Has to be dragged into the console by hand — browser automation
  caps file transfers at 10 MB and the bundle is 27 MB. The alternative is the Play
  Developer Publishing API with a service account (fastlane supply / gradle-play-publisher).
- **App content declarations**: privacy policy URL, Data safety, content rating, target
  audience, ads. Answers are below.
- **7-inch tablet screenshots** — the listing marks these required.
- **12 testers, 14 days.** This is a personal developer account, so production access needs
  a published closed test with at least 12 opted-in testers running 14 continuous days.
  "Apply for production" stays greyed out until then. This is the long pole, not the paperwork.

## The artifact

```
app/build/outputs/bundle/release/app-release.aab     ~27 MB
```

| field | value |
|---|---|
| package name | `xyz.doniwirawan.bikefit` |
| versionCode / versionName | `1` / `1.0` |
| targetSdk | 35 — meets Play's current requirement |
| ABIs | `arm64-v8a`, `armeabi-v7a` (see the ABI gotcha in README) |

The package name is permanent once the first release is published. It is the same applicationId the
TWA in `../app` uses — the TWA is no longer linked from the site, so the native app took the clean
name. Anyone still running a sideloaded TWA build will have to uninstall it before the Play version
installs, because the signing keys differ.

**Play App Signing is safe for this app.** Google re-signs with its own key, which for the TWA in
`../` would break the `assetlinks.json` fingerprint. This app is not a TWA and has no asset links,
so the re-signing costs nothing here. Keep `keystore.jks` regardless: it is the *upload* key, and
without it no future update can be uploaded.

## Data safety form

The honest answers are unusually short, because the app has no `INTERNET` permission:

- **Does your app collect or share any of the required user data types?** → **No.**
- **Data encrypted in transit / deletion request mechanism** → not applicable, nothing is transmitted.
- Camera: declared as a *permission*, but not as data collection — the video is processed on-device
  and never leaves the phone. Play's form asks about collection (sent off device), not access.

Play may flag the camera permission and ask what it is for. The answer: recording the rider's own
clip for on-device analysis; the clip is written only to app-private storage.

## Store listing

**Title (≤30):** `Bike Fit Analyzer`

**Short description (≤80):**
`Film your pedal stroke, get your saddle height and reach measured — all on your phone.`

**Full description (≤4000):**

```
Bike Fit Analyzer measures your riding position from a short video of yourself pedalling.
Put the phone beside the bike, record 10-30 seconds, and it reports four angles that decide
whether your bike fits you:

• Knee angle at the bottom of the stroke — saddle height
• Torso angle from horizontal — how stretched out you are
• Elbow bend — how much shock your arms can absorb
• Shoulder angle — reach

Each is graded against the range for your bike type: road, endurance, TT, gravel or MTB.
You get a plain-language "do this" list, and you can save results and compare a before and
after when you change something.

Nothing is uploaded. The app has no internet permission at all — it physically cannot send
your video anywhere. The pose model is bundled in the app, so it works with no connection.

This is a 2D side-view estimate, not a professional bike fit, and not medical advice.
Saddle height is the most reliable number it gives you; reach is the softest.
```

**Category:** Health & Fitness · **Content rating:** Everyone · **Ads:** none · **In-app purchases:** none

**Privacy policy URL:** `https://bikefit.doniwirawan.xyz/privacy`
(the "The Android app" section there was written for this submission — deploy the site before
submitting, or the reviewer hits a policy that doesn't mention the app)

## Graphics you still need to make

Play will not accept the listing without these, and they are not in the repo:

- App icon, 512×512 PNG (32-bit, no alpha) — `mobile/native/app/src/main/res/mipmap-*/ic_launcher.png` is the source
- Feature graphic, 1024×500 PNG/JPG, no alpha
- At least 2 phone screenshots, 16:9 or 9:16, min 320px on the short side

Screenshots worth taking: the result card with a RED knee and the "do this" list, the
before/after compare view, and the recorder with a bike framed in it.

## Submission order

1. Deploy the site first — `cd web && vercel deploy --prod` — so the privacy URL is live.
2. Play Console → Create app → fill the listing above.
3. Upload the AAB to **Internal testing** first, install it from the test link, confirm the
   analysis runs end to end on a real phone. The emulator ABI trap in README makes this worth doing.
4. Complete Data safety, Content rating, Ads declaration, and Target audience.
5. Promote to Production. First review typically takes a few days.
