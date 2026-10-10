#!/bin/bash
# Smoke-test trybu interaktywnego: bez tty odpowiedzi czytane są z fd3 = stdin.
# Pomijamy wszystkie sekcje ("p") i sprawdzamy, że skrypt dochodzi do
# podsumowania bez błędu i niczego nie usuwa.
TEST_NAME="interactive"
# shellcheck source=tests/lib.sh
. "$(dirname "$0")/lib.sh"

new_sandbox
make_stub osascript 0
mkdir_mb "$FAKE_HOME/.npm/_cacache" 1   # gdyby coś poszło nie tak, zauważymy

# „p" dla każdej z 12 sekcji → wszystko pominięte. yes dostarcza odpowiedzi.
yes p | HOME="$FAKE_HOME" PATH="$STUB_BIN:$PATH" "$MIOTLA" > "$OUT" 2>&1
rc=$?

assert_eq "$rc" "0"                               "tryb interaktywny kończy się kodem 0"
assert_out_has "PODSUMOWANIE"                     "dochodzi do podsumowania"
assert_out_has "pominięto"                        "sekcje pomijane zgodnie z odpowiedzią"
assert_exists "$FAKE_HOME/.npm/_cacache"          "pominięcie wszystkiego = nic nie usunięte"
cleanup_sandbox

# To samo w --dry-run (też nie usuwa)
new_sandbox
make_stub osascript 0
mkdir_mb "$FAKE_HOME/.npm/_cacache" 1
yes p | HOME="$FAKE_HOME" PATH="$STUB_BIN:$PATH" "$MIOTLA" --dry-run > "$OUT" 2>&1
assert_out_has "DRY-RUN"                           "baner dry-run w trybie interaktywnym"
assert_exists "$FAKE_HOME/.npm/_cacache"           "dry-run interaktywny nic nie usuwa"
cleanup_sandbox

finish
