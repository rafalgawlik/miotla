#!/usr/bin/env python3
"""Generator ikony Miotły (template: czerń + alfa) — kształt „besom” (jak 🧹).

Styl jak morning-agent: nadpróbkowanie 8× + LANCZOS. Zapis w 2× pikseli z
DPI=144, więc macOS renderuje ~18 pt (ostro na Retinie, w rozmiarze paska).

Wyniki:
  assets/broom-template.png          — ikona statyczna (bezczynność)
  assets/broom_sweep_00..07.png      — klatki „zamiatania” (animacja w trakcie)
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
PIVOT = (0.83, 0.11)         # czubek trzonka — oś obrotu przy zamiataniu
FRAMES = 8
SWING = 7.0                  # amplituda wychylenia w stopniach


def _unit(dx, dy):
    d = math.hypot(dx, dy)
    return (dx / d, dy / d)


def draw_broom(size_pt, angle=0.0):
    """Miotła-besom jako template (czerń + alfa), opcjonalnie wychylona."""
    s = size_pt * 2 * SS         # 2× (Retina) × nadpróbkowanie
    img = Image.new("RGBA", (s, s), CLEAR)
    d = ImageDraw.Draw(img)

    pivot = (PIVOT[0] * s, PIVOT[1] * s)       # czubek trzonka
    bind = (0.47 * s, 0.52 * s)                # miejsce wiązania
    ux, uy = _unit(bind[0] - pivot[0], bind[1] - pivot[1])   # oś
    nx, ny = (-uy, ux)                         # prostopadła

    # trzonek (cienki, zaokrąglone końce)
    d.line([pivot, bind], fill=BLACK, width=int(0.050 * s))
    r = 0.028 * s
    d.ellipse([pivot[0] - r, pivot[1] - r, pivot[0] + r, pivot[1] + r], fill=BLACK)

    # włosie: wiązka rozszerzająca się do zaokrąglonego dołu (teardrop)
    tip = (bind[0] + ux * 0.40 * s, bind[1] + uy * 0.40 * s)
    wB, wT = 0.045 * s, 0.185 * s
    N = 40
    left, right = [], []
    for i in range(N + 1):
        t = i / N
        w = wB + (wT - wB) * (t ** 0.75)
        cx = bind[0] + (tip[0] - bind[0]) * t
        cy = bind[1] + (tip[1] - bind[1]) * t
        left.append((cx + nx * w, cy + ny * w))
        right.append((cx - nx * w, cy - ny * w))
    d.polygon(left + right[::-1], fill=BLACK)

    # opaska wiązania
    bw = 0.12 * s
    d.line([(bind[0] + nx * bw, bind[1] + ny * bw),
            (bind[0] - nx * bw, bind[1] - ny * bw)], fill=BLACK, width=int(0.055 * s))

    # szpary między strawami (wycięcia do przezroczystości)
    for frac in (-0.66, -0.33, 0.0, 0.33, 0.66):
        x1 = tip[0] + nx * (wT * 0.95 * frac) + ux * 0.03 * s
        y1 = tip[1] + ny * (wT * 0.95 * frac) + uy * 0.03 * s
        d.line([(bind[0] + ux * 0.14 * s, bind[1] + uy * 0.14 * s), (x1, y1)],
               fill=CLEAR, width=int(0.016 * s))

    if angle:
        img = img.rotate(angle, resample=Image.BICUBIC, center=pivot)

    return img.resize((size_pt * 2, size_pt * 2), Image.LANCZOS)


def draw_app_icon(size=512):
    """Ikona Docka / Cmd-Tab: biała miotła na zaokrąglonym zielonym kafelku."""
    S = size
    top, bot = (52, 211, 153), (10, 150, 110)   # emerald → green (jak landing)
    grad = Image.new("RGBA", (S, S))
    gd = ImageDraw.Draw(grad)
    for y in range(S):
        t = y / (S - 1)
        gd.line([(0, y), (S, y)], fill=(
            int(top[0] + (bot[0] - top[0]) * t),
            int(top[1] + (bot[1] - top[1]) * t),
            int(top[2] + (bot[2] - top[2]) * t), 255))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.225), fill=255)
    tile = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    tile.paste(grad, (0, 0), mask)

    # sylwetka miotły (czerń+alfa) → przemalowana na biało, wyśrodkowana
    broom = draw_broom(128)                      # 256×256, czerń na przezroczystym
    alpha = broom.split()[3]
    white = Image.merge("RGBA", (Image.new("L", broom.size, 255),) * 3 + (alpha,))
    target = int(S * 0.80)
    white = white.resize((target, target), Image.LANCZOS)
    off = (S - target) // 2
    tile.alpha_composite(white, (off, off))
    return tile


def save(img, name, dpi=(144, 144)):
    path = os.path.join(HERE, name)
    img.save(path, dpi=dpi)            # 144 dpi → punkty = piksele/2 = rozmiar paska
    return path


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def main():
    size_pt = int(sys.argv[1]) if len(sys.argv) > 1 else 18

    static = save(draw_broom(size_pt), "broom-template.png")
    print("ICON_STATIC=" + b64(static))

    # kolorowa ikona Docka / Cmd-Tab (72 dpi — pełny rozmiar)
    save(draw_app_icon(512), "app_icon.png", dpi=(72, 72))
    print("APP_ICON=app_icon.png")

    for i in range(FRAMES):
        ang = SWING * math.sin(2 * math.pi * i / FRAMES)
        p = save(draw_broom(size_pt, ang), f"broom_sweep_{i:02d}.png")
        print(f"SWEEP_{i:02d}=" + b64(p))


if __name__ == "__main__":
    main()
