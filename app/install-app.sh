#!/bin/bash
# shellcheck disable=SC1111
# Build and install "Miotła.app" so it is launchable from the Dock, Launchpad,
# Spotlight and /Applications. Registers a Login Item (autostart + single
# instance) and removes the old launchd agent.
set -uo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)                 # .../miotla/app
PKG="$ROOT/miotla_app"
ICON_SRC="$PKG/assets/app_icon.png"
APP_NAME="Miotła"
BUNDLE_ID="com.miotla.app"
VERSION="0.1.0"

say() { printf '%s\n' "$1"; }
ok()  { printf '✓ %s\n' "$1"; }
err() { printf '✗ %s\n' "$1" >&2; }

[ -f "$ICON_SRC" ] || { err "Missing icon: $ICON_SRC"; exit 1; }

# Where to install (prefer /Applications, else ~/Applications)
if [ -w /Applications ]; then DEST="/Applications"; else DEST="$HOME/Applications"; mkdir -p "$DEST"; fi
APP="$DEST/$APP_NAME.app"

# --- stop and remove the old launchd autostart (avoids a second instance) ---
launchctl bootout "gui/$(id -u)/$BUNDLE_ID" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/$BUNDLE_ID.plist"
pkill -if 'miotla_app' 2>/dev/null || true

# --- build the .app skeleton ---
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

# icns from the PNG
TMP=$(mktemp -d)
ICONSET="$TMP/miotla.iconset"; mkdir -p "$ICONSET"
for s in 16 32 128 256 512; do
    sips -z "$s" "$s"           "$ICON_SRC" --out "$ICONSET/icon_${s}x${s}.png"      >/dev/null 2>&1
    sips -z "$((s*2))" "$((s*2))" "$ICON_SRC" --out "$ICONSET/icon_${s}x${s}@2x.png" >/dev/null 2>&1
done
iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/miotla.icns" 2>/dev/null \
    || cp "$ICON_SRC" "$APP/Contents/Resources/miotla.icns"
rm -rf "$TMP"

# Info.plist (regular app → shows in Dock / Launchpad / Spotlight)
cat > "$APP/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>$APP_NAME</string>
    <key>CFBundleDisplayName</key><string>$APP_NAME</string>
    <key>CFBundleIdentifier</key><string>$BUNDLE_ID</string>
    <key>CFBundleExecutable</key><string>miotla</string>
    <key>CFBundleIconFile</key><string>miotla</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleVersion</key><string>$VERSION</string>
    <key>CFBundleShortVersionString</key><string>$VERSION</string>
    <key>LSMinimumSystemVersion</key><string>11.0</string>
    <key>NSHighResolutionCapable</key><true/>
    <key>LSMultipleInstancesProhibited</key><true/>
</dict>
</plist>
EOF

# Launcher: runs the Python app from this repo's venv (creates it on first run)
cat > "$APP/Contents/MacOS/miotla" <<EOF
#!/bin/zsh
ROOT="$ROOT"
VENV="\$ROOT/.venv"
PY="/Library/Frameworks/Python.framework/Versions/3.10/bin/python3"
[[ -x "\$PY" ]] || PY="\$(command -v python3)"
if [[ ! -d "\$VENV" ]]; then
  "\$PY" -m venv "\$VENV"
  "\$VENV/bin/pip" install -q --upgrade pip
  "\$VENV/bin/pip" install -q -r "\$ROOT/requirements.txt"
fi
export PYTHONPATH="\$ROOT"
exec "\$VENV/bin/python" -m miotla_app
EOF
chmod +x "$APP/Contents/MacOS/miotla"
# Refresh Launch Services / Dock so the icon and name appear immediately
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister \
    -f "$APP" 2>/dev/null || true
touch "$APP"
ok "Built $APP"

# --- autostart via Login Item (launches through LaunchServices → one instance) ---
osascript -e "tell application \"System Events\" to delete (every login item whose name is \"$APP_NAME\")" 2>/dev/null || true
if osascript -e "tell application \"System Events\" to make login item at end with properties {path:\"$APP\", hidden:false}" >/dev/null 2>&1; then
    ok "Added Login Item (starts on login)"
else
    say "Could not add Login Item automatically — add $APP in System Settings → General → Login Items."
fi

# --- launch now ---
open "$APP" && ok "Launched $APP_NAME"

say ""
ok "Done. You can now launch Miotła from the Dock, Launchpad, Spotlight or $DEST."
say "• Grant Full Disk Access (System Settings → Privacy & Security) so it sees the Trash and app caches."
say "• Uninstall: ./uninstall-app.sh"
