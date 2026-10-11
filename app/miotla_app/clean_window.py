"""Okno „Pełne sprzątanie" — kategorie z pozycjami i checkboxami (przewijane).

Każda kategoria ma nagłówek-checkbox (zaznacza/odznacza swoje pozycje) i wcięte
pozycje per sztuka. Na dole licznik „Zaznaczono: X" aktualizuje się na żywo,
w nagłówku „Zaznacz/odznacz wszystko". Nic nie znika do kliknięcia Sprzątaj.
Bezpieczne cache są domyślnie zaznaczone; groźne (emulatory, Archives, cały
cache Gradle, Kosz, sudo) — odznaczone i z ⚠. Pozycje „(sudo)" (snapshoty
Time Machine, sleepimage) usuwa się z natywnym pytaniem o hasło.
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

_KEEP: list = []

_SAFE_ON = {"npm_yarn", "xcode_derived", "xcode_caches", "electron", "dart", "cache_dir"}
_W = 580
_MAX_H = 660
_ROW = 24


class _FlippedView(NSView):
    def isFlipped(self):
        return True


def _text(s, x, y, w, *, bold=False, align_right=False):
    lbl = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, 18))
    lbl.setStringValue_(s)
    lbl.setBezeled_(False)
    lbl.setDrawsBackground_(False)
    lbl.setEditable_(False)
    lbl.setSelectable_(False)
    lbl.setFont_(NSFont.boldSystemFontOfSize_(12) if bold else NSFont.systemFontOfSize_(12))
    if align_right:
        lbl.setAlignment_(1)   # NSTextAlignmentRight
    return lbl


def _size_txt(path, mb) -> str:
    if mb and int(mb) > 0:
        return engine.human(mb)
    if str(path).startswith("sudo:"):
        return "(sudo)"
    return engine.human(0)


class _CleanController(NSObject):
    def _recount(self):
        total = sum(int(mb) for g in self.groups for (_p, b, mb) in g["items"] if b.state())
        self.total_label.setStringValue_(f"Zaznaczono: {engine.human(total)}")

    def recount_(self, _sender):
        self._recount()

    def selectGroup_(self, sender):
        for g in self.groups:
            if g["master"] is sender:
                for (_p, b, _mb) in g["items"]:
                    b.setState_(sender.state())
                break
        self._recount()

    def selectAll_(self, _sender):
        boxes = [b for g in self.groups for (_p, b, _mb) in g["items"]]
        target = 0 if boxes and all(b.state() for b in boxes) else 1
        for g in self.groups:
            g["master"].setState_(target)
            for (_p, b, _mb) in g["items"]:
                b.setState_(target)
        self._recount()

    def clean_(self, _sender):
        paths = [p for g in self.groups for (p, b, _mb) in g["items"] if b.state()]
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

    sel_group = objc.selector(ctrl.selectGroup_, signature=b"v@:@")
    recount = objc.selector(ctrl.recount_, signature=b"v@:@")

    doc_w = _W - 32
    doc = _FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, doc_w, 10))
    y = 6
    for cat in categories:
        token = cat.get("token", "")
        default_on = token in _SAFE_ON
        warn = cat.get("warn") or ""
        master = NSButton.alloc().initWithFrame_(NSMakeRect(8, y, doc_w - 16, 22))
        master.setButtonType_(NSSwitchButton)
        mt = f"{cat.get('label', token)}   ·   {engine.human(cat.get('total_mb', 0))}"
        if warn:
            mt += "   ⚠"
            master.setToolTip_(warn)
        master.setTitle_(mt)
        master.setFont_(NSFont.boldSystemFontOfSize_(12))
        master.setState_(1 if default_on else 0)
        master.setTarget_(ctrl)
        master.setAction_(sel_group)
        doc.addSubview_(master)
        y += _ROW

        items = []
        for it in cat.get("items", []):
            path = it.get("path", "")
            mb = it.get("mb", 0) or 0
            box = NSButton.alloc().initWithFrame_(NSMakeRect(32, y, doc_w - 40, 20))
            box.setButtonType_(NSSwitchButton)
            box.setTitle_(f"{it.get('desc', '')}   ·   {_size_txt(path, mb)}")
            box.setState_(1 if default_on else 0)
            box.setTarget_(ctrl)
            box.setAction_(recount)
            doc.addSubview_(box)
            items.append((path, box, int(mb)))
            y += _ROW
        y += 8
        ctrl.groups.append({"master": master, "items": items})

    doc_h = y + 4
    doc.setFrameSize_((doc_w, doc_h))

    header_h, footer_h = 44, 52
    win_h = min(_MAX_H, header_h + footer_h + doc_h)
    rect = NSMakeRect(0, 0, _W, win_h)
    style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskResizable
    win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        rect, style, NSBackingStoreBuffered, False)
    win.setTitle_("Miotła — pełne sprzątanie")
    win.setReleasedWhenClosed_(False)
    ctrl.window = win

    view = NSView.alloc().initWithFrame_(rect)

    # nagłówek: tytuł + „zaznacz/odznacz wszystko"
    view.addSubview_(_text("Zaznacz, co usunąć — nic nie zniknie do kliknięcia Sprzątaj.",
                           16, win_h - 30, _W - 210, bold=True))
    all_btn = NSButton.alloc().initWithFrame_(NSMakeRect(_W - 190, win_h - 36, 174, 26))
    all_btn.setTitle_("Zaznacz / odznacz wszystko")
    all_btn.setBezelStyle_(NSBezelStyleRounded)
    all_btn.setFont_(NSFont.systemFontOfSize_(11))
    all_btn.setTarget_(ctrl)
    all_btn.setAction_(objc.selector(ctrl.selectAll_, signature=b"v@:@"))
    view.addSubview_(all_btn)

    # lista (przewijana)
    scroll = NSScrollView.alloc().initWithFrame_(
        NSMakeRect(12, footer_h, _W - 24, win_h - header_h - footer_h))
    scroll.setHasVerticalScroller_(True)
    scroll.setAutohidesScrollers_(True)
    scroll.setDrawsBackground_(False)
    scroll.setDocumentView_(doc)
    view.addSubview_(scroll)

    # stopka: Anuluj · licznik · Sprzątaj
    cancel_btn = NSButton.alloc().initWithFrame_(NSMakeRect(16, 12, 100, 32))
    cancel_btn.setTitle_("Anuluj")
    cancel_btn.setBezelStyle_(NSBezelStyleRounded)
    cancel_btn.setKeyEquivalent_("\x1b")
    cancel_btn.setTarget_(ctrl)
    cancel_btn.setAction_(objc.selector(ctrl.cancel_, signature=b"v@:@"))
    view.addSubview_(cancel_btn)

    ctrl.total_label = _text("Zaznaczono: 0 MB", 126, 20, 180)
    view.addSubview_(ctrl.total_label)

    clean_btn = NSButton.alloc().initWithFrame_(NSMakeRect(_W - 205, 12, 190, 32))
    clean_btn.setTitle_("Sprzątaj zaznaczone")
    clean_btn.setBezelStyle_(NSBezelStyleRounded)
    clean_btn.setKeyEquivalent_("\r")
    clean_btn.setTarget_(ctrl)
    clean_btn.setAction_(objc.selector(ctrl.clean_, signature=b"v@:@"))
    view.addSubview_(clean_btn)

    ctrl._recount()

    win.setContentView_(view)
    win.center()
    NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
    win.makeKeyAndOrderFront_(None)

    _KEEP.append(win)
    _KEEP.append(ctrl)
    if len(_KEEP) > 12:
        del _KEEP[:2]
