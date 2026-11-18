#!/usr/bin/env python3
"""Şriftin Azərbaycan hərflərini və verilmiş mətni dəstəkləməsini yoxlayır.
  typecheck.py font.ttf [--text "..."]"""
import sys
from fontTools.ttLib import TTFont
AZ = "ƏəĞğİıŞşÇçÖöÜü"
def az_upper(s): return s.replace("i", "İ").replace("ı", "I").upper()
def az_lower(s): return s.replace("İ", "i").replace("I", "ı").lower()
f = sys.argv[1]; cm = TTFont(f).getBestCmap()
miss = [c for c in AZ if ord(c) not in cm]
print(f, "Azərbaycan hərfləri:", "TAM" if not miss else "ÇATMIR " + "".join(miss))
if "--text" in sys.argv:
    t = sys.argv[sys.argv.index("--text") + 1]
    bad = sorted({c for c in t + az_upper(t) if not c.isspace() and ord(c) not in cm})
    print("mətn:", "OK" if not bad else "dəstəklənmir: " + "".join(bad))
    print("böyük hərf (az):", az_upper(t))
sys.exit(1 if miss else 0)
