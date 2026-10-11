#!/usr/bin/env python3
"""Generator ikony Miotły dla SwiftBar (templateImage: czerń + alfa).

Styl dopasowany do morning-agent: nadpróbkowanie 8× + LANCZOS, czysty
monochromatyczny kształt. Zapisywany w 2× pikseli z DPI=144, więc macOS
renderuje go w ~18 pt (ostro na Retinie, w rozmiarze paska menu).

Wyniki:
  assets/broom-template.png          — ikona statyczna (bezczynność)
  assets/broom_sweep_00..07.png      — klatki „zamiatania" (animacja w trakcie)
  + base64 statycznej ikony oraz klatek na stdout (do wklejenia w pluginie)

Użycie:  python3 assets/make_icon.py [rozmiar_pt]   # domyślnie 18
"""
import base64
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SS = 8                       # nadpróbkowanie dla gładkich krawędzi
BLACK = (0, 0, 0, 255)
CLEAR = (0, 0, 0, 0)
PIVOT = (0.80, 0.14)         # czubek trzonka — oś obrotu przy zamiataniu
FRAMES = 8                   # klatki animacji
SWING = 7.0                  # amplituda wychylenia w stopniach


def draw_broom(size_pt, angle=0.0):
    """Miotła jako template (czerń + alfa), opcjonalnie wychylona o `angle`."""
    s = size_pt * 2 * SS     # 2× (Retina) × nadpróbkowanie
    img = Image.new("RGBA", (s, s), CLEAR)
    d = ImageDraw.Draw(img)

    def P(x, y):
        return (x * s, y * s)

    def dot(x, y, r):
        d.ellipse([x * s - r, y * s - r, x * s + r, y * s + r], fill=BLACK)

    # Trzonek: gruba ukośna linia z zaokrąglonymi końcami.
    d.line([P(*PIVOT), P(0.44, 0.56)], fill=BLACK, width=int(0.075 * s))
    dot(PIVOT[0], PIVOT[1], 0.040 * s)

    # Opaska wiążąca trzonek z włosiem.
    d.line([P(0.37, 0.52), P(0.52, 0.60)], fill=BLACK, width=int(0.055 * s))

    # Włosie: rozchylony trapez.
    head = [P(0.355, 0.545), P(0.515, 0.625), P(0.585, 0.955), P(0.085, 0.905)]
    d.polygon(head, fill=BLACK)

    # Szpary między kłosami włosia (wycinane do przezroczystości).
    for t in (0.18, 0.34, 0.50, 0.66, 0.82):
        x0 = 0.355 + t * (0.515 - 0.355)
        y0 = 0.545 + t * (0.625 - 0.545)
        x1 = 0.085 + t * (0.585 - 0.085)
        d.line([P(x0, y0 + 0.10), P(x1, 0.955)], fill=CLEAR, width=int(0.016 * s))

    if angle:
        img = img.rotate(angle, resample=Image.BICUBIC,
                         center=(PIVOT[0] * s, PIVOT[1] * s))

    out = img.resize((size_pt * 2, size_pt * 2), Image.LANCZOS)
    return out


def save(img, name):
    path = os.path.join(HERE, name)
    img.save(path, dpi=(144, 144))     # 144 dpi → punkty = piksele/2 = rozmiar paska
    return path


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def main():
    size_pt = int(sys.argv[1]) if len(sys.argv) > 1 else 18

    static = save(draw_broom(size_pt), "broom-template.png")
    print("ICON_STATIC=" + b64(static))

    for i in range(FRAMES):
        ang = SWING * math.sin(2 * math.pi * i / FRAMES)
        p = save(draw_broom(size_pt, ang), f"broom_sweep_{i:02d}.png")
        print(f"SWEEP_{i:02d}=" + b64(p))


if __name__ == "__main__":
    main()
