#!/usr/bin/env python3
"""Generator ikony Miotły dla SwiftBar (templateImage: czerń + alfa).

Rysuje miotłę: ukośny trzonek + rozchylone włosie z kilkoma szparami.
Renderuje w dużej skali i zmniejsza z antyaliasingiem. Zapisuje PNG i
wypisuje base64 (do wklejenia jako templateImage=...).

Użycie:  python3 assets/make_icon.py [rozmiar_px]   # domyślnie 36
"""
import base64
import sys
from PIL import Image, ImageDraw

OUT = __file__.rsplit("/", 1)[0] + "/broom-template.png"
size = int(sys.argv[1]) if len(sys.argv) > 1 else 36
SS = 8                      # nadpróbkowanie
S = size * SS
BLACK = (0, 0, 0, 255)
CLEAR = (0, 0, 0, 0)

img = Image.new("RGBA", (S, S), CLEAR)
d = ImageDraw.Draw(img)


def P(x, y):
    return (x * S, y * S)


# Trzonek: gruba ukośna linia z zaokrąglonymi końcami.
d.line([P(0.80, 0.12), P(0.42, 0.56)], fill=BLACK, width=int(0.075 * S))
# zaokrąglenie górnego końca trzonka
r = 0.038 * S
cx, cy = 0.80 * S, 0.12 * S
d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BLACK)

# Opaska łącząca trzonek z włosiem.
d.line([P(0.34, 0.52), P(0.52, 0.62)], fill=BLACK, width=int(0.055 * S))

# Włosie: rozchylony trapez.
head = [P(0.345, 0.545), P(0.515, 0.635), P(0.63, 0.95), P(0.13, 0.95)]
d.polygon(head, fill=BLACK)

# Szpary między kłosami włosia (wycinamy do przezroczystości).
for t in (0.30, 0.43, 0.56, 0.69, 0.82):
    x = 0.13 + t * (0.63 - 0.13)
    d.line([P(x, 0.70), P(x - 0.01, 0.95)], fill=CLEAR, width=int(0.018 * S))

img = img.resize((size, size), Image.LANCZOS)
img.save(OUT)

with open(OUT, "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
print(b64)
