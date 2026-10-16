#!/usr/bin/env bash
# Build APK cho FC Online Trợ Lý không cần Gradle.
# Cần: JDK 17+, Android SDK có "build-tools;35.0.0" và "platforms;android-34".
#   ANDROID_HOME   đường dẫn SDK (mặc định /opt/android-sdk)
#   FCO_KEYSTORE   tệp khóa ký (mặc định android/fco-release.jks; tự tạo nếu chưa có — GIỮ KỸ tệp này,
#                  mất khóa thì bản sau không cài đè được lên bản cũ)
#   FCO_KEY_PASS   mật khẩu khóa (mặc định "fcotroly")
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
WEB="$(dirname "$HERE")"
SDK="${ANDROID_HOME:-/opt/android-sdk}"
BT="$SDK/build-tools/35.0.0"
JAR="$SDK/platforms/android-34/android.jar"
KS="${FCO_KEYSTORE:-$HERE/fco-release.jks}"
PASS="${FCO_KEY_PASS:-fcotroly}"
OUT="${1:-$WEB/fc-online-tro-ly.apk}"
B="$(mktemp -d)"; trap 'rm -rf "$B"' EXIT

# Tài nguyên: biểu tượng các mật độ màn hình, tạo từ icon-512.png
python3 - "$WEB/icon-512.png" "$B/res" <<'PY'
import sys, os
from PIL import Image
src, res = sys.argv[1], sys.argv[2]
im = Image.open(src)
for d, s in {'mdpi':48,'hdpi':72,'xhdpi':96,'xxhdpi':144,'xxxhdpi':192}.items():
    os.makedirs(f'{res}/mipmap-{d}', exist_ok=True)
    im.resize((s, s), Image.LANCZOS).save(f'{res}/mipmap-{d}/ic_launcher.png')
PY

# Web app nhúng vào assets/www (không cần service worker trong APK)
mkdir -p "$B/assets/www"
cp "$WEB/index.html" "$WEB/manifest.webmanifest" "$WEB"/icon-*.png "$B/assets/www/"

"$BT/aapt2" compile --dir "$B/res" -o "$B/res.zip"
"$BT/aapt2" link -I "$JAR" --manifest "$HERE/AndroidManifest.xml" -A "$B/assets" \
  -o "$B/base.apk" "$B/res.zip" --auto-add-overlay

mkdir -p "$B/classes"
javac -encoding UTF-8 -nowarn -Xlint:-options -source 8 -target 8 -bootclasspath "$JAR" -classpath "$JAR:$BT/core-lambda-stubs.jar" \
  -d "$B/classes" $(find "$HERE/src" -name '*.java')
(cd "$B/classes" && jar cf "$B/classes.jar" .)
"$BT/d8" --release --min-api 24 --lib "$JAR" --output "$B" "$B/classes.jar"
(cd "$B" && zip -q base.apk classes.dex)

"$BT/zipalign" -f -p 4 "$B/base.apk" "$B/aligned.apk"
if [ ! -f "$KS" ]; then
  keytool -genkeypair -keystore "$KS" -alias fco -keyalg RSA -keysize 2048 -validity 10000 \
    -storepass "$PASS" -keypass "$PASS" -dname "CN=FC Online Tro Ly, O=phamnhan.click, C=VN" >/dev/null 2>&1
  echo "Đã tạo khóa ký mới: $KS"
fi
"$BT/apksigner" sign --ks "$KS" --ks-key-alias fco --ks-pass "pass:$PASS" --key-pass "pass:$PASS" --out "$OUT" "$B/aligned.apk"
"$BT/apksigner" verify "$OUT"
echo "APK: $OUT ($(du -h "$OUT" | cut -f1))"
