"""Full-cleanup window — categories with items and checkboxes (scrollable).

Each category has a header checkbox (toggles all its items) and indented
per-item checkboxes. A live "Selected: X" counter sits at the bottom, with
"Select / deselect all" in the header. Nothing is removed until you click Clean.
Safe caches are checked by default; riskier ones (emulators, Archives, the whole
Gradle cache, Trash, sudo) are unchecked and marked ⚠. The "(sudo)" items
(Time Machine snapshots, sleepimage) are removed with a native password prompt.
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


def _text(s, x, y, w, *, bold=False):
    lbl = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, 18))
    lbl.setStringValue_(s)
    lbl.setBezeled_(False)
    lbl.setDrawsBackground_(False)
    lbl.setEditable_(False)
    lbl.setSelectable_(False)
    lbl.setFont_(NSFont.boldSystemFontOfSize_(12) if bold else NSFont.systemFontOfSize_(12))
    return lbl


def _size_txt(path, mb) -> str:
    if mb and int(mb) > 0:
        return engine.human(mb)
    if str(path).startswith("sudo:"):
        return "(sudo)"
    return engine.human(0)


class _CleanController(NSObject):
    def _recount(self):
        total = sum(mb for g in self.groups for (_p, b, mb, _d) in g["items"] if b.state())
        self.total_label.setStringValue_(f"Selected: {engine.human(total)}")

    def recount_(self, _sender):
        self._recount()

    def selectGroup_(self, sender):
        for g in self.groups:
            if g["master"] is sender:
                for (_p, b, _mb, _d) in g["items"]:
                    b.setState_(sender.state())
                break
        self._recount()

    def selectAll_(self, _sender):
        boxes = [b for g in self.groups for (_p, b, _mb, _d) in g["items"]]
        target = 0 if boxes and all(b.state() for b in boxes) else 1
        for g in self.groups:
            g["master"].setState_(target)
            for (_p, b, _mb, _d) in g["items"]:
                b.setState_(target)
        self._recount()

    def clean_(self, _sender):
        items = [(p, d) for g in self.groups for (p, b, _mb, d) in g["items"] if b.state()]
        self.window.close()
        if items and self.app is not None:
            self.app.run_selected_clean(items)

    def cancel_(self, _sender):
        self.window.close()


def show_clean(app, categories) -> None:
    categories = [c for c in (categories or []) if c.get("items")]
    if not categories:
        from . import output_window
        output_window.show_text(
            "Nothing to clean was found.\n"
            "(Quick cleanup takes care of everyday caches.)",
            "Miotła — full cleanup")
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
            mb = int(it.get("mb", 0) or 0)
            desc = it.get("desc", "")
            box = NSButton.alloc().initWithFrame_(NSMakeRect(32, y, doc_w - 40, 20))
            box.setButtonType_(NSSwitchButton)
            box.setTitle_(f"{desc}   ·   {_size_txt(path, mb)}")
            box.setState_(1 if default_on else 0)
            box.setTarget_(ctrl)
            box.setAction_(recount)
            doc.addSubview_(box)
            items.append((path, box, mb, desc))
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
    win.setTitle_("Miotła — full cleanup")
    win.setReleasedWhenClosed_(False)
    ctrl.window = win

    view = NSView.alloc().initWithFrame_(rect)

    view.addSubview_(_text("Select what to remove — nothing is deleted until you click Clean.",
                           16, win_h - 30, _W - 210, bold=True))
    all_btn = NSButton.alloc().initWithFrame_(NSMakeRect(_W - 190, win_h - 36, 174, 26))
    all_btn.setTitle_("Select / deselect all")
    all_btn.setBezelStyle_(NSBezelStyleRounded)
    all_btn.setFont_(NSFont.systemFontOfSize_(11))
    all_btn.setTarget_(ctrl)
    all_btn.setAction_(objc.selector(ctrl.selectAll_, signature=b"v@:@"))
    view.addSubview_(all_btn)

    scroll = NSScrollView.alloc().initWithFrame_(
        NSMakeRect(12, footer_h, _W - 24, win_h - header_h - footer_h))
    scroll.setHasVerticalScroller_(True)
    scroll.setAutohidesScrollers_(True)
    scroll.setDrawsBackground_(False)
    scroll.setDocumentView_(doc)
    view.addSubview_(scroll)

    cancel_btn = NSButton.alloc().initWithFrame_(NSMakeRect(16, 12, 100, 32))
    cancel_btn.setTitle_("Cancel")
    cancel_btn.setBezelStyle_(NSBezelStyleRounded)
    cancel_btn.setKeyEquivalent_("\x1b")
    cancel_btn.setTarget_(ctrl)
    cancel_btn.setAction_(objc.selector(ctrl.cancel_, signature=b"v@:@"))
    view.addSubview_(cancel_btn)

    ctrl.total_label = _text("Selected: 0 MB", 126, 20, 180)
    view.addSubview_(ctrl.total_label)

    clean_btn = NSButton.alloc().initWithFrame_(NSMakeRect(_W - 175, 12, 160, 32))
    clean_btn.setTitle_("Clean selected")
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
