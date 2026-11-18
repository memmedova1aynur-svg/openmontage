#!/usr/bin/env python3
"""Pinterest önizləmələrindən nömrəli contact sheet: python3 pin_sheet.py <dir> [--cols 5]
Sheet-ə BAX, 15–20 nəticədən ən güclü 3–5 referansı nömrə ilə seç, səbəbini yaz (refs.md)."""
import json, sys, argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ap = argparse.ArgumentParser(); ap.add_argument("dir"); ap.add_argument("--cols", type=int, default=5); ap.add_argument("--h", type=int, default=420)
a = ap.parse_args(); d = Path(a.dir)
pins = json.loads((d / "pins.json").read_text())
W, H = int(a.h * 0.75), a.h
rows = (len(pins) + a.cols - 1) // a.cols
s = Image.new("RGB", (a.cols * W, rows * (H + 30)), "white"); dr = ImageDraw.Draw(s)
try: f = ImageFont.truetype("/root/.fonts/ayra/DMSans-700.ttf", 18)
except Exception: f = ImageFont.load_default()
for p in pins:
    im = Image.open(p["preview"]).convert("RGB"); im.thumbnail((W - 6, H - 6))
    x, y = (p["n"] % a.cols) * W, (p["n"] // a.cols) * (H + 30)
    s.paste(im, (x + (W - im.width) // 2, y + (H - im.height) // 2))
    dr.text((x + 6, y + H + 4), f"#{p['n']}", fill="black", font=f)
s.save(d / "sheet.jpg", quality=82); print(d / "sheet.jpg", len(pins))
