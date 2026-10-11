"""Miotła — apka paska menu (rumps): ikona + wolne miejsce, sprzątanie w oknie."""
from __future__ import annotations

import os
import threading

import rumps

from . import __version__, engine

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
ICON_PATH = os.path.join(_ASSETS, "broom-template.png")
SWEEP_FRAMES = [os.path.join(_ASSETS, f"broom_sweep_{i:02d}.png") for i in range(8)]
SWEEP_FRAMES = [p for p in SWEEP_FRAMES if os.path.exists(p)]
FALLBACK_TITLE = "🧹"

RED_GB = 20
ORANGE_GB = 40

_APP = None


def _set_app_name(name: str = "Miotła") -> None:
    try:
        from Foundation import NSBundle
        bundle = NSBundle.mainBundle()
        for getter in ("localizedInfoDictionary", "infoDictionary"):
            info = getattr(bundle, getter)()
            if info is not None:
                info["CFBundleName"] = name
                info["CFBundleDisplayName"] = name
    except Exception:
        pass


class MiotlaApp(rumps.App):
    def __init__(self) -> None:
        has_icon = os.path.exists(ICON_PATH)
        super().__init__(
            "Miotła",
            icon=ICON_PATH if has_icon else None,
            title=None if has_icon else FALLBACK_TITLE,
            template=True,
            quit_button="Zakończ",
        )
        global _APP
        _APP = self
        _set_app_name()

        self._busy = False
        self._anim_timer = None
        self._anim_i = 0

        self.status_item = rumps.MenuItem("Wolne: …")
        self.quick_item = rumps.MenuItem("Szybkie sprzątanie", callback=self.quick_clean)
        self.preview_item = rumps.MenuItem("Podgląd (co zostałoby usunięte)", callback=self.preview)
        self.full_item = rumps.MenuItem("Pełne sprzątanie…", callback=self.full_clean_window)
        self.term_item = rumps.MenuItem("Interaktywne (Terminal)…", callback=self.full_terminal)
        self.last_item = rumps.MenuItem("Ostatnie sprzątanie: —")
        self.log_item = rumps.MenuItem("Otwórz log", callback=self.open_log)

        self.menu = [
            self.status_item,
            None,
            self.quick_item,
            self.preview_item,
            self.full_item,
            self.term_item,
            None,
            self.last_item,
            self.log_item,
            rumps.MenuItem("O Miotle", callback=self.about),
        ]

        self.refresh()
        self.timer = rumps.Timer(self._tick, 300)   # co 5 min
        self.timer.start()

    # ---------------------------------------------------------------- UI
    def _apply_busy(self, on: bool) -> None:
        if self._anim_timer is not None:
            self._anim_timer.stop()
            self._anim_timer = None
        if on and SWEEP_FRAMES:
            self.title = "sprzątanie…"
            self._anim_i = 0
            self._anim_timer = rumps.Timer(self._anim_tick, 0.09)
            self._anim_timer.start()
        elif on:
            self.title = "sprzątanie…"
        else:
            self.icon = ICON_PATH
            self.refresh()

    def _set_busy(self, on: bool) -> None:
        from PyObjCTools.AppHelper import callAfter
        self._busy = bool(on)
        callAfter(self._apply_busy, bool(on))

    def _anim_tick(self, _timer) -> None:
        self.icon = SWEEP_FRAMES[self._anim_i % len(SWEEP_FRAMES)]
        self._anim_i += 1

    def _notify(self, title: str, message: str) -> None:
        import subprocess

        def esc(s: str) -> str:
            return (s or "").replace("\\", "\\\\").replace('"', '\\"')
        script = f'display notification "{esc(message)}" with title "{esc(title)}"'
        try:
            subprocess.run(["osascript", "-e", script], check=False)
        except Exception:
            pass

    def _show_window(self, text: str, title: str) -> None:
        from PyObjCTools.AppHelper import callAfter
        from . import output_window
        callAfter(output_window.show_text, text, title)

    def _bar_color(self, free_mb: int):
        from AppKit import NSColor
        if free_mb < RED_GB * 1024:
            return NSColor.systemRedColor()
        if free_mb < ORANGE_GB * 1024:
            return NSColor.systemOrangeColor()
        return NSColor.labelColor()

    def _set_bar(self, text: str, free_mb: int) -> None:
        """Ustaw tytuł w pasku z kolorem progowym (atrybutowany tytuł przycisku)."""
        self.title = text   # zwykły tytuł — spójność rumps + fallback
        try:
            button = self._nsapp.nsstatusitem.button()
            if button is None:
                return
            from AppKit import NSAttributedString, NSForegroundColorAttributeName
            attrs = {NSForegroundColorAttributeName: self._bar_color(free_mb)}
            button.setAttributedTitle_(
                NSAttributedString.alloc().initWithString_attributes_(text, attrs))
        except Exception:
            pass

    def refresh(self, *_args) -> None:
        if self._busy:
            return
        free_mb, used_mb = engine.disk_free_used_mb()
        self._set_bar(engine.human0(free_mb), free_mb)
        self.status_item.title = (
            f"Wolne: {engine.human(free_mb)}   ·   Zajęte: {engine.human(used_mb)}")
        st = engine.read_state()
        if st.get("last_run_human"):
            self.last_item.title = (
                f"Ostatnie sprzątanie: {st['last_run_human']}, "
                f"odzyskano {engine.human(st.get('last_freed_mb', 0))}")
        else:
            self.last_item.title = "Ostatnie sprzątanie: —"
        self._maybe_low_space_note(free_mb)

    def _maybe_low_space_note(self, free_mb: int) -> None:
        level = "low" if free_mb < RED_GB * 1024 else "ok"
        try:
            prev = open(engine.NOTIFY_STATE).read().strip()
        except OSError:
            prev = ""
        if level != prev:
            if level == "low":
                self._notify("Miotła", f"Zostało {engine.human0(free_mb)} — czas na sprzątanie.")
            try:
                os.makedirs(engine.CACHE, exist_ok=True)
                with open(engine.NOTIFY_STATE, "w") as f:
                    f.write(level)
            except OSError:
                pass

    # ----------------------------------------------------------- actions
    def quick_clean(self, _=None) -> None:
        if self._busy:
            return
        self._set_busy(True)

        def work() -> None:
            rc, out, summ = engine.run_auto(dry_run=False)
            freed = summ.get("freed_mb", "0")
            self._set_busy(False)
            if str(summ.get("status")) == "locked":
                self._notify("Miotła", "Sprzątanie już trwa.")
            else:
                self._notify("Miotła", f"Odzyskano {engine.human(freed)}")
            self._show_window(out, "Miotła — sprzątanie")

        threading.Thread(target=work, daemon=True).start()

    def preview(self, _=None) -> None:
        if self._busy:
            return
        self._set_busy(True)

        def work() -> None:
            _rc, out, _summ = engine.run_auto(dry_run=True)
            self._set_busy(False)
            self._show_window(out, "Miotła — podgląd (nic nie usunięto)")

        threading.Thread(target=work, daemon=True).start()

    def full_clean_window(self, _=None) -> None:
        if self._busy:
            return
        self._set_busy(True)

        def work() -> None:
            cats = [c for c in engine.scan() if c.get("total_mb", 0) > 0]
            self._set_busy(False)
            from PyObjCTools.AppHelper import callAfter
            from . import clean_window
            callAfter(clean_window.show_clean, self, cats)

        threading.Thread(target=work, daemon=True).start()

    def run_selected_clean(self, paths) -> None:
        """Wywoływane przez okno „Pełne sprzątanie" — usuwa zaznaczone pozycje.

        Rozdziela ścieżki w $HOME (clean_items) od pozycji sudo (clean_sudo
        z jednym natywnym pytaniem o hasło)."""
        real = [p for p in paths if not str(p).startswith("sudo:")]
        sudo = [p for p in paths if str(p).startswith("sudo:")]
        if not (real or sudo) or self._busy:
            return
        self._set_busy(True)

        def work() -> None:
            out = ""
            freed = 0
            if real:
                _rc, o, summ = engine.clean_items(real)
                out += o
                try:
                    freed = int(summ.get("freed_mb", 0))
                except (TypeError, ValueError):
                    freed = 0
            if sudo:
                # osascript pokaże natywne okno hasła — uruchom na głównym wątku
                from PyObjCTools.AppHelper import callAfter
                callAfter(self._run_sudo_then_finish, sudo, out, freed)
                return
            self._finish_clean(out, freed)

        threading.Thread(target=work, daemon=True).start()

    def _run_sudo_then_finish(self, sudo, out, freed) -> None:
        def work() -> None:
            _rc, so = engine.clean_sudo(list(sudo))
            full = (out + "\n\n── sudo ──\n" + so) if out else ("── sudo ──\n" + so)
            self._finish_clean(full, freed)
        threading.Thread(target=work, daemon=True).start()

    def _finish_clean(self, out, freed) -> None:
        self._set_busy(False)
        if freed:
            self._notify("Miotła", f"Odzyskano {engine.human(freed)}")
        else:
            self._notify("Miotła", "Sprzątanie zakończone")
        self._show_window(out or "Gotowe.", "Miotła — pełne sprzątanie")
        from PyObjCTools.AppHelper import callAfter
        callAfter(self.refresh)

    def full_terminal(self, _=None) -> None:
        engine.open_interactive_in_terminal()

    def open_log(self, _=None) -> None:
        log = engine.latest_log()
        if log:
            engine.open_path(log)
        else:
            self._notify("Miotła", "Brak logów — uruchom najpierw sprzątanie.")

    def about(self, _=None) -> None:
        text = (
            f"Miotła {__version__}\n\n"
            "Bezpieczne sprzątanie Maca dewelopera z paska menu.\n"
            "Apka wywołuje skrypt `miotla` i pokazuje wynik w oknie.\n\n"
            f"Skrypt: {engine.script_path()}\n"
            "Autor: Rafał Gawlik · github.com/rafalgawlik/miotla\n")
        self._show_window(text, "O Miotle")

    # ----------------------------------------------------------- timer
    def _tick(self, _timer) -> None:
        self.refresh()


def main() -> None:
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ("-v", "--version"):
        print(f"miotla-app {__version__}")
        return
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print("Miotła — apka paska menu. Uruchom bez argumentów, by pokazać ikonę 🧹.")
        return

    # Apka tylko w pasku menu (bez ikony w Docku).
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
        NSApplication.sharedApplication().setActivationPolicy_(
            NSApplicationActivationPolicyAccessory)
    except Exception:
        pass

    _set_app_name()
    MiotlaApp().run()
