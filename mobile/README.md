# Bike Fit Analyzer — Android

A **Trusted Web Activity** (TWA) wrapper around https://bikefit.doniwirawan.xyz/app.

## Why a TWA and not a WebView

The analyzer needs WebGPU, `getUserMedia` (the Record button) and `MediaRecorder`.
A plain `WebView` supports those poorly or not at all. A TWA runs the site in the
user's real Chrome engine, so every feature works exactly as it does on the web,
and the app is always up to date — shipping a fix to the website ships it to the
app, with no new APK.

The trade-off: it needs an internet connection, and it needs Chrome (or another
TWA-capable browser) installed. Without Chrome it falls back to a Custom Tab.

## The URL bar

The app only runs full-screen (no browser address bar) if Digital Asset Links
verify. That means:

- `web/.well-known/assetlinks.json` on the site must list the SHA-256 fingerprint
  of the certificate the APK is signed with, and
- the APK must actually be signed with that certificate.

If you re-sign with a different key (including Play App Signing), **update
assetlinks.json with the new fingerprint** or the address bar comes back.

## Build

Needs the Android SDK and a JDK (Android Studio ships one).

```sh
export JAVA_HOME="/c/Program Files/Android/Android Studio/jbr"
export ANDROID_SDK_ROOT="$LOCALAPPDATA/Android/Sdk"
gradle --no-daemon assembleRelease
# -> app/build/outputs/apk/release/app-release.apk
```

Signing values come from env vars, falling back to the local `keystore.jks`:
`BIKEFIT_KEYSTORE`, `BIKEFIT_STORE_PASS`, `BIKEFIT_KEY_ALIAS`, `BIKEFIT_KEY_PASS`.

## The keystore

`mobile/keystore.jks` is **gitignored and must stay that way**. It is the only key
that can sign an update to this app — if it is lost, existing installs can never
be updated, and the fingerprint in `assetlinks.json` becomes wrong. Back it up
somewhere safe.

Current fingerprint (matches `assetlinks.json`):
`FC:D3:8F:CC:9E:29:A3:B7:64:7E:FA:3F:95:58:9D:89:03:8C:C2:AB:A4:69:C6:5A:44:D2:14:7C:A2:CD:8A:34`

## Play Store

Not published. If you do publish, Google re-signs with its own key (Play App
Signing) — take the fingerprint Play shows you and add it to `assetlinks.json`
alongside this one.
