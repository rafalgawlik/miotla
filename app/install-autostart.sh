#!/bin/bash
# Autostart apki Miotła po zalogowaniu (LaunchAgent).
# Tworzy ~/Library/LaunchAgents/com.miotla.app.plist wskazujący na run.sh
# tego repo, zatrzymuje ewentualną starą instancję i ładuje agenta.
set -uo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
LABEL="com.miotla.app"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOGDIR="$HOME/Library/Logs/miotla"
RUN="$ROOT/run.sh"

[ -f "$RUN" ] || { printf 'Brak %s\n' "$RUN" >&2; exit 1; }
mkdir -p "$HOME/Library/LaunchAgents" "$LOGDIR"

# Zatrzymaj starą instancję (zarządzaną i ręczną), żeby nie było dubla.
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
pkill -if 'miotla_app' 2>/dev/null || true   # -i: proces to Python (wielka litera)

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/zsh</string>
        <string>$RUN</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>StandardOutPath</key>
    <string>$LOGDIR/app.out.log</string>
    <key>StandardErrorPath</key>
    <string>$LOGDIR/app.err.log</string>
</dict>
</plist>
EOF

# Załaduj (nowe API z fallbackiem na starsze).
if launchctl bootstrap "gui/$(id -u)" "$PLIST" 2>/dev/null; then :; else
    launchctl load -w "$PLIST"
fi
launchctl enable "gui/$(id -u)/$LABEL" 2>/dev/null || true

printf '✓ Autostart włączony: %s\n' "$PLIST"
printf '  Apka wstaje po zalogowaniu i uruchomiła się teraz.\n'
printf '  Wyłączenie autostartu: ./uninstall-autostart.sh\n'
