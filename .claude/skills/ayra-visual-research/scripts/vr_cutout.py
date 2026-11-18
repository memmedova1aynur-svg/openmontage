#!/usr/bin/env python3
"""İstənilən obyekt şəklinin fonunu sil → şəffaf, kəsilmiş PNG (rembg isnet-general-use, lokal, açarsız).

  python3 vr_cutout.py giriş.jpg çıxış.png [--model isnet-general-use] [--max 1600]

İnsan portretləri üçün birefnet-portrait istifadə et (üz cizgiləri dəyişdirilmir, yalnız fon).
"""
import argparse
from PIL import Image
from rembg import new_session, remove

ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("dst")
ap.add_argument("--model", default="isnet-general-use"); ap.add_argument("--max", type=int, default=1600)
a = ap.parse_args()
im = Image.open(a.src).convert("RGB"); im.thumbnail((a.max, a.max))
cut = remove(im, session=new_session(a.model))
bbox = cut.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox()
(cut.crop(bbox) if bbox else cut).save(a.dst)
print(a.dst, cut.size)
