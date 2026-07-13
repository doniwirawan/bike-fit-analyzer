# Bike Fit Analyzer — native Android app

A real Android app, not a wrapper. MediaPipe runs on-device, the pose model is bundled in the
APK, and the analysis runs in a foreground worker so it keeps going when you leave the app.

The app has **no INTERNET permission**. It cannot upload your video even if it wanted to.

## Why native (what the TWA in ../ could not do)

- **Background processing.** A browser tab is throttled or killed when backgrounded. A
  `CoroutineWorker` in a foreground service is not — verified on an emulator: analysis ran to
  completion with the launcher in front and the app closed.
- **A notification when it's done.** You get "Your bike fit is ready · knee 21° · 5 strokes"
  instead of having to sit and watch a progress bar.
- **Offline.** The 9MB pose model ships inside the APK (this is why it's ~35MB, vs 449KB for
  the TWA, which downloads the model from a CDN every time).

## It agrees with the website

Both run MediaPipe with the same zones, so they should — and on the same clip they do:

| angle | web | native |
|---|---|---|
| knee at bottom | 20° RED | 21° RED |
| torso | 42° GREEN | 42° GREEN |
| elbow | 20° GREEN | 20° GREEN |
| shoulder | 81° GREEN | 82° GREEN |
| strokes | 6 | 5 |

All four grades match. The stroke count differs because the app samples ~15fps while the web app
walks every frame; the angles are medians across the strokes it does find, so this doesn't move
them meaningfully.

**`FitLogic.kt` is a port of the grading rules in `web/app.html`.** If you change the zones,
the BDC detection, the median, or the advice in one place, change it in the other, or the phone
and the website will give the same rider different verdicts.

## Build

```sh
export JAVA_HOME="/c/Program Files/Android/Android Studio/jbr"
export ANDROID_SDK_ROOT="$LOCALAPPDATA/Android/Sdk"
gradle --no-daemon assembleRelease
```

## Gotchas found the hard way

- **ABI:** MediaPipe 0.10.14 ships no `x86_64` `.so`. Leave x86_64 in the APK and it dies on
  x86_64 devices (emulators) with `UnsatisfiedLinkError`. `abiFilters` is restricted to
  `arm64-v8a` and `armeabi-v7a` for that reason.
- **Foreground service type:** WorkManager's `SystemForegroundService` must be declared with
  `foregroundServiceType="dataSync"` in the manifest, or Android 14+ refuses to start it and the
  background analysis dies the moment you leave the app.
- **URI grants:** the file picker's URI grant does not survive into a background worker. The
  video is copied into app storage first (`Staging.kt`).
- **Frame sampling:** `OPTION_CLOSEST_SYNC` only returns keyframes, which can be seconds apart —
  the ankle signal goes flat and most pedal strokes are never found. Use `OPTION_CLOSEST`.

## Not done yet

In-app camera recording (front/back). Right now you pick a clip, or share one into the app.
