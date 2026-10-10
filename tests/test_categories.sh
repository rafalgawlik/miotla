#!/bin/bash
# Testy kategorii --auto: biała lista jest usuwana, rzeczy nietykalne i spoza
# białej listy zostają; narzędzia (brew/xcrun/docker) są wołane poprawnie;
# Gradle pomijany przy działającym daemonie, Electron przy działającej apce.
TEST_NAME="categories"
# shellcheck source=tests/lib.sh
. "$(dirname "$0")/lib.sh"

# populate_home — standardowa makieta katalogów w $FAKE_HOME
populate_home() {
    local H="$FAKE_HOME"
    # --- biała lista (ma zniknąć) ---
    mkdir_mb "$H/.npm/_cacache" 1
    mkdir_mb "$H/.npm/_npx" 1
    mkdir_mb "$H/Library/Caches/Yarn" 1
    mkdir_mb "$H/.gradle/daemon" 1
    mkdir_mb "$H/.gradle/wrapper/dists/gradle-7.0-bin/abc" 1   # najstarsza dystrybucja → usuń
    mkdir_mb "$H/.gradle/wrapper/dists/gradle-8.9-bin/abc" 1   # zostaje (KEEP=2)
    mkdir_mb "$H/.gradle/wrapper/dists/gradle-9.0-bin/abc" 1   # zostaje
    mkdir_mb "$H/.gradle/caches/7.5" 1                          # wersja spoza keep → usuń
    mkdir_mb "$H/.gradle/caches/8.9" 1                          # zostaje
    mkdir_mb "$H/.gradle/caches/9.0" 1                          # zostaje
    mkdir_mb "$H/.gradle/caches/transforms-3" 1                 # stara generacja → usuń
    mkdir_mb "$H/.gradle/caches/transforms-4" 1                 # najnowsza → zostaje
    mkdir_mb "$H/.gradle/caches/modules-2" 1                    # jedyna generacja → zostaje
    mkdir_mb "$H/.gradle/caches/build-cache-1" 1               # build-cache → usuń w całości
    mkdir_mb "$H/Library/Developer/Xcode/DerivedData/App-abc" 1
    mkdir_mb "$H/Library/Caches/com.apple.dt.Xcode" 1
    mkdir_mb "$H/Library/Caches/org.swift.swiftpm" 1
    mkdir_mb "$H/Library/Developer/CoreSimulator/Caches" 1
    mkdir_mb "$H/Library/Application Support/Notion/Code Cache" 1
    mkdir_mb "$H/Library/Application Support/Notion/Cache" 1

    # --- NIETYKALNE / spoza białej listy (ma zostać) ---
    echo "org.gradle.jvmargs=-Xmx4g" > "$H/.gradle/gradle.properties"
    mkdir_mb "$H/Library/Application Support/Notion/IndexedDB" 1   # dane apki, nie cache
    mkdir_mb "$H/Library/Application Support/Signal/Code Cache" 1  # komunikator — nigdy
    mkdir_mb "$H/.konan/kotlin-native-1" 1
    mkdir_mb "$H/.cache/pip" 1
    mkdir_mb "$H/.claude/projects" 1
    mkdir_mb "$H/.Trash/cos" 1
    mkdir_mb "$H/.android/avd/Pixel.avd" 1
    mkdir_mb "$H/Library/Android/sdk/ndk/27.0" 1
    mkdir_mb "$H/Library/Developer/Xcode/Archives/2024-01-01" 1
}

std_stubs() {
    make_stub osascript 0
    make_stub xcrun 0
    make_stub brew 0 "This operation would free approximately 1.2GB of disk space."
    make_stub docker 0 "Total reclaimed space: 1.5GB"
}

# ══ A. Happy path: nic nie działa → cała biała lista znika, reszta zostaje ══
new_sandbox; std_stubs; make_pgrep ""; populate_home
run_miotla --auto

echo " [A] biała lista usunięta:"
assert_absent "$FAKE_HOME/.npm/_cacache"                            "npm _cacache"
assert_absent "$FAKE_HOME/.npm/_npx"                                "npm _npx"
assert_absent "$FAKE_HOME/Library/Caches/Yarn"                      "Yarn"
assert_absent "$FAKE_HOME/.gradle/daemon"                           "logi daemonów Gradle"
assert_absent "$FAKE_HOME/.gradle/wrapper/dists/gradle-7.0-bin"     "stara dystrybucja Gradle 7.0"
assert_absent "$FAKE_HOME/.gradle/caches/7.5"                       "cache Gradle 7.5"
assert_absent "$FAKE_HOME/.gradle/caches/transforms-3"             "stara generacja transforms-3"
assert_absent "$FAKE_HOME/.gradle/caches/build-cache-1"            "build-cache-1"
assert_absent "$FAKE_HOME/Library/Developer/Xcode/DerivedData/App-abc" "DerivedData"
assert_absent "$FAKE_HOME/Library/Caches/com.apple.dt.Xcode"        "cache Xcode"
assert_absent "$FAKE_HOME/Library/Caches/org.swift.swiftpm"         "cache SPM"
assert_absent "$FAKE_HOME/Library/Developer/CoreSimulator/Caches"   "CoreSimulator/Caches"
assert_absent "$FAKE_HOME/Library/Application Support/Notion/Code Cache" "Electron: Notion Code Cache"
assert_absent "$FAKE_HOME/Library/Application Support/Notion/Cache" "Electron: Notion Cache"

echo " [A] rzeczy nietykalne i zostawiane:"
assert_exists "$FAKE_HOME/.gradle/gradle.properties"               "gradle.properties NIETYKALNE"
assert_exists "$FAKE_HOME/.gradle/caches"                          "katalog ~/.gradle/caches (nie cały kasowany)"
assert_exists "$FAKE_HOME/.gradle/caches/8.9"                      "cache Gradle 8.9 (keep)"
assert_exists "$FAKE_HOME/.gradle/caches/9.0"                      "cache Gradle 9.0 (keep)"
assert_exists "$FAKE_HOME/.gradle/caches/transforms-4"            "najnowsza generacja transforms-4"
assert_exists "$FAKE_HOME/.gradle/caches/modules-2"              "jedyna generacja modules-2"
assert_exists "$FAKE_HOME/.gradle/wrapper/dists/gradle-8.9-bin"    "dystrybucja Gradle 8.9 (keep)"
assert_exists "$FAKE_HOME/.gradle/wrapper/dists/gradle-9.0-bin"    "dystrybucja Gradle 9.0 (keep)"
assert_exists "$FAKE_HOME/Library/Application Support/Notion/IndexedDB" "dane apki Electron (IndexedDB)"
assert_exists "$FAKE_HOME/Library/Application Support/Signal/Code Cache" "Signal NIGDY"
assert_exists "$FAKE_HOME/.konan/kotlin-native-1"                 ".konan NIGDY w auto"
assert_exists "$FAKE_HOME/.cache/pip"                             ".cache NIGDY w auto"
assert_exists "$FAKE_HOME/.claude/projects"                       ".claude NIGDY"
assert_exists "$FAKE_HOME/.Trash/cos"                             "Kosz NIGDY w auto"
assert_exists "$FAKE_HOME/.android/avd/Pixel.avd"                 "emulator NIGDY w auto"
assert_exists "$FAKE_HOME/Library/Android/sdk/ndk/27.0"           "NDK NIGDY w auto"
assert_exists "$FAKE_HOME/Library/Developer/Xcode/Archives/2024-01-01" "Archives NIGDY w auto"

echo " [A] narzędzia wołane poprawnie:"
assert_called "brew cleanup --prune=all"                          "brew cleanup"
assert_called "xcrun simctl delete unavailable"                   "simctl delete unavailable"
assert_called "docker builder prune -f"                           "docker builder prune"
assert_called "docker image prune -f"                             "docker image prune"
assert_not_called "docker system prune"                           "BEZ docker system prune -a"
cleanup_sandbox

# ══ B. Daemon Gradle działa → Gradle pominięty, cache zostaje ══
new_sandbox; std_stubs; make_pgrep "GradleDaemon"; populate_home
run_miotla --auto --json
assert_exists "$FAKE_HOME/.gradle/daemon"                         "daemon: logi daemonów zostają"
assert_exists "$FAKE_HOME/.gradle/caches/build-cache-1"           "daemon: build-cache zostaje"
assert_exists "$FAKE_HOME/.gradle/wrapper/dists/gradle-7.0-bin"   "daemon: stara dystrybucja zostaje"
assert_out_has '"gradle_daemon"'                                  "JSON skipped zawiera gradle_daemon"
assert_absent "$FAKE_HOME/.npm/_cacache"                          "daemon: npm i tak posprzątane"
cleanup_sandbox

# ══ C. Apka Electron działa → jej cache pominięty ══
new_sandbox; std_stubs; make_pgrep "Notion"; populate_home
run_miotla --auto
assert_exists "$FAKE_HOME/Library/Application Support/Notion/Code Cache" "uruchomiona apka: cache zostaje"
assert_out_has "uruchomione — pomijam"                            "komunikat o pominięciu uruchomionej apki"
cleanup_sandbox

# ══ D. dry-run niczego nie usuwa ══
new_sandbox; std_stubs; make_pgrep ""; populate_home
run_miotla --auto --dry-run
assert_exists "$FAKE_HOME/.npm/_cacache"                          "dry-run: nic nie usunięte"
assert_exists "$FAKE_HOME/Library/Caches/Yarn"                    "dry-run: Yarn zostaje"
assert_not_called "docker builder prune"                          "dry-run: docker prune nie wykonany"
assert_out_has "dry-run"                                          "dry-run: adnotacja w wyjściu"
cleanup_sandbox

finish
