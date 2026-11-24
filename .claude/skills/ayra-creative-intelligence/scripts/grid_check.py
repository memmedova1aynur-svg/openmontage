#!/usr/bin/env python3
"""Instagram profil grid kəsimi yoxlaması: hər dizaynın 3:4 mərkəz kəsimi (360×480) + 150px kiçik nüsxə + ölçü yoxlaması.
  python3 grid_check.py a.png b.png c.png --out check.jpg [--grid9]   (--grid9: 9 faylı 3×3 şahmat grid kimi düz)
"""
import argparse
from PIL import Image, ImageDraw
ap = argparse.ArgumentParser(); ap.add_argument("imgs", nargs="+"); ap.add_argument("--out", required=True); ap.add_argument("--grid9", action="store_true")
a = ap.parse_args()
OK = {(1080, 1350), (1080, 1920), (1080, 1080)}
def crop34(im):
    w, h = im.size; ch = w * 4 // 3
    return im.crop((0, (h - ch) // 2, w, (h - ch) // 2 + ch)) if h > ch else im.crop(((w - h * 3 // 4) // 2, 0, (w - h * 3 // 4) // 2 + h * 3 // 4, h))
ims = [Image.open(p).convert("RGB") for p in a.imgs]
for p, im in zip(a.imgs, ims):
    print(("OK  " if im.size in OK else "ÖLÇÜ XƏTASI ") + f"{im.size} {p}")
if a.grid9:
    W, H, g = 360, 480, 4; s = Image.new("RGB", (3 * W + 2 * g, ((len(ims) + 2) // 3) * (H + g)), "white")
    for i, im in enumerate(ims):
        s.paste(crop34(im).resize((W, H), Image.LANCZOS), ((i % 3) * (W + g), (i // 3) * (H + g)))
else:
    s = Image.new("RGB", (len(ims) * 370, 700), "white"); d = ImageDraw.Draw(s)
    for i, im in enumerate(ims):
        c = crop34(im); s.paste(c.resize((360, 480), Image.LANCZOS), (i * 370, 0)); s.paste(c.resize((150, 200), Image.LANCZOS), (i * 370, 495))
s.save(a.out, quality=90); print(a.out)
