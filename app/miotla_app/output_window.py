"""Natywne okno (AppKit) z monospace'owym, przewijalnym tekstem — wynik
sprzątania / podglądu pokazujemy tu zamiast w Terminalu.

Wszystko musi dziać się na głównym wątku (NSWindow). Trzymamy referencje do
okien w module, żeby GC ich nie zamknął.
"""
from __future__ import annotations

from AppKit import (
    NSApplication,
    NSBackingStoreBuffered,
    NSColor,
    NSFont,
    NSScrollView,
    NSTextView,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskMiniaturizable,
    NSWindowStyleMaskResizable,
    NSWindowStyleMaskTitled,
)

_WINDOWS: list = []     # referencje, żeby okna nie znikały

_STYLE = (NSWindowStyleMaskTitled | NSWindowStyleMaskClosable
          | NSWindowStyleMaskMiniaturizable | NSWindowStyleMaskResizable)


def show_text(text: str, title: str = "Miotła") -> None:
    rect = ((0, 0), (720, 520))
    win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        rect, _STYLE, NSBackingStoreBuffered, False)
    win.setTitle_(title)
    win.setReleasedWhenClosed_(False)

    scroll = NSScrollView.alloc().initWithFrame_(((0, 0), (720, 520)))
    scroll.setHasVerticalScroller_(True)
    scroll.setHasHorizontalScroller_(True)
    scroll.setAutohidesScrollers_(True)

    tv = NSTextView.alloc().initWithFrame_(((0, 0), (720, 520)))
    tv.setEditable_(False)
    tv.setRichText_(False)
    tv.setDrawsBackground_(True)
    tv.setBackgroundColor_(NSColor.textBackgroundColor())
    tv.setTextColor_(NSColor.labelColor())
    tv.setFont_(NSFont.monospacedSystemFontOfSize_weight_(12.0, 0.0))
    tv.setString_(text or "")
    tv.setTextContainerInset_((12, 12))

    scroll.setDocumentView_(tv)
    win.setContentView_(scroll)
    win.center()

    NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
    win.makeKeyAndOrderFront_(None)

    _WINDOWS.append(win)
    # nie trzymaj w nieskończoność zbyt wielu okien
    if len(_WINDOWS) > 8:
        _WINDOWS.pop(0)
