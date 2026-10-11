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

# ── ryzykowne kategorie per-pozycja: scan emituje tylko „stare/nieużywane" ──
new_sandbox; make_pgrep ""   # pgrep "" → qemu nie działa
mkdir_mb "$FAKE_HOME/.android/avd/Pixel.avd" 2
mkdir_mb "$FAKE_HOME/.android/avd/Tablet.avd" 2
mkdir_mb "$FAKE_HOME/.gradle/wrapper/dists/gradle-7.0-bin/a" 2
mkdir_mb "$FAKE_HOME/.gradle/wrapper/dists/gradle-8.9-bin/a" 2
mkdir_mb "$FAKE_HOME/.gradle/wrapper/dists/gradle-9.0-bin/a" 2
run_miotla --scan=gradle_dists,android_emulators --json
assert_out_has '"desc":"Gradle 7.0 (gradle-7.0-bin)"' "scan: stara dystrybucja 7.0 na liście"
assert_out_lacks '"desc":"Gradle 9.0'                 "scan: najnowszy Gradle NIE na liście"
assert_out_has '"desc":"Emulator Pixel"'              "scan: emulator Pixel na liście"
cleanup_sandbox

# ── nowe kategorie: DeviceSupport, cache narzędzi w ~ ──
new_sandbox; make_pgrep ""
mkdir_mb "$FAKE_HOME/Library/Developer/Xcode/iOS DeviceSupport/17.0" 2
mkdir_mb "$FAKE_HOME/.sometool/cache" 2
run_miotla --scan=xcode_devicesupport,home_tool_caches --json
assert_out_has '"iOS DeviceSupport/17.0"'  "scan: DeviceSupport na liście"
assert_out_has '.sometool/cache'           "scan: cache narzędzia w ~ na liście"
cleanup_sandbox

# ── --clean-items usuwa dokładnie wskazane ścieżki; strażnik $HOME ──
new_sandbox; make_pgrep ""
mkdir_mb "$FAKE_HOME/.android/avd/Pixel.avd" 2
mkdir_mb "$FAKE_HOME/.android/avd/Tablet.avd" 2
printf '%s\n' "$FAKE_HOME/.android/avd/Pixel.avd" > "$SANDBOX/sel.txt"
run_miotla "--clean-items=$SANDBOX/sel.txt"
assert_absent "$FAKE_HOME/.android/avd/Pixel.avd"  "clean-items: Pixel usunięty"
assert_exists "$FAKE_HOME/.android/avd/Tablet.avd" "clean-items: Tablet (niewskazany) zostaje"
# ścieżka spoza $HOME — odmowa
printf '/etc/hosts\n' > "$SANDBOX/evil.txt"
run_miotla "--clean-items=$SANDBOX/evil.txt"
assert_out_has "Odmowa"                            "clean-items: odmowa dla ścieżki spoza HOME"
assert_exists "/etc/hosts"                         "clean-items: /etc/hosts nietknięte"
cleanup_sandbox

finish
