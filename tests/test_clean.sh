#!/bin/bash
# Testy trybów --scan / --clean (okno „Pełne sprzątanie"): skan wypisuje
# kategorie, clean usuwa tylko wybrane, dry-run nic nie rusza, Kosz empty,
# nietykalne i niewybrane kategorie zostają.
TEST_NAME="clean"
# shellcheck source=tests/lib.sh
. "$(dirname "$0")/lib.sh"

populate() {
    local H="$FAKE_HOME"
    mkdir_mb "$H/.npm/_cacache" 2
    mkdir_mb "$H/Library/Caches/Yarn" 2
    mkdir_mb "$H/Library/Developer/Xcode/DerivedData/App-x" 3
    mkdir_mb "$H/.cache/pip" 2
    mkdir_mb "$H/.gradle/caches/8.9" 3
    mkfile_mb "$H/.Trash/plik.bin" 2
    echo "x=1" > "$H/.gradle/gradle.properties"   # NIETYKALNE (poza caches)
}

# ── --scan: wypisuje kategorie z rozmiarami ──
new_sandbox; make_pgrep ""; populate
run_miotla --scan --json
assert_out_has '"token":"xcode_derived"'      "scan: jest xcode_derived"
assert_out_has '"token":"gradle_all"'          "scan: jest gradle_all"
assert_out_has '"token":"trash"'               "scan: jest trash"
assert_out_has '"desc":"DerivedData/App-x"'    "scan: pozycja DerivedData"
cleanup_sandbox

# ── --clean dry-run: nic nie usuwa ──
new_sandbox; make_pgrep ""; populate
run_miotla --clean=xcode_derived,cache_dir --dry-run
assert_out_has "dry_run=1"                     "clean dry-run: RESULT"
assert_exists "$FAKE_HOME/Library/Developer/Xcode/DerivedData/App-x" "dry-run nie usuwa DerivedData"
assert_exists "$FAKE_HOME/.cache/pip"          "dry-run nie usuwa .cache"
cleanup_sandbox

# ── --clean realne: usuwa tylko wybrane ──
new_sandbox; make_pgrep ""; populate
run_miotla --clean=xcode_derived,cache_dir,trash
assert_absent "$FAKE_HOME/Library/Developer/Xcode/DerivedData/App-x" "clean: DerivedData usunięte"
assert_absent "$FAKE_HOME/.cache/pip"          "clean: .cache usunięte"
assert_eq "$(ls -A "$FAKE_HOME/.Trash" 2>/dev/null)" "" "clean: Kosz opróżniony"
assert_exists "$FAKE_HOME/.Trash"              "clean: katalog .Trash zostaje"
# niewybrane kategorie i nietykalne — bez zmian
assert_exists "$FAKE_HOME/.npm/_cacache"       "clean: npm (niewybrane) zostaje"
assert_exists "$FAKE_HOME/Library/Caches/Yarn" "clean: Yarn (niewybrane) zostaje"
assert_exists "$FAKE_HOME/.gradle/caches/8.9"  "clean: gradle (niewybrane) zostaje"
assert_exists "$FAKE_HOME/.gradle/gradle.properties" "clean: gradle.properties NIETYKALNE"
cleanup_sandbox

# ── gradle_all usuwa cały ~/.gradle/caches, ale nie gradle.properties ──
new_sandbox; make_pgrep ""; populate
run_miotla --clean=gradle_all
assert_absent "$FAKE_HOME/.gradle/caches"      "gradle_all: cały caches usunięty"
assert_exists "$FAKE_HOME/.gradle/gradle.properties" "gradle_all: gradle.properties zostaje"
cleanup_sandbox

finish
