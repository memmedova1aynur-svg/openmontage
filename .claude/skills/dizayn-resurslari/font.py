#!/usr/bin/env python3
"""Google Fonts / Fontshare şriftini TTF kimi endirir və Azərbaycan hərflərini yoxlayır.
  font.py "Playfair Display" 400,700 [--qovluq ~/.fonts]
  font.py --fontshare satoshi 500,700
  font.py --yoxla fayl.ttf"""
import sys, re, os, urllib.request, urllib.parse, json
AZ = "ƏəĞğİıŞşÇçÖöÜü"
def get(u, ua="Mozilla/4.0"): return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": ua}), timeout=30).read()
def yoxla(p):
    from fontTools.ttLib import TTFont
    cm = TTFont(p).getBestCmap(); miss = [c for c in AZ if ord(c) not in cm]
    return "Ə-dəstəyi TAM" if not miss else "ÇATMIR: " + "".join(miss)
a = sys.argv[1:]; q = os.path.expanduser("~/.fonts")
if "--qovluq" in a: i = a.index("--qovluq"); q = os.path.expanduser(a[i + 1]); del a[i:i + 2]
os.makedirs(q, exist_ok=True)
if a and a[0] == "--yoxla": print(a[1], yoxla(a[1])); sys.exit()
if a and a[0] == "--fontshare":
    slug, w = a[1], (a[2] if len(a) > 2 else "400")
    css = get(f"https://api.fontshare.com/v2/css?f[]={slug}@{w}&display=swap", "Mozilla/5.0").decode()
    urls = re.findall(r"url\('?(//[^)']+\.ttf)", css) or re.findall(r"url\('?(//[^)']+\.woff2)", css)
    for u in urls:
        p = os.path.join(q, slug + "_" + os.path.basename(u.split("?")[0])); open(p, "wb").write(get("https:" + u, "Mozilla/5.0"))
        print(p, yoxla(p) if p.endswith(".ttf") else "(woff2)")
    sys.exit()
fam, w = a[0], (a[1] if len(a) > 1 else "400")
css = get("https://fonts.googleapis.com/css2?family=" + urllib.parse.quote(fam) + ":wght@" + w.replace(",", ";")).decode()
for wt, u in re.findall(r"font-weight:\s*(\d+);.*?url\((https://[^)]+\.ttf)\)", css, re.S):
    p = os.path.join(q, fam.replace(" ", "") + f"-{wt}.ttf"); open(p, "wb").write(get(u)); print(p, yoxla(p))
