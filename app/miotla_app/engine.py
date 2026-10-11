"""Silnik: rozmowa z `bin/miotla`, wolne miejsce (df) i plik stanu.

Apka nie powiela logiki sprzątania — wywołuje skrypt `miotla` i czyta jego
wynik (linia RESULT / --json oraz plik stanu). Dzięki temu Etap 1 i Etap 2
korzystają z tego samego, przetestowanego silnika.
"""
from __future__ import annotations

import json
import os
import subprocess

HOME = os.path.expanduser("~")
CACHE = os.path.join(HOME, "Library", "Caches", "miotla")
LOGS = os.path.join(HOME, "Library", "Logs", "miotla")
STATE = os.path.join(CACHE, "state")
NOTIFY_STATE = os.path.join(CACHE, "notify")
VOLUME = "/System/Volumes/Data"


def script_path() -> str:
    """Ścieżka do `bin/miotla`: repo obok apki → ~/.config/miotla/config → domyślna."""
    here = os.path.dirname(os.path.abspath(__file__))
    cand = os.path.normpath(os.path.join(here, "..", "..", "bin", "miotla"))
    if os.path.exists(cand):
        return cand
    cfg = os.path.join(HOME, ".config", "miotla", "config")
    try:
        for line in open(cfg):
            line = line.strip()
            if line.startswith("SCRIPT="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                val = os.path.expanduser(val.replace("$HOME", HOME))
                if val:
                    return val
    except OSError:
        pass
    return os.path.join(HOME, "Projects", "miotla", "bin", "miotla")


def disk_free_used_mb() -> tuple[int, int]:
    """(wolne_MB, zajęte_MB) dla wolumenu danych — tanio, przez df."""
    try:
        out = subprocess.run(["df", "-m", VOLUME], capture_output=True, text=True).stdout
        parts = out.splitlines()[1].split()
        return int(parts[3]), int(parts[2])
    except Exception:
        return 0, 0


def read_state() -> dict:
    d: dict = {}
    try:
        for line in open(STATE):
            if "=" in line:
                k, v = line.rstrip("\n").split("=", 1)
                d[k] = v
    except OSError:
        pass
    return d


def latest_log() -> str | None:
    try:
        logs = [os.path.join(LOGS, f) for f in os.listdir(LOGS)
                if f.startswith("miotla-") and f.endswith(".log")]
        return max(logs, key=os.path.getmtime) if logs else None
    except OSError:
        return None


def human(mb) -> str:
    mb = float(mb or 0)
    return f"{mb / 1024:.1f} GB" if mb >= 1024 else f"{int(mb)} MB"


def human0(mb) -> str:
    mb = float(mb or 0)
    return f"{mb / 1024:.0f} GB" if mb >= 1024 else f"{int(mb)} MB"


def _parse_summary(output: str) -> dict:
    """Wyłuskaj podsumowanie z wyjścia (ostatnia linia JSON albo linia RESULT)."""
    for line in reversed(output.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except ValueError:
                pass
        if line.startswith("RESULT "):
            d: dict = {}
            for tok in line[len("RESULT "):].split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    d[k] = v
            return d
    return {}


def run_auto(dry_run: bool = False) -> tuple[int, str, dict]:
    """Uruchom `miotla --auto [--dry-run] --json`. Zwróć (kod, pełne_wyjście, podsumowanie)."""
    args = [script_path(), "--auto", "--json"]
    if dry_run:
        args.append("--dry-run")
    try:
        p = subprocess.run(args, capture_output=True, text=True)
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out, _parse_summary(out)
    except Exception as exc:  # noqa: BLE001
        return 1, f"Błąd uruchomienia miotła:\n{exc}", {}


def open_interactive_in_terminal() -> None:
    """Pełne, interaktywne sprzątanie wymaga klawiatury → otwórz w Terminalu."""
    subprocess.run(["open", "-a", "Terminal", script_path()], check=False)


def open_path(path: str) -> None:
    if path:
        subprocess.run(["open", path], check=False)
