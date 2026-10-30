"""Miotła — menu bar app (rumps): icon + free space, cleanup shown in a window."""
from __future__ import annotations

import os
import threading

import rumps

from . import __version__, engine

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
ICON_PATH = os.path.join(_ASSETS, "broom-template.png")
APP_ICON_PATH = os.path.join(_ASSETS, "app_icon.png")   # kolorowa ikona Docka/Cmd-Tab
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
            quit_button="Quit",
        )
        global _APP
        _APP = self
        _set_app_name()

        self._busy = False
        self._anim_timer = None
        self._anim_i = 0

        self.status_item = rumps.MenuItem("Free: …")
        self.purgeable_item = rumps.MenuItem("Purgeable: —")
        self.quick_item = rumps.MenuItem("Quick cleanup", callback=self.quick_clean)
        self.preview_item = rumps.MenuItem("Preview (what would be removed)", callback=self.preview)
        self.full_item = rumps.MenuItem("Full cleanup…", callback=self.full_clean_window)
        self.last_item = rumps.MenuItem("Last cleanup: —")
        self.log_item = rumps.MenuItem("Open log", callback=self.open_log)

        self.menu = [
            self.status_item,
            self.purgeable_item,
            None,
            self.quick_item,
            self.preview_item,
            self.full_item,
            None,
            self.last_item,
            self.log_item,
            rumps.MenuItem("About Miotła", callback=self.about),
        ]

        self.refresh()
        from . import notifications
        notifications.setup()                        # ask for notification permission
        self.timer = rumps.Timer(self._tick, 300)   # every 5 min
        self.timer.start()

    # ---------------------------------------------------------------- UI
    def _apply_busy(self, on: bool) -> None:
        if self._anim_timer is not None:
            self._anim_timer.stop()
            self._anim_timer = None
        if on and SWEEP_FRAMES:
            self.title = "cleaning…"
            self._anim_i = 0
            self._anim_timer = rumps.Timer(self._anim_tick, 0.09)
            self._anim_timer.start()
        elif on:
            self.title = "cleaning…"
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

    def _bar_color(self, free_mb: int):
        from AppKit import NSColor
        if free_mb < RED_GB * 1024:
            return NSColor.systemRedColor()
        if free_mb < ORANGE_GB * 1024:
            return NSColor.systemOrangeColor()
        return NSColor.labelColor()

    def _set_bar(self, text: str, free_mb: int) -> None:
        """Set the menu bar title with a threshold color (attributed button title)."""
        self.title = text
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

    def _notify(self, title: str, message: str) -> None:
        from . import notifications
        notifications.notify(message or title)

    def _show_window(self, text: str, title: str, links=None) -> None:
        from PyObjCTools.AppHelper import callAfter
        from . import output_window
        callAfter(output_window.show_text, text, title, links)

    def refresh(self, *_args) -> None:
        if self._busy:
            return
        free_mb, used_mb = engine.disk_free_used_mb()
        self._set_bar(engine.human0(free_mb), free_mb)
        self.status_item.title = (
            f"Free: {engine.human(free_mb)}   ·   Used: {engine.human(used_mb)}")
        purgeable_mb = engine.disk_purgeable_mb()
        self.purgeable_item.title = (
            f"+ {engine.human(purgeable_mb)} purgeable (macOS frees it when needed)"
            if purgeable_mb >= 1024 else "Purgeable: —")
        st = engine.read_state()
        if st.get("last_run_human"):
            self.last_item.title = (
                f"Last cleanup: {st['last_run_human']}, "
                f"recovered {engine.human(st.get('last_freed_mb', 0))}")
        else:
            self.last_item.title = "Last cleanup: —"
        self._maybe_low_space_note(free_mb)

    def _maybe_low_space_note(self, free_mb: int) -> None:
        level = "low" if free_mb < RED_GB * 1024 else "ok"
        try:
            prev = open(engine.NOTIFY_STATE).read().strip()
        except OSError:
            prev = ""
        if level != prev:
            if level == "low":
                self._notify("Miotła", f"{engine.human0(free_mb)} left — time to clean up.")
            try:
                os.makedirs(engine.CACHE, exist_ok=True)
                with open(engine.NOTIFY_STATE, "w") as f:
                    f.write(level)
            except OSError:
                pass

    def _summary(self, summ: dict, title_line: str, dry: bool) -> str:
        freed = summ.get("freed_mb", 0)
        fa = summ.get("free_after_mb", 0)
        sk = summ.get("skipped")
        if isinstance(sk, list):
            sk = ", ".join(sk)
        lines = [title_line, ""]
        if dry:
            lines.append(f"Would free about {engine.human(freed)}. Nothing was removed.")
            lines.append("Use “Full cleanup…” to choose exactly what to remove.")
        else:
            lines.append(f"Recovered: {engine.human(freed)}")
        if fa:
            lines.append(f"Free space: {engine.human(fa)}")
        if sk and sk not in ("none", ""):
            lines.append(f"Skipped: {sk}")
        return "\n".join(lines)

    # ----------------------------------------------------------- actions
    def quick_clean(self, _=None) -> None:
        if self._busy:
            return
        self._set_busy(True)

        def work() -> None:
            _rc, _out, summ = engine.run_auto(dry_run=False)
            self._set_busy(False)
            if str(summ.get("status")) == "locked":
                self._notify("Miotła", "Cleanup already running.")
                return
            freed = summ.get("freed_mb", 0)
            self._notify("Miotła",
                         f"Recovered {engine.human(freed)}" if freed else "Nothing to clean.")
            self._show_window(self._summary(summ, "Quick cleanup finished.", dry=False),
                              "Miotła — quick cleanup")

        threading.Thread(target=work, daemon=True).start()

    def preview(self, _=None) -> None:
        if self._busy:
            return
        self._set_busy(True)

        def work() -> None:
            _rc, _out, summ = engine.run_auto(dry_run=True)
            self._set_busy(False)
            self._show_window(self._summary(summ, "Preview — quick cleanup", dry=True),
                              "Miotła — preview (nothing removed)")

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

    def run_selected_clean(self, items) -> None:
        """Called by the full-cleanup window. `items` = list of (path, desc)."""
        real = [(p, d) for (p, d) in items if not str(p).startswith("sudo:")]
        sudo = [(p, d) for (p, d) in items if str(p).startswith("sudo:")]
        if not (real or sudo) or self._busy:
            return
        self._set_busy(True)
        removed = [d for (_p, d) in items]

        def work() -> None:
            freed = 0
            if real:
                _rc, _o, summ = engine.clean_items([p for (p, _d) in real])
                try:
                    freed = int(summ.get("freed_mb", 0))
                except (TypeError, ValueError):
                    freed = 0
            if sudo:
                from PyObjCTools.AppHelper import callAfter
                callAfter(self._run_sudo_then_finish, [p for (p, _d) in sudo], removed, freed)
                return
            self._finish_full(removed, freed, None)

        threading.Thread(target=work, daemon=True).start()

    def _run_sudo_then_finish(self, sudo_tokens, removed, freed) -> None:
        def work() -> None:
            _rc, so = engine.clean_sudo(list(sudo_tokens))
            self._finish_full(removed, freed, so)
        threading.Thread(target=work, daemon=True).start()

    def _finish_full(self, removed, freed, sudo_out) -> None:
        from PyObjCTools.AppHelper import callAfter
        self._set_busy(False)
        self._notify("Miotła",
                     f"Recovered {engine.human(freed)}" if freed else "Cleanup finished.")
        lines = ["Full cleanup finished.", "",
                 f"Recovered: {engine.human(freed)}"
                 + ("  (plus system items)" if sudo_out is not None else ""),
                 "", "Removed:"]
        lines += [f"  • {d}" for d in removed]
        if sudo_out is not None:
            lines += ["", "── system (sudo) ──", (sudo_out.strip() or "done")]
        self._show_window("\n".join(lines), "Miotła — full cleanup")
        callAfter(self.refresh)

    def open_log(self, _=None) -> None:
        log = engine.latest_log()
        if log:
            engine.open_path(log)
        else:
            self._notify("Miotła", "No logs yet — run a cleanup first.")

    def about(self, _=None) -> None:
        links = [
            ("rafalgawlik.com", "https://rafalgawlik.com"),
            ("GitHub — @rafalgawlik", "https://github.com/rafalgawlik"),
            ("Repository — github.com/rafalgawlik/miotla", "https://github.com/rafalgawlik/miotla"),
            ("Website — rafalgawlik.github.io/miotla", "https://rafalgawlik.github.io/miotla/"),
        ]
        text = (
            f"Miotła {__version__}\n\n"
            "Safe cleanup for a developer's Mac, right from the menu bar.\n"
            "See free space and reclaim it with one click — in a window, not a terminal.\n\n"
            f"Engine script: {engine.script_path()}\n"
            "© 2026 Rafał Gawlik · MIT License")
        self._show_window(text, "About Miotła", links=links)

    # ----------------------------------------------------------- timer
    def _tick(self, _timer) -> None:
        self.refresh()


def main() -> None:
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ("-v", "--version"):
        print(f"miotla-app {__version__}")
        return
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print("Miotła — menu bar app. Run with no arguments to show the 🧹 icon.")
        return

    # Single instance is enforced by LSMultipleInstancesProhibited in the
    # app bundle's Info.plist, so no in-process guard here.
    _set_app_name()
    MiotlaApp().run()
