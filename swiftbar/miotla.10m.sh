#!/bin/bash
# <xbar.title>Miotła</xbar.title>
# <xbar.version>1.0</xbar.version>
# <xbar.author>Rafał Gawlik</xbar.author>
# <xbar.desc>Wolne miejsce na dysku + bezpieczne sprzątanie Maca dewelopera jednym kliknięciem.</xbar.desc>
# <xbar.dependencies>bash</xbar.dependencies>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideDisablePlugin>false</swiftbar.hideDisablePlugin>
#
# Miotła — plugin paska menu. Odświeżanie co 10 min (nazwa pliku: .10m.).
# Jest TANIE: tylko `df` i plik stanu, żadnego `du`.

# ════════════════════════════════════════════════════════════
#  KONFIGURACJA — wszystko w jednym miejscu
# ════════════════════════════════════════════════════════════
SCRIPT="$HOME/Projects/miotla/bin/miotla"   # ścieżka do skryptu miotla
RED_GB=20                                    # poniżej → czerwony
ORANGE_GB=40                                 # poniżej → pomarańczowy
VOLUME="/System/Volumes/Data"                # wolumen danych
# Opcjonalne nadpisanie powyższych w ~/.config/miotla/config (key=value w bashu)
# shellcheck source=/dev/null
[ -f "$HOME/.config/miotla/config" ] && . "$HOME/.config/miotla/config"

CACHE="$HOME/Library/Caches/miotla"
LOGS="$HOME/Library/Logs/miotla"
STATE="$CACHE/state"
NOTIFY_STATE="$CACHE/notify"                 # dedupe powiadomienia o małym miejscu
LOCK="$CACHE/lock"

# Ikona miotły jako templateImage (czerń + alfa — macOS zabarwia pod pasek).
# Statyczna (bezczynność) oraz klatki „zamiatania” (animacja w trakcie sprzątania).
ICON="iVBORw0KGgoAAAANSUhEUgAAACQAAAAkCAYAAADhAJiYAAAACXBIWXMAABYlAAAWJQFJUiTwAAACg0lEQVR4nM2YO2gVQRSGv9nNNWi0ECQqgkYsVDAiKXySVBHSGBB8VDYWUVAEsdEuNhYiCCIB8dWIpUIqi1iIRtAUGhvxUYgoPhG5qBhNsjLwjx5GCyG7c++BZWYfd/fb/z9zduZCYyIDHE0SjiYKp3Yx0BYdSx652qXAJ2AcaBWQs16mCAcUQA24DMwHXgPTiZ7/F0yL+lcEdtUok9yymtqTghn5l1WpYQ4J5pHsSpkuvyPYtFMwr4AVUYInh+kGJoA6sDE6lyxytauB9xpJ2xoFk6ldCDyVVfujfEoKk6kC3xHMYCqYTNaEYevM/nXBXDA2JR3emcmNs4IZjiArfbiPzXr4bP7EUcGMyTaXotZkUuOGHn4LWADs0f4LYIm5NgkMsuKuIJ4DX4G3wNpUhS83/TXAOQH8FJTfDut8a9UgTv1lwBDww0D4bUqbL4Lbq7IrjJDQP6JJVQCYUAUOUFapg2VDWXu6Ta4UAonV8e0DYDfwBhgoC8iqMhc4Y1SwCviRdVzngn2n9bt2Koh+4EmkRAGMAjt0zYCOBaAuo0gpyvibLAcuRhDfpYj/Jq0HOoBZwENzzbhJ/hnDtOgmXv5VwF4d9yA3Vej8XOYD0Ac8Az4CncqfXN+sKd1rsgx1MFBbgGPAY83u6oLxufENuA30APukzmepVjcrixlFkHhabzuqWrJJ1fcLsEEK+II3TyMvvMwlweRlwFggjAUerhd4CewC7gHrgHfASuVasHWoLGX+x8ZFqi0e9ARwLUp6v8ZKNmEPUHNk4X3gvEZUoeTtTDXFiKF8HABOyc5JzQobspxxZj7cp5FWKOltZU8eNbVblUdN8T9PZvoNhwkRljqVxS8xTqSDRZ/UUQAAAABJRU5ErkJggg=="
SWEEP=(
  "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"
)

# ════════════════════════════════════════════════════════════
#  POMOCNICZE
# ════════════════════════════════════════════════════════════
human() { awk -v m="$1" 'BEGIN { if (m + 0 >= 1024) printf "%.1f GB", m / 1024; else printf "%d MB", m + 0 }'; }
human0() { awk -v m="$1" 'BEGIN { if (m + 0 >= 1024) printf "%.0f GB", m / 1024; else printf "%d MB", m + 0 }'; }
state_val() { awk -F= -v k="$1" '$1 == k { sub(/^[^=]*=/, ""); print; exit }' "$STATE" 2>/dev/null; }

# ── wolne / zajęte (tanio: df) ──
read -r free_mb used_mb <<EOF
$(df -m "$VOLUME" 2>/dev/null | awk 'NR == 2 { print $4, $3 }')
EOF
free_mb=${free_mb:-0}
used_mb=${used_mb:-0}

# ── kolor wg progu ──
COLOR=""
if   [ "$free_mb" -lt $((RED_GB * 1024)) ];    then COLOR="red"
elif [ "$free_mb" -lt $((ORANGE_GB * 1024)) ]; then COLOR="orange"
fi

# ── powiadomienie o małym miejscu (jedno, bez spamu) ──
level="ok"; [ "$free_mb" -lt $((RED_GB * 1024)) ] && level="low"
prev=$(cat "$NOTIFY_STATE" 2>/dev/null)
if [ "$level" != "$prev" ]; then
    if [ "$level" = "low" ]; then
        osascript -e "display notification \"Zostało $(human0 "$free_mb") — czas na sprzątanie.\" with title \"Miotła\"" >/dev/null 2>&1
    fi
    mkdir -p "$CACHE" 2>/dev/null
    echo "$level" > "$NOTIFY_STATE"
fi

# ════════════════════════════════════════════════════════════
#  PASEK MENU
# ════════════════════════════════════════════════════════════
if [ -d "$LOCK" ]; then
    # Trwa sprzątanie — animacja „zamiatania”: kolejna klatka z licznika.
    # Licznik posuwa `miotla --auto`, które w trakcie odświeża plugin.
    n=${#SWEEP[@]}
    idx=$(cat "$CACHE/anim" 2>/dev/null); case "$idx" in ''|*[!0-9]*) idx=0 ;; esac
    mkdir -p "$CACHE" 2>/dev/null; echo $(((idx + 1) % n)) > "$CACHE/anim"
    echo "sprzątanie… | templateImage=${SWEEP[$((idx % n))]}"
else
    printf '%s | templateImage=%s%s\n' "$(human0 "$free_mb")" "$ICON" "${COLOR:+ color=$COLOR}"
fi

echo "---"
printf 'Wolne: %s' "$(human "$free_mb")"; [ -n "$COLOR" ] && printf ' | color=%s' "$COLOR"; echo
echo "Zajęte: $(human "$used_mb")"
echo "---"

if [ -x "$SCRIPT" ]; then
    echo "Szybkie sprzątanie | bash=\"$SCRIPT\" param0=--auto param1=--animate terminal=false refresh=true"
    echo "Podgląd (dry-run) w Terminalu | bash=\"$SCRIPT\" param0=--auto param1=--dry-run terminal=true"
    echo "Pełne sprzątanie w Terminalu | bash=\"$SCRIPT\" terminal=true"
else
    echo "⚠ Nie znaleziono skryptu | color=red"
    echo "-- Ustaw SCRIPT na górze pluginu: $SCRIPT"
fi
echo "---"

if [ -f "$STATE" ]; then
    last_human=$(state_val last_run_human)
    last_freed=$(state_val last_freed_mb)
    echo "Ostatnie sprzątanie: ${last_human:-?}, odzyskano $(human "${last_freed:-0}") | color=#888888"
else
    echo "Ostatnie sprzątanie: brak | color=#888888"
fi

latest_log=$(find "$LOGS" -maxdepth 1 -name 'miotla-*.log' 2>/dev/null | sort | tail -1)
if [ -n "$latest_log" ]; then
    echo "Otwórz log | bash=/usr/bin/open param0=\"$latest_log\" terminal=false"
else
    echo "Otwórz log (brak) | color=#888888"
fi
echo "Odśwież | refresh=true"
