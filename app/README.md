# Miotła — apka paska menu (Etap 2)

Natywna apka macOS (rumps/pyobjc) z ikoną miotły w pasku menu. Pokazuje wolne
miejsce i uruchamia sprzątanie **w oknie** (nie w Terminalu). Pod spodem wywołuje
ten sam skrypt `bin/miotla` i czyta jego wynik (`--json` + plik stanu).

## Co potrafi

- ikona 🧹 (besom) + wolne miejsce w pasku; podczas pracy animacja „zamiatania”
- **Szybkie sprzątanie** — `miotla --auto`, wynik w oknie + powiadomienie
- **Podgląd** — `miotla --auto --dry-run` w oknie (nic nie usuwa)
- **Pełne sprzątanie w Terminalu** — tryb interaktywny (wymaga klawiatury)
- „Ostatnie sprzątanie”, „Otwórz log”, „O Miotle”

## Instalacja

### Homebrew (zalecane)

```sh
brew install rafalgawlik/tap/miotla
brew services start miotla
```

Formuła instaluje apkę (venv) **razem ze skryptem `bin/miotla`** (trafia na PATH,
więc apka go znajduje) — skrypt jest częścią instalacji.

Publikowanie nowej wersji: utwórz release `vX.Y.Z` na GitHubie, policz sha
(`app/packaging/homebrew/release-sha.sh X.Y.Z`) i skopiuj `miotla.rb` do tapa
`rafalgawlik/homebrew-tap` (`Formula/miotla.rb`).

### Ze źródeł

```sh
cd app
./run.sh          # pierwszy raz: tworzy .venv i instaluje rumps
```

Autostart po zalogowaniu:

```sh
cd app
./install-autostart.sh      # tworzy LaunchAgent i uruchamia apkę teraz
./uninstall-autostart.sh    # wyłącza autostart i zatrzymuje apkę
```

(Szablon pliku: `packaging/com.miotla.app.plist`.)

## Status

Wersja 0.1 — działa ikona, podgląd i sprzątanie w oknie, animacja.
W planach: kolor progowy liczby w pasku, okno interaktywnego sprzątania
z wyborami (checkboxy) zamiast Terminala, ustawienia.
