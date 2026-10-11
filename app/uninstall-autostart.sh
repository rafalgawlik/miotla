#!/bin/bash
# Wyłącz autostart apki Miotła i zatrzymaj ją.
set -uo pipefail

LABEL="com.miotla.app"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
[ -f "$PLIST" ] && rm -f "$PLIST" && printf '✓ Usunięto %s\n' "$PLIST"
pkill -if 'miotla_app' 2>/dev/null || true   # -i: proces to Python (wielka litera)
printf '✓ Autostart wyłączony, apka zatrzymana.\n'
