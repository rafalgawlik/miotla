# 🧹 Miotła

Narzędzie do bezpiecznego sprzątania Maca dewelopera: cache Dockera, Gradle/Androida/KMP,
Xcode'a i symulatorów, aplikacji Electron (Notion, Teams, Claude, VS Code…), npm/Homebrew,
Kosza i danych systemowych. Pokazuje wolne miejsce w pasku menu i pozwala posprzątać
jednym kliknięciem.

Dwa tryby:

- **Interaktywny** (`miotla`) — przechodzi po kategoriach i pyta o każdą decyzję. Pełna kontrola,
  także rzeczy, których tryb automatyczny świadomie nie rusza (emulatory, Archives, Kosz,
  snapshoty Time Machine itd.).
- **Automatyczny** (`miotla --auto`) — zero pytań, sprząta **tylko w 100% odtwarzalne cache**
  (biała lista poniżej). Napędza plugin SwiftBar w pasku menu.

## Bezpieczeństwo

Miotła kasuje **wyłącznie wewnątrz katalogu domowego** (jedyne wyjątki w trybie interaktywnym,
zawsze po pytaniu: snapshoty Time Machine i `sleepimage` przez `sudo`).

**Nigdy nie rusza:**

- przeglądarek (Brave, Chrome, Firefox, Safari, Arc, Edge…),
- danych Signala i WhatsAppa,
- `~/.gradle/gradle.properties`,
- ustawień i logowania Claude Code (`~/.claude`).

Na prawdziwym systemie uruchamiaj najpierw **podgląd** (`--dry-run`) — nic wtedy nie znika.

## Tryb `--auto` — co sprząta (biała lista)

Tylko cache, które narzędzia odtworzą same przy następnym użyciu:

- **npm**: `~/.npm/_cacache`, `~/.npm/_npx`; **Yarn**: `~/Library/Caches/Yarn`
- **Homebrew**: `brew cleanup --prune=all`
- **Gradle** — tylko gdy **nie działa** żaden daemon Gradle/Kotlin (jeśli działa — pomija,
  nie zabija): build-cache, stare generacje cache (`transforms-3` itp.), cache i dystrybucje
  starszych wersji (zostają 2 najnowsze), logi daemonów
- **Xcode**: DerivedData, cache Xcode i Swift Package Managera, `CoreSimulator/Caches`,
  `simctl delete unavailable`
- **Electron**: katalogi cache aplikacji opartych na Chromium, **z pominięciem uruchomionych**
  (konta, dokumenty i ustawienia zostają — znika tylko cache)
- **Docker** (gdy działa): `docker builder prune` i `docker image prune` — tylko wiszące obrazy
  i cache buildów (bez `-a`, bez wolumenów)

**Czego `--auto` NIGDY nie rusza:** emulatorów i obrazów systemu Android, NDK, runtime'ów
symulatorów, Xcode Archives, całego `~/.gradle/caches`, `~/.konan`, `~/.cache`, wersji Claude Code,
folderów starych IDE, katalogów `build/` w projektach, Kosza, snapshotów Time Machine,
`sleepimage` — i niczego przez `sudo`.

### Użycie z wiersza poleceń

```sh
bin/miotla                 # tryb interaktywny
bin/miotla --dry-run       # interaktywny podgląd (nic nie usuwa)
bin/miotla --auto          # automatyczne sprzątanie białej listy
bin/miotla --auto --dry-run  # podgląd tego, co zrobiłby --auto
bin/miotla --auto --json   # wynik jako JSON (do skryptów/aplikacji)
```

Każde uruchomienie `--auto`:

- blokuje się przed równoległym startem (lock w `~/Library/Caches/miotla/`),
- zapisuje log w `~/Library/Logs/miotla/` (zostaje ostatnie 20),
- kończy się linią do parsowania, np.:
  `RESULT status=ok freed_mb=4312 free_before_mb=98000 free_after_mb=102312 dry_run=0 skipped=gradle_daemon`
- zapisuje ostatni wynik (data, odzyskane MB) do pliku stanu `~/Library/Caches/miotla/state`,
- pokazuje powiadomienie macOS „Miotła: Odzyskano X” (poza `--dry-run`).

## Plugin SwiftBar (pasek menu)

W pasku: ikona miotły + wolne miejsce na `/System/Volumes/Data`
(czerwone < 20 GB, pomarańczowe < 40 GB; podczas pracy — „sprzątanie…”).

Menu: wolne/zajęte miejsce, **Szybkie sprzątanie** (`--auto` w tle),
**Podgląd** (`--auto --dry-run` w Terminalu), **Pełne sprzątanie w Terminalu** (tryb interaktywny),
„Ostatnie sprzątanie: …”, „Otwórz log”.

Odświeża się co 10 minut i jest tanie — czyta tylko `df` i plik stanu (żadnego `du`).

### Instalacja

1. Zainstaluj SwiftBar: <https://swiftbar.app> lub `brew install --cask swiftbar`.
2. Uruchom SwiftBar i wskaż folder na wtyczki (SwiftBar → Preferences).
3. W repo:

   ```sh
   ./install.sh
   ```

   Skrypt sprawdzi SwiftBar, podlinkowuje plugin do jego folderu wtyczek i — jeśli repo leży
   poza `~/Projects/miotla` — zapisze ścieżkę skryptu do `~/.config/miotla/config`.
   **Niczego nie instaluje bez pytania.**
4. Nadaj SwiftBarowi **Pełny dostęp do dysku** (żeby widział m.in. Kosz i cache aplikacji):
   *Ustawienia systemowe → Prywatność i ochrona → Pełny dostęp do dysku* → dodaj **SwiftBar**.

Odinstalowanie: `./uninstall.sh`.

### Konfiguracja

Progi kolorów i ścieżka skryptu są na górze `swiftbar/miotla.10m.sh`. Można je nadpisać bez
edycji pluginu, tworząc `~/.config/miotla/config`:

```sh
SCRIPT="$HOME/ścieżka/do/bin/miotla"
RED_GB=20
ORANGE_GB=40
```

## Wymagania

- macOS (systemowy `bash` 3.2 wystarcza)
- SwiftBar — tylko dla pluginu w pasku menu
- narzędzia opcjonalne: `brew`, `docker`, `xcrun` — używane, jeśli są obecne

## Testy

```sh
tests/run.sh
```

Testy działają na atrapie katalogu domowego i atrapach narzędzi (xcrun/docker/brew/pgrep…),
więc **nie dotykają prawdziwego `$HOME`**. CI (GitHub Actions) odpala `shellcheck` i testy
na `macos-latest`.
