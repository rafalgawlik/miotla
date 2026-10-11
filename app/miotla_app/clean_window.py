"""Okno „Pełne sprzątanie" — lista kategorii z rozmiarami i checkboxami.

Zaznaczasz, co usunąć, i klikasz „Sprzątaj zaznaczone". Nic nie znika, dopóki
nie klikniesz. Groźne kategorie (cały cache Gradle, Kosz) są domyślnie
odznaczone i oznaczone ⚠.
"""
from __future__ import annotations

import objc
from AppKit import (
    NSApplication,
    NSBackingStoreBuffered,
    NSButton,
    NSBezelStyleRounded,
    NSColor,
    NSFont,
    NSMakeRect,
    NSSwitchButton,
    NSTextField,
    NSView,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskTitled,
)
from Foundation import NSObject

from . import engine

_KEEP: list = []     # referencje do okien/kontrolerów (żeby GC nie zamknął)

_DEFAULT_OFF = {"gradle_all", "trash"}   # groźniejsze — domyślnie odznaczone
_ROW_H = 30
_PAD = 18
_W = 460


def _label(text, x, y, w, *, bold=False, color=None, size=12.0):
    lbl = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, 18))
    lbl.setStringValue_(text)
    lbl.setBezeled_(False)
    lbl.setDrawsBackground_(False)
    lbl.setEditable_(False)
    lbl.setSelectable_(False)
    lbl.setFont_(NSFont.boldSystemFontOfSize_(size) if bold else NSFont.systemFontOfSize_(size))
    if color is not None:
        lbl.setTextColor_(color)
    return lbl


class _CleanController(NSObject):
    def clean_(self, _sender):
        tokens = [tok for tok, box in self.boxes if box.state()]
        self.window.close()
        if tokens and self.app is not None:
            self.app.run_selected_clean(tokens)

    def cancel_(self, _sender):
        self.window.close()


def show_clean(app, categories) -> None:
    if not categories:
        from . import output_window
        output_window.show_text(
            "Nie znaleziono nic do wyczyszczenia w kategoriach pełnego sprzątania.\n"
            "(Szybkie sprzątanie zajmuje się bieżącymi cache na co dzień.)",
            "Miotła — pełne sprzątanie")
        return

    n = len(categories)
    content_h = _PAD + 44 + n * _ROW_H + 52     # nagłówek + wiersze + przyciski
    rect = NSMakeRect(0, 0, _W, content_h)
    style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable
    win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        rect, style, NSBackingStoreBuffered, False)
    win.setTitle_("Miotła — pełne sprzątanie")
    win.setReleasedWhenClosed_(False)

    view = NSView.alloc().initWithFrame_(rect)

    # nagłówek
    view.addSubview_(_label(
        "Zaznacz, co wyczyścić — nic nie zniknie, dopóki nie klikniesz Sprzątaj.",
        _PAD, content_h - 30, _W - 2 * _PAD, bold=True))

    ctrl = _CleanController.alloc().init()
    ctrl.window = win
    ctrl.app = app
    ctrl.boxes = []

    y = content_h - 44
    for cat in categories:
        y -= _ROW_H
        token = cat.get("token", "")
        size = engine.human(cat.get("total_mb", 0))
        warn = cat.get("warn") or ""
        title = f"{cat.get('label', token)}   ·   {size}"
        if warn:
            title += "   ⚠"
        box = NSButton.alloc().initWithFrame_(NSMakeRect(_PAD, y, _W - 2 * _PAD, 22))
        box.setButtonType_(NSSwitchButton)
        box.setTitle_(title)
        box.setState_(0 if token in _DEFAULT_OFF else 1)
        if warn:
            box.setToolTip_(warn)
        view.addSubview_(box)
        ctrl.boxes.append((token, box))

    # przyciski
    clean_btn = NSButton.alloc().initWithFrame_(NSMakeRect(_W - 200, 12, 185, 32))
    clean_btn.setTitle_("Sprzątaj zaznaczone")
    clean_btn.setBezelStyle_(NSBezelStyleRounded)
    clean_btn.setKeyEquivalent_("\r")
    clean_btn.setTarget_(ctrl)
    clean_btn.setAction_(objc.selector(ctrl.clean_, signature=b"v@:@"))
    view.addSubview_(clean_btn)

    cancel_btn = NSButton.alloc().initWithFrame_(NSMakeRect(_PAD, 12, 100, 32))
    cancel_btn.setTitle_("Anuluj")
    cancel_btn.setBezelStyle_(NSBezelStyleRounded)
    cancel_btn.setKeyEquivalent_("\x1b")
    cancel_btn.setTarget_(ctrl)
    cancel_btn.setAction_(objc.selector(ctrl.cancel_, signature=b"v@:@"))
    view.addSubview_(cancel_btn)

    win.setContentView_(view)
    win.center()
    NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
    win.makeKeyAndOrderFront_(None)

    _KEEP.append(win)
    _KEEP.append(ctrl)
    if len(_KEEP) > 12:
        del _KEEP[:2]
