#!/bin/bash
# Odinstalowanie pluginu Miotła ze SwiftBar. Nie rusza samego SwiftBara.
set -uo pipefail

PLUGIN_NAME="miotla.10m.sh"
SWIFTBAR_ID="com.ameba.SwiftBar"
CACHE="$HOME/Library/Caches/miotla"
LOGS="$HOME/Library/Logs/miotla"

say() { printf '%s\n' "$1"; }
ok()  { printf '✓ %s\n' "$1"; }
ask() { local a; printf '%s (t/N): ' "$1"; IFS= read -r a || a=""; case "$a" in t|T|y|Y|tak|TAK) return 0 ;; *) return 1 ;; esac; }

PLUGDIR=$(defaults read "$SWIFTBAR_ID" PluginDirectory 2>/dev/null)
removed=0
if [ -n "$PLUGDIR" ] && [ -e "$PLUGDIR/$PLUGIN_NAME" ]; then
    rm -f "$PLUGDIR/$PLUGIN_NAME" && { ok "Usunięto plugin z $PLUGDIR"; removed=1; }
fi
[ "$removed" -eq 0 ] && say "Nie znaleziono podlinkowanego pluginu (nic do usunięcia)."

if [ -d "$CACHE" ] || [ -d "$LOGS" ]; then
    if ask "Usunąć też stan i logi Miotły ($CACHE, $LOGS)?"; then
        rm -rf "$CACHE" "$LOGS" && ok "Usunięto stan i logi."
    else
        say "Pozostawiam stan i logi."
    fi
fi

say "Odśwież SwiftBar (menu → Refresh All), żeby ikona zniknęła."
