"""Native scrollable, monospaced text window — cleanup/preview results and the
About box are shown here instead of a terminal.

Everything must run on the main thread (NSWindow). Window references are kept in
the module so the GC does not close them. `links` adds clickable URLs (About).
"""
from __future__ import annotations

from AppKit import (
    NSApplication,
    NSAttributedString,
    NSBackingStoreBuffered,
    NSColor,
    NSFont,
    NSFontAttributeName,
    NSForegroundColorAttributeName,
    NSLinkAttributeName,
    NSMutableAttributedString,
    NSScrollView,
    NSTextView,
    NSUnderlineStyleAttributeName,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskMiniaturizable,
    NSWindowStyleMaskResizable,
    NSWindowStyleMaskTitled,
)

_WINDOWS: list = []

_STYLE = (NSWindowStyleMaskTitled | NSWindowStyleMaskClosable
          | NSWindowStyleMaskMiniaturizable | NSWindowStyleMaskResizable)


def show_text(text: str, title: str = "Miotła", links=None) -> None:
    rect = ((0, 0), (720, 520))
    win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        rect, _STYLE, NSBackingStoreBuffered, False)
    win.setTitle_(title)
    win.setReleasedWhenClosed_(False)

    scroll = NSScrollView.alloc().initWithFrame_(((0, 0), (720, 520)))
    scroll.setHasVerticalScroller_(True)
    scroll.setAutohidesScrollers_(True)

    tv = NSTextView.alloc().initWithFrame_(((0, 0), (720, 520)))
    tv.setEditable_(False)
    tv.setSelectable_(True)
    tv.setRichText_(True)
    tv.setDrawsBackground_(True)
    tv.setBackgroundColor_(NSColor.textBackgroundColor())
    tv.setTextContainerInset_((12, 12))

    font = NSFont.monospacedSystemFontOfSize_weight_(12.0, 0.0)
    body = NSMutableAttributedString.alloc().initWithString_attributes_(
        text or "", {NSFontAttributeName: font,
                     NSForegroundColorAttributeName: NSColor.labelColor()})

    for label, url in (links or []):
        link_attrs = {
            NSFontAttributeName: font,
            NSForegroundColorAttributeName: NSColor.linkColor(),
            NSLinkAttributeName: url,
            NSUnderlineStyleAttributeName: 1,
        }
        body.appendAttributedString_(
            NSAttributedString.alloc().initWithString_attributes_("\n", {NSFontAttributeName: font}))
        body.appendAttributedString_(
            NSAttributedString.alloc().initWithString_attributes_(label + "  ↗", link_attrs))

    tv.textStorage().setAttributedString_(body)

    scroll.setDocumentView_(tv)
    win.setContentView_(scroll)
    win.center()

    NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
    win.makeKeyAndOrderFront_(None)

    _WINDOWS.append(win)
    if len(_WINDOWS) > 8:
        _WINDOWS.pop(0)
