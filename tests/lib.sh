#!/bin/bash
# Biblioteka pomocnicza testów Miotły.
# Testy działają WYŁĄCZNIE na atrapie $HOME w katalogu tymczasowym oraz na
# atrapach narzędzi (xcrun/docker/brew/tmutil/pgrep/osascript/pmset) w PATH.
# Nigdy nie dotykają prawdziwego $HOME.

set -u

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
MIOTLA="$ROOT/bin/miotla"

PASS=0
FAIL=0

# ── sandbox ──────────────────────────────────────────────────
# new_sandbox → ustawia FAKE_HOME, STUB_BIN, CALL_LOG, OUT
new_sandbox() {
    SANDBOX=$(mktemp -d "${TMPDIR:-/tmp}/miotla-test.XXXXXX") || exit 1
    FAKE_HOME="$SANDBOX/home"
    STUB_BIN="$SANDBOX/bin"
    CALL_LOG="$SANDBOX/calls.log"
    OUT="$SANDBOX/out.txt"
    mkdir -p "$FAKE_HOME" "$STUB_BIN"
    : > "$CALL_LOG"
    # Domyślny stub osascript — żeby testy nie wysyłały prawdziwych powiadomień.
    make_stub osascript 0
}
cleanup_sandbox() { [ -n "${SANDBOX:-}" ] && rm -rf "$SANDBOX"; }

# make_stub NAZWA KOD_WYJŚCIA [tekst_stdout...]
# Tworzy atrapę narzędzia: loguje argumenty do CALL_LOG, wypisuje tekst, zwraca kod.
make_stub() {
    local name="$1" code="$2"; shift 2
    {
        echo '#!/bin/bash'
        echo "echo \"$name \$*\" >> \"$CALL_LOG\""
        local line
        for line in "$@"; do printf 'printf "%%s\\n" %q\n' "$line"; done
        echo "exit $code"
    } > "$STUB_BIN/$name"
    chmod +x "$STUB_BIN/$name"
}

# mkfile_mb ŚCIEŻKA MB — utwórz plik o podanym rozmiarze (realne bajty, nie sparse)
mkfile_mb() {
    mkdir -p "$(dirname "$1")"
    dd if=/dev/zero of="$1" bs=1048576 count="$2" 2>/dev/null
}
# mkdir_mb KATALOG MB — katalog z jednym plikiem danego rozmiaru
mkdir_mb() { mkdir -p "$1"; mkfile_mb "$1/data.bin" "$2"; }

# ── uruchamianie miotły w sandboxie ──────────────────────────
# run_miotla ARGS... → stdout+stderr do OUT, zwraca kod wyjścia miotły
run_miotla() {
    HOME="$FAKE_HOME" \
    PATH="$STUB_BIN:$PATH" \
    MIN_SIZE_MB="${MIN_SIZE_MB:-1}" \
        "$MIOTLA" "$@" > "$OUT" 2>&1
}

# ── asercje ──────────────────────────────────────────────────
_ok()   { PASS=$((PASS + 1)); printf '  \033[0;32m✓\033[0m %s\n' "$1"; }
_bad()  { FAIL=$((FAIL + 1)); printf '  \033[0;31m✗\033[0m %s\n' "$1"; }

assert_exists()     { if [ -e "$1" ]; then _ok "istnieje: ${2:-$1}"; else _bad "miało istnieć: ${2:-$1}"; fi; }
assert_absent()     { if [ ! -e "$1" ]; then _ok "usunięte/brak: ${2:-$1}"; else _bad "miało NIE istnieć: ${2:-$1}"; fi; }
assert_file_has()   { if grep -qF "$2" "$1" 2>/dev/null; then _ok "${3:-zawiera: $2}"; else _bad "${3:-brak w pliku: $2} (plik: $1)"; fi; }
assert_out_has()    { if grep -qF "$1" "$OUT"; then _ok "${2:-wyjście zawiera: $1}"; else _bad "${2:-brak w wyjściu: $1}"; fi; }
assert_out_lacks()  { if grep -qF "$1" "$OUT"; then _bad "${2:-wyjście NIE powinno zawierać: $1}"; else _ok "${2:-brak w wyjściu (ok): $1}"; fi; }
assert_called()     { if grep -qF "$1" "$CALL_LOG"; then _ok "wywołano: $1"; else _bad "miało być wywołane: $1"; fi; }
assert_not_called() { if grep -qF "$1" "$CALL_LOG"; then _bad "NIE powinno być wywołane: $1"; else _ok "nie wywołano (ok): $1"; fi; }
assert_eq()         { if [ "$1" = "$2" ]; then _ok "${3:-równe: $1}"; else _bad "${3:-$1 != $2}"; fi; }

# finish → podsumowanie i kod wyjścia (0 = wszystko przeszło)
finish() {
    printf '  %s: %d OK, %d BŁĄD\n' "${TEST_NAME:-test}" "$PASS" "$FAIL"
    [ "$FAIL" -eq 0 ]
}
