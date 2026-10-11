"""Okno „Pełne sprzątanie" — kategorie z pozycjami i checkboxami (przewijane).

Każda kategoria to nagłówek z checkboxem (zaznacza/odznacza wszystkie swoje
pozycje) i wcięte pozycje z osobnymi checkboxami. Zaznaczasz dokładnie, co
usunąć, i klikasz „Sprzątaj zaznaczone". Nic nie znika do kliknięcia.
Bezpieczne cache są domyślnie zaznaczone; groźniejsze (emulatory, Archives,
cały cache Gradle, Kosz) — odznaczone i z ⚠.
"""
from __future__ import annotations

import objc
from AppKit import (
    NSApplication,
    NSBackingStoreBuffered,
    NSBezelStyleRounded,
    NSButton,
    NSFont,
    NSMakeRect,
    NSScrollView,
    NSSwitchButton,
    NSTextField,
    NSView,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskResizable,
    NSWindowStyleMaskTitled,
)
from Foundation import NSObject

from . import engine

_KEEP: list = []     # referencje do okien/kontrolerów

_SAFE_ON = {"npm_yarn", "xcode_derived", "xcode_caches", "electron", "dart", "cache_dir"}
_W = 560
_MAX_H = 640
_ROW = 24


class _FlippedView(NSView):
    def isFlipped(self):
        return True


def _label(text, x, y, w, *, bold=False):
    lbl = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, 18))
    lbl.setStringValue_(text)
    lbl.setBezeled_(False)
    lbl.setDrawsBackground_(False)
    lbl.setEditable_(False)
    lbl.setSelectable_(False)
    lbl.setFont_(NSFont.boldSystemFontOfSize_(12) if bold else NSFont.systemFontOfSize_(12))
    return lbl


class _CleanController(NSObject):
    def toggleGroup_(self, sender):
        for g in self.groups:
            if g["master"] is sender:
                for _p, box in g["items"]:
                    box.setState_(sender.state())
                return

    def clean_(self, _sender):
        paths = [p for g in self.groups for (p, box) in g["items"] if box.state()]
        self.window.close()
        if paths and self.app is not None:
            self.app.run_selected_clean(paths)

    def cancel_(self, _sender):
        self.window.close()


def show_clean(app, categories) -> None:
    categories = [c for c in (categories or []) if c.get("items")]
    if not categories:
        from . import output_window
        output_window.show_text(
            "Nie znaleziono nic do wyczyszczenia.\n"
            "(Szybkie sprzątanie zajmuje się bieżącymi cache na co dzień.)",
            "Miotła — pełne sprzątanie")
        return

    ctrl = _CleanController.alloc().init()
    ctrl.app = app
    ctrl.groups = []

    # dokument (przewijana lista), układany od góry (widok „flipped")
    doc_w = _W - 32
    doc = _FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, doc_w, 10))
    y = 6
    for cat in categories:
        token = cat.get("token", "")
        default_on = token in _SAFE_ON
        master = NSButton.alloc().initWithFrame_(NSMakeRect(8, y, doc_w - 16, 22))
        master.setButtonType_(NSSwitchButton)
        warn = cat.get("warn") or ""
        mt = f"{cat.get('label', token)}   ·   {engine.human(cat.get('total_mb', 0))}"
        if warn:
            mt += "   ⚠"
            master.setToolTip_(warn)
        master.setTitle_(mt)
        master.setFont_(NSFont.boldSystemFontOfSize_(12))
        master.setState_(1 if default_on else 0)
        master.setTarget_(ctrl)
        master.setAction_(objc.selector(ctrl.toggleGroup_, signature=b"v@:@"))
        doc.addSubview_(master)
        y += _ROW

        items = []
        for it in cat.get("items", []):
            box = NSButton.alloc().initWithFrame_(NSMakeRect(32, y, doc_w - 40, 20))
            box.setButtonType_(NSSwitchButton)
            box.setTitle_(f"{it.get('desc', '')}   ·   {engine.human(it.get('mb', 0))}")
            box.setState_(1 if default_on else 0)
            doc.addSubview_(box)
            items.append((it.get("path", ""), box))
            y += _ROW
        y += 8
        ctrl.groups.append({"master": master, "items": items})

    doc_h = y + 4
    doc.setFrameSize_((doc_w, doc_h))

    # okno: nagłówek (góra) + lista (środek, przewijana) + przyciski (dół)
    header_h, footer_h = 40, 52
    win_h = min(_MAX_H, header_h + footer_h + doc_h)
    rect = NSMakeRect(0, 0, _W, win_h)
    style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskResizable
    win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        rect, style, NSBackingStoreBuffered, False)
    win.setTitle_("Miotła — pełne sprzątanie")
    win.setReleasedWhenClosed_(False)
    ctrl.window = win

    view = NSView.alloc().initWithFrame_(rect)
    view.addSubview_(_label(
        "Zaznacz, co usunąć — nic nie zniknie, dopóki nie klikniesz Sprzątaj.",
        16, win_h - 28, _W - 32, bold=True))

    scroll = NSScrollView.alloc().initWithFrame_(
        NSMakeRect(12, footer_h, _W - 24, win_h - header_h - footer_h))
    scroll.setHasVerticalScroller_(True)
    scroll.setAutohidesScrollers_(True)
    scroll.setDrawsBackground_(False)
    scroll.setDocumentView_(doc)
    view.addSubview_(scroll)

    clean_btn = NSButton.alloc().initWithFrame_(NSMakeRect(_W - 205, 12, 190, 32))
    clean_btn.setTitle_("Sprzątaj zaznaczone")
    clean_btn.setBezelStyle_(NSBezelStyleRounded)
    clean_btn.setKeyEquivalent_("\r")
    clean_btn.setTarget_(ctrl)
    clean_btn.setAction_(objc.selector(ctrl.clean_, signature=b"v@:@"))
    view.addSubview_(clean_btn)

    cancel_btn = NSButton.alloc().initWithFrame_(NSMakeRect(16, 12, 100, 32))
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
