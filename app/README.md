# Miotła — menu bar app (Stage 2)

Native macOS app (rumps/pyobjc) with a broom icon in the menu bar. Shows free
space and runs cleanup **in a window** (not a terminal). Under the hood it calls
the same `bin/miotla` engine and reads its result (`--json` + a state file).

## What it does

- 🧹 icon + free space in the bar (colored: orange < 40 GB, red < 20 GB);
  the broom sweeps while a cleanup runs
- **Quick cleanup** — `miotla --auto`, result in a window + notification
- **Preview** — `miotla --auto --dry-run`, in a window (removes nothing)
- **Full cleanup…** — a window with per-item checkboxes (specific emulators,
  Archives, old versions…), including sudo items (Time Machine snapshots,
  sleepimage) via a native password prompt
- Last cleanup, Open log, About Miotła (with links)

## Install

### As an app (recommended — launchable from Dock / Launchpad / Spotlight)

```sh
cd app
./install-app.sh        # builds /Applications/Miotła.app, adds a Login Item, launches it
./uninstall-app.sh      # removes the app, Login Item and autostart
```

The app is a thin bundle that runs this repo's Python venv (created on first
launch), so keep the repo in place. Grant **Full Disk Access**
(System Settings → Privacy & Security) so it can see the Trash and app caches.

### Homebrew

```sh
brew install rafalgawlik/tap/miotla
brew services start miotla
```

The formula installs the app (venv) **together with the `bin/miotla` script**
(on PATH, so the app finds it). To publish a new version: create a `vX.Y.Z`
release on GitHub, compute the sha (`app/packaging/homebrew/release-sha.sh X.Y.Z`)
and copy `miotla.rb` into the tap `rafalgawlik/homebrew-tap`.

### From source (menu bar only, no app bundle)

```sh
cd app
./run.sh                # first run creates .venv and installs rumps
```

## Status

Works: menu bar icon with threshold color, Quick/Preview/Full cleanup in
windows, sweeping animation, About with links, `.app` bundle with autostart.
The `bin/miotla` CLI (interactive mode) stays available and is in Polish.
