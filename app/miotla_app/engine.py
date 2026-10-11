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
    """Znajdź skrypt `miotla`. Kolejność:
    1) kopia dołączona do pakietu (miotla_app/bin/miotla) — apka samodzielna,
    2) repo obok apki (tryb deweloperski),
    3) `miotla` na PATH (instalacja Homebrew),
    4) SCRIPT z ~/.config/miotla/config,
    5) ścieżka domyślna.
    """
    import shutil
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (os.path.join(here, "bin", "miotla"),
                 os.path.normpath(os.path.join(here, "..", "..", "bin", "miotla"))):
        if os.path.exists(cand):
            return cand
    on_path = shutil.which("miotla")
    if on_path:
        return on_path
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
    args = [script_path(), "--auto", "--json", "--no-notify"]
    if dry_run:
        args.append("--dry-run")
    try:
        p = subprocess.run(args, capture_output=True, text=True)
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out, _parse_summary(out)
    except Exception as exc:  # noqa: BLE001
        return 1, f"Błąd uruchomienia miotła:\n{exc}", {}


def scan(tokens: list | None = None) -> list:
    """Zeskanuj kategorie (bez usuwania). Zwróć listę dictów kategorii."""
    arg = "--scan" if not tokens else "--scan=" + ",".join(tokens)
    try:
        p = subprocess.run([script_path(), arg], capture_output=True, text=True)
        return json.loads(p.stdout or "[]")
    except Exception:
        return []


def clean(tokens: list, dry_run: bool = False) -> tuple[int, str, dict]:
    """Usuń wybrane kategorie. Zwróć (kod, pełne_wyjście, podsumowanie)."""
    if not tokens:
        return 0, "", {}
    args = [script_path(), "--clean=" + ",".join(tokens), "--json", "--no-notify"]
    if dry_run:
        args.append("--dry-run")
    try:
        p = subprocess.run(args, capture_output=True, text=True)
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out, _parse_summary(out)
    except Exception as exc:  # noqa: BLE001
        return 1, f"Błąd uruchomienia miotła:\n{exc}", {}


def clean_items(paths: list, dry_run: bool = False) -> tuple[int, str, dict]:
    """Usuń dokładnie wskazane ścieżki (bezpiecznie, tylko w $HOME)."""
    if not paths:
        return 0, "", {}
    import tempfile
    fd, fn = tempfile.mkstemp(suffix=".txt", prefix="miotla-sel-")
    try:
        with os.fdopen(fd, "w") as f:
            f.write("\n".join(paths) + "\n")
        args = [script_path(), "--clean-items=" + fn, "--json", "--no-notify"]
        if dry_run:
            args.append("--dry-run")
        p = subprocess.run(args, capture_output=True, text=True)
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out, _parse_summary(out)
    except Exception as exc:  # noqa: BLE001
        return 1, f"Błąd uruchomienia miotła:\n{exc}", {}
    finally:
        try:
            os.remove(fn)
        except OSError:
            pass


def sudo_shell_cmd(items: list) -> str:
    """Zbuduj polecenie powłoki dla zaznaczonych pozycji sudo (sentinelowe ścieżki)."""
    import shlex
    cmds: list = []
    for it in items:
        if it == "sudo:sleepimage":
            cmds.append("/usr/bin/pmset -a hibernatemode 0")
            cmds.append("/bin/rm -f /private/var/vm/sleepimage")
        elif it.startswith("sudo:snapshot:"):
            date = it.split(":", 2)[2]
            cmds.append("/usr/bin/tmutil deletelocalsnapshots " + shlex.quote(date))
    return " ; ".join(cmds)


def clean_sudo(items: list) -> tuple[int, str]:
    """Usuń pozycje wymagające sudo — jedno natywne pytanie o hasło (osascript)."""
    shell_cmd = sudo_shell_cmd(items)
    if not shell_cmd:
        return 0, ""
    apple = 'do shell script "%s" with administrator privileges' % (
        shell_cmd.replace("\\", "\\\\").replace('"', '\\"'))
    try:
        p = subprocess.run(["osascript", "-e", apple], capture_output=True, text=True)
        out = (p.stdout or "") + (p.stderr or "")
        if p.returncode != 0 and "-128" in out:
            out = "Anulowano (nie podano hasła)."
        return p.returncode, out or "Gotowe (sudo)."
    except Exception as exc:  # noqa: BLE001
        return 1, f"Błąd (sudo): {exc}"


def open_interactive_in_terminal() -> None:
    """Pełne, interaktywne sprzątanie wymaga klawiatury → otwórz w Terminalu."""
    subprocess.run(["open", "-a", "Terminal", script_path()], check=False)


def open_path(path: str) -> None:
    if path:
        subprocess.run(["open", path], check=False)
