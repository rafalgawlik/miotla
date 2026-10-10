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
ICON="iVBORw0KGgoAAAANSUhEUgAAACQAAAAkCAYAAADhAJiYAAACu0lEQVR4nM2YTahNURTHf+fj4XnSi5fnqzCRlAkTokhmipESb0RSSowMEFMjEyZmSspEqWeEmWKGiVKUiQHPZz7ue9e77x6t+u9ane69Ot179nurTmvftfY5+7/X/q+1974QX1IgYYFI6trJQgGzAVg236By6SPANPAKGBeg6KAy6V1AA5gDCmBPyR8VzEbgE9ASmFtaQs+paNk0CrwWEHseuqWKtlyJomP6sQNj3BmRPVp0Ekfi2wLSBj4A62SPulRD0lcF5i/wG9gxHyQekj4pME3pg7KHyEWRXPqAliiAOVMCG0Uy6a3AD2BWYK6VwEaRVNoq73tFx8Dcc2CipncKDAPPXHo/BRa71K8dRDm977v0fgeMxU7vDFik9nWBMd58Bba4PlEkd+1zrtbYPrWvQ59aJNFjvHgC3AROCEzYMCdigfG8WQl8ceRtaanODqrW5BUBjeodAxJIawXwo/q0pA1srZJJ33UELkrPI6V/7ceKTHq7Bg4nvsKBM9ukO3bUKpn0ZInERQngS1eVk7rB7O0CJhTDsF3sL71XWf5XSdvAEmA38EADXZTvhqryc+CObFYY6YfUvQDZ4PbhY8BO4JsiZId1dAK0PlPiUUt3rhWaSDJIQCF1U+Cyas9q4Ke75DW0Z5lvLfBdxD/cD7m7Aco0y6PAJgGZk92igSN0pq0jVZQmHL8GAigRGNsmLrmBlysqdmsIYn1m5Guqn10AV6ldebdPe0TntE6AiU6BY+JLWLJpFcIpAfjsTgGHeny/EqAQHYvCBbVxy+G3jaKDL9Sk4/K1+wUUonNed6imftuAS3WdGZEtl56V74+iVygrN8tfKUq+c5ipAbki27DsMyL3L2CNbJl0w/nGZbPadarLpHtK0iHVjQ/bFH5kf6s/DCzbDJyBfqPTofcZr9brO/b7Razdvzb5Bx5swQ8yjGKOAAAAAElFTkSuQmCC"

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
    echo "sprzątanie… | templateImage=$ICON"
else
    printf '%s | templateImage=%s%s\n' "$(human0 "$free_mb")" "$ICON" "${COLOR:+ color=$COLOR}"
fi

echo "---"
printf 'Wolne: %s' "$(human "$free_mb")"; [ -n "$COLOR" ] && printf ' | color=%s' "$COLOR"; echo
echo "Zajęte: $(human "$used_mb")"
echo "---"

if [ -x "$SCRIPT" ]; then
    echo "Szybkie sprzątanie | bash=\"$SCRIPT\" param0=--auto terminal=false refresh=true"
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
