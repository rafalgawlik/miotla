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
ICON="iVBORw0KGgoAAAANSUhEUgAAACQAAAAkCAYAAADhAJiYAAAACXBIWXMAABYlAAAWJQFJUiTwAAACy0lEQVR4nOWXXYhNURiGn/1zZjBMwqCQnwsJFyZycn8UN6O4lAtNUUrNhSh3UpqaJiF3kkTmAnHlxoXISLlQU37KT4lElL+Rceacra/eVavdhHP2OXsrq1bfae21z372u97vW2vDf94CIAYi/lG4Qh8eAjOBA0DFGy+klRTPAwlQB9ZqLCwKpl8wP4oEihUrgvgpqD0az9XckeJq4BNQFcxgETCh4gLgpdQxmBFPudwMHejtO4FRgVi/o7Eob5hYv0e8jHoGzCvSxIOCqco/q4rwTUlxr2AmpE4lBZtLixW3CGJCUP0p2FxapGiF7ouX3kfzhAlSBl0IvPDS+0IR6R2pTwfup9K7lGd6hymDXvHS+6nS2+3uDbe4ifmTwDmgA3gLbBfMV6AP+CB1auRk3l7go7dEk4Lp9aCbbmED8xJgtpZoFvBcCrnr2+SnWh7eiRUvC8wdI74B75Xqo5oXthsoVhxIwbhe1djh1Py2+qYsrziYBzKvgzJTP9Tctqlj0ofyjX+meaQt4ThwD3jnLd/8rFC/k9dgTJUzwDJPnbPKKDP2TWCGtg3bRNfIU2GzaR/+od4MADt0MLe6c0oPt6XsAbqBucBdqbIpq0JTAUWCMd8MSZlpwC0Z2CBWAG8UO7SXGfQG/UfSKiC/3lwSXKhd/CKwCxjTwX1cH349qj+2VOu9Kh20Cqgu3yyXOrZ8x4B98kyfsqwsiEUCMPWWAIv1X5mB3FLt93zTCVwH5ugY+hhYpyJoarwSRFX3Bt4HYCYglxVbgZMaM9/Y1nAVOAgMA7uBJzKyKfcZ6NIJ0bVyFiCX9omgNgI3dIQwb5wADgGv5RNT6TSwU/d168Fdgqt5CiVZgawf8a5Z9tgy3tbDVkqxMRVA2+G/q2LX9UI2f7MAxwXbEFhaVrcx/m1RC1QgDcRSf6m+Vq/pJTIDTXXNj9ZNDfcg+93S9gvklrZFhHJkRQAAAABJRU5ErkJggg=="
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
