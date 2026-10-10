#!/bin/bash
# shellcheck disable=SC1111  # polskie cudzysłowy „” w komunikatach są celowe
# Instalacja pluginu Miotła do SwiftBar.
# Nic nie instaluje bez pytania: SwiftBara proponuje, nie wymusza.
set -uo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
SCRIPT="$ROOT/bin/miotla"
PLUGIN_SRC="$ROOT/swiftbar/miotla.10m.sh"
PLUGIN_NAME="miotla.10m.sh"
SWIFTBAR_ID="com.ameba.SwiftBar"
DEFAULT_SCRIPT="$HOME/Projects/miotla/bin/miotla"   # musi odpowiadać wartości w pluginie

say()  { printf '%s\n' "$1"; }
err()  { printf '✗ %s\n' "$1" >&2; }
ok()   { printf '✓ %s\n' "$1"; }
ask()  { local a; printf '%s (t/N): ' "$1"; IFS= read -r a || a=""; case "$a" in t|T|y|Y|tak|TAK) return 0 ;; *) return 1 ;; esac; }

[ -f "$SCRIPT" ] || { err "Brak skryptu: $SCRIPT"; exit 1; }
[ -f "$PLUGIN_SRC" ] || { err "Brak pluginu: $PLUGIN_SRC"; exit 1; }
chmod +x "$SCRIPT" "$PLUGIN_SRC" 2>/dev/null || true

# ── 1. Czy SwiftBar jest zainstalowany? ──
swiftbar_installed() {
    [ -d "/Applications/SwiftBar.app" ] && return 0
    [ -d "$HOME/Applications/SwiftBar.app" ] && return 0
    mdfind "kMDItemCFBundleIdentifier == '$SWIFTBAR_ID'" 2>/dev/null | grep -q . && return 0
    return 1
}
if ! swiftbar_installed; then
    err "Nie znaleziono SwiftBar."
    if command -v brew >/dev/null 2>&1 && ask "Zainstalować SwiftBar przez: brew install --cask swiftbar?"; then
        brew install --cask swiftbar || { err "Instalacja SwiftBar nie powiodła się."; exit 1; }
    else
        say "Zainstaluj SwiftBar: https://swiftbar.app  (lub: brew install --cask swiftbar), potem uruchom ponownie."
        exit 1
    fi
fi
ok "SwiftBar jest zainstalowany."

# ── 2. Folder wtyczek SwiftBar ──
PLUGDIR=$(defaults read "$SWIFTBAR_ID" PluginDirectory 2>/dev/null)
if [ -z "$PLUGDIR" ] || [ ! -d "$PLUGDIR" ]; then
    err "SwiftBar nie ma ustawionego folderu wtyczek."
    say "Otwórz SwiftBar → Preferences i wskaż folder na wtyczki, a potem uruchom ten skrypt ponownie."
    say "(Możesz użyć np. ~/Library/Application Support/SwiftBar/Plugins)"
    exit 1
fi
ok "Folder wtyczek: $PLUGDIR"

# ── 3. Symlink pluginu ──
DEST="$PLUGDIR/$PLUGIN_NAME"
if [ -e "$DEST" ] || [ -L "$DEST" ]; then
    if [ "$(readlink "$DEST" 2>/dev/null)" = "$PLUGIN_SRC" ]; then
        ok "Plugin już podlinkowany."
    elif ask "W $PLUGDIR istnieje już $PLUGIN_NAME — podmienić?"; then
        ln -sf "$PLUGIN_SRC" "$DEST" && ok "Plugin podmieniony."
    else
        say "Pozostawiam istniejący plik. Przerywam."
        exit 1
    fi
else
    ln -s "$PLUGIN_SRC" "$DEST" && ok "Plugin podlinkowany: $DEST"
fi

# ── 4. Ścieżka skryptu dla pluginu (gdy repo nie jest w ~/Projects/miotla) ──
if [ "$SCRIPT" != "$DEFAULT_SCRIPT" ]; then
    mkdir -p "$HOME/.config/miotla"
    printf 'SCRIPT="%s"\n' "$SCRIPT" > "$HOME/.config/miotla/config"
    ok "Zapisano ścieżkę skryptu do ~/.config/miotla/config (repo poza ~/Projects/miotla)."
fi

say ""
ok "Gotowe."
say "• Odśwież SwiftBar (menu → Refresh All) albo kliknij w ikonę Miotły."
say "• Nadaj SwiftBarowi „Pełny dostęp do dysku”: Ustawienia systemowe →"
say "  Prywatność i ochrona → Pełny dostęp do dysku → dodaj SwiftBar."
say "• Odinstalowanie: ./uninstall.sh"
