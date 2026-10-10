#!/bin/bash
# Testy infrastruktury --auto: RESULT/JSON, plik stanu, log, rotacja, lock,
# dry-run (brak zapisu stanu i powiadomienia).
TEST_NAME="infra"
# shellcheck source=tests/lib.sh
. "$(dirname "$0")/lib.sh"

# ── RESULT + stan + log + powiadomienie (realne uruchomienie, 0 kategorii) ──
new_sandbox
run_miotla --auto
assert_out_has "RESULT status=ok"                 "wypisuje linię RESULT"
assert_out_has "dry_run=0"                         "RESULT: dry_run=0"
STATE="$FAKE_HOME/Library/Caches/miotla/state"
assert_exists "$STATE"                             "plik stanu powstał"
assert_file_has "$STATE" "last_status=ok"          "stan: status ok"
assert_file_has "$STATE" "last_freed_mb="          "stan: pole freed_mb"
LOGDIR="$FAKE_HOME/Library/Logs/miotla"
assert_eq "$(find "$LOGDIR" -name 'miotla-*.log' | wc -l | tr -d ' ')" "1" "powstał 1 log"
assert_called "osascript"                          "wysłano powiadomienie"
cleanup_sandbox

# ── JSON ──
new_sandbox
run_miotla --auto --json
assert_out_has '"status":"ok"'                     "JSON: status"
assert_out_has '"dry_run":0'                       "JSON: dry_run"
assert_out_has '"skipped":['                       "JSON: tablica skipped"
cleanup_sandbox

# ── dry-run: brak zapisu stanu i powiadomienia ──
new_sandbox
run_miotla --auto --dry-run
assert_out_has "dry_run=1"                         "dry-run w RESULT"
assert_absent "$FAKE_HOME/Library/Caches/miotla/state" "dry-run NIE zapisuje stanu"
assert_not_called "osascript"                      "dry-run NIE powiadamia"
cleanup_sandbox

# ── lock: żywy PID blokuje drugie uruchomienie ──
new_sandbox
mkdir -p "$FAKE_HOME/Library/Caches/miotla/lock"
echo $$ > "$FAKE_HOME/Library/Caches/miotla/lock/pid"   # $$ = żywy proces
run_miotla --auto --json
assert_out_has '"status":"locked"'                 "żywy lock → status locked"
cleanup_sandbox

# ── lock: nieświeży (martwy PID) jest przejmowany ──
new_sandbox
mkdir -p "$FAKE_HOME/Library/Caches/miotla/lock"
echo 999999 > "$FAKE_HOME/Library/Caches/miotla/lock/pid"
run_miotla --auto --json
assert_out_has '"status":"ok"'                     "martwy lock → przejęty, ok"
assert_absent "$FAKE_HOME/Library/Caches/miotla/lock" "lock posprzątany po uruchomieniu"
cleanup_sandbox

# ── rotacja logów: zostaje ostatnie 20 ──
new_sandbox
LOGDIR="$FAKE_HOME/Library/Logs/miotla"
mkdir -p "$LOGDIR"
for i in $(seq -w 1 25); do : > "$LOGDIR/miotla-200001$i-000000.log"; done
run_miotla --auto           # tworzy 26., rotacja ma zejść do 20
assert_eq "$(find "$LOGDIR" -name 'miotla-*.log' | wc -l | tr -d ' ')" "20" "po rotacji zostaje 20 logów"
cleanup_sandbox

finish
