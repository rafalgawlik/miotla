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

## Uruchomienie

```sh
cd app
./run.sh          # pierwszy raz: tworzy .venv i instaluje rumps
```

Autostart po zalogowaniu: skopiuj `packaging/com.miotla.app.plist` do
`~/Library/LaunchAgents/` (zamień ścieżkę w pliku) i `launchctl load` go.

## Status

Wersja 0.1 — działa ikona, podgląd i sprzątanie w oknie, animacja.
W planach: kolor progowy liczby w pasku, okno interaktywnego sprzątania
z wyborami (checkboxy) zamiast Terminala, ustawienia.
