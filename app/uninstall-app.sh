#!/bin/bash
# shellcheck disable=SC1111
# Remove Miotła.app, its Login Item and the old launchd agent; stop the app.
set -uo pipefail

APP_NAME="Miotła"
BUNDLE_ID="com.miotla.app"

osascript -e "tell application \"$APP_NAME\" to quit" 2>/dev/null || true
pkill -if 'miotla_app' 2>/dev/null || true
osascript -e "tell application \"System Events\" to delete (every login item whose name is \"$APP_NAME\")" 2>/dev/null || true
launchctl bootout "gui/$(id -u)/$BUNDLE_ID" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/$BUNDLE_ID.plist"
rm -rf "/Applications/$APP_NAME.app" "$HOME/Applications/$APP_NAME.app"

printf '✓ Miotła uninstalled (app, Login Item, autostart). The repo stays intact.\n'
