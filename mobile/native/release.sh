#!/usr/bin/env bash
# Release the native Android app.
#
#   1. bump versionCode and versionName in app/build.gradle
#   2. write what changed in release-notes.json (en + id)
#   3. ./release.sh            then commit and push, which deploys the site
#
# It builds the signed APK, checks it is signed with the release key (so it installs over the
# old version and keeps people's saved results), copies it to web/bikefit-native.apk, writes
# web/android.json (what /android and the in-app "Check for updates" compare against), and
# creates the GitHub release android-v<versionName> with the APK attached.
#
# Signing credentials: from the environment, else from mobile/signing.env (gitignored).
set -euo pipefail
cd "$(dirname "$0")"
ROOT=$(cd ../.. && { pwd -W 2>/dev/null || pwd; })  # a path Windows Python can open

# The release key's certificate. Same value as web/.well-known/assetlinks.json.
CERT="fcd38fcc9e29a3b7647efa3f95589d89038cc2aba469c65a44d2147ca2cd8a34"

die() { echo "release: $*" >&2; exit 1; }

[ -f ../signing.env ] && { set -a; . ../signing.env; set +a; }
for v in BIKEFIT_STORE_PASS BIKEFIT_KEY_ALIAS BIKEFIT_KEY_PASS; do
  [ -n "${!v:-}" ] || die "$v is not set (environment or mobile/signing.env)"
done

CODE=$(sed -nE 's/^\s*versionCode ([0-9]+).*/\1/p' app/build.gradle)
NAME=$(sed -nE 's/^\s*versionName "([^"]+)".*/\1/p' app/build.gradle)
LIVE=$(python -c "import json;print(json.load(open('$ROOT/web/android.json'))['versionCode'])")
[ "$CODE" -gt "$LIVE" ] || die "versionCode $CODE is not above the published $LIVE. Bump it in app/build.gradle."
python -c "import json;n=json.load(open('release-notes.json'));assert n['en'] and n['id']" \
  || die "release-notes.json needs en and id notes"
git -C "$ROOT" rev-parse -q --verify "refs/tags/android-v$NAME" >/dev/null \
  && die "tag android-v$NAME already exists"

export JAVA_HOME="${JAVA_HOME:-/c/Program Files/Android/Android Studio/jbr}"
export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$LOCALAPPDATA/Android/Sdk}"
GRADLE=$(command -v gradle || ls "$HOME"/.gradle/wrapper/dists/gradle-8.9-all/*/gradle-8.9/bin/gradle | head -1)
# the jar, not apksigner.bat: the .bat can't read a Git Bash style JAVA_HOME
APKSIGNER_JAR=$(ls "$ANDROID_SDK_ROOT"/build-tools/*/lib/apksigner.jar | sort -V | tail -1)

echo "release: building $NAME ($CODE)"
"$GRADLE" --no-daemon -q assembleRelease
APK=app/build/outputs/apk/release/app-release.apk
[ -f "$APK" ] || die "no APK at $APK"

"$JAVA_HOME/bin/java" -jar "$APKSIGNER_JAR" verify --print-certs "$APK" | tr 'A-Z' 'a-z' | grep -q "sha-256 digest: $CERT" \
  || die "APK is not signed with the release key; it would not install over the old version"

cp "$APK" "$ROOT/web/bikefit-native.apk"
cp "$APK" bikefit-native.apk

python - "$ROOT/web/android.json" "$CODE" "$NAME" "$ROOT/web/bikefit-native.apk" <<'PY'
import json, os, sys, datetime
out, code, name, apk = sys.argv[1:]
notes = json.load(open('release-notes.json', encoding='utf-8'))
rel = {"versionCode": int(code), "versionName": name, "date": datetime.date.today().isoformat(),
       "sizeMB": round(os.path.getsize(apk) / 1e6), "apk": "/bikefit-native.apk", "notes": notes}
with open(out, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(rel, f, ensure_ascii=False, indent=2); f.write('\n')
PY

# Push first: Vercel deploys main, and the tag should point at the commit that ships this APK.
git -C "$ROOT" add web/android.json web/bikefit-native.apk mobile/native/bikefit-native.apk \
  mobile/native/app/build.gradle mobile/native/release-notes.json
git -C "$ROOT" commit -q -m "Android app $NAME"
git -C "$ROOT" push -q

NOTES=$(python -c "import json;print('\n'.join('- '+n for n in json.load(open('release-notes.json',encoding='utf-8'))['en']))")
cp "$APK" "bikefit-android-$NAME.apk"
gh release create "android-v$NAME" "bikefit-android-$NAME.apk" \
  --target "$(git -C "$ROOT" rev-parse HEAD)" \
  --title "Android app $NAME" \
  --notes "$NOTES

Install over the previous version to keep your saved results. Download page: https://bikefit.doniwirawan.xyz/android"
rm "bikefit-android-$NAME.apk"

echo "release: $NAME is out. Live at https://bikefit.doniwirawan.xyz/android once Vercel finishes deploying."
