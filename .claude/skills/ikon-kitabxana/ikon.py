#!/usr/bin/env python3
"""Iconify açıq API (açarsız) ilə ikon axtarışı, yükləmə və önizləmə.
  ikon.py axtar <söz> [--dest ph,lucide,...] [--say 40]
  ikon.py yukle <dest:ad> [<dest:ad> ...] --reng "#DC5063" [--olcu 512] [--qovluq out/] [--png]
  ikon.py onizle <söz> [--dest ...] [--say 36] [--reng ...] --fayl preview.png
  ikon.py lisenziya <dest>
Dəstlər (hamısı kommersiya üçün pulsuz): lucide ISC, ph(Phosphor) MIT, tabler MIT, heroicons MIT,
iconoir MIT, ri(Remix) Apache-2.0, material-symbols Apache-2.0, fluent-emoji MIT,
simple-icons CC0 (brend loqoları; ticarət nişanı qaydaları ayrıca), streamline CC-BY-4.0 (müəllif adı)."""
import sys, json, urllib.request, urllib.parse, os, argparse
API = "https://api.iconify.design"
DEF = "ph,lucide,tabler,iconoir,heroicons,ri,material-symbols"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "icon-client"})
    return urllib.request.urlopen(req, timeout=30).read()

def axtar(q, dest, say):
    u = f"{API}/search?query={urllib.parse.quote(q)}&limit={max(32, say)}" + (f"&prefixes={dest}" if dest else "")
    return json.loads(get(u))["icons"][:say]

def svg(icon, reng=None, olcu=None):
    pre, ad = icon.split(":", 1); qs = {}
    if reng: qs["color"] = reng
    if olcu: qs["height"] = str(olcu)
    return get(f"{API}/{pre}/{ad}.svg" + ("?" + urllib.parse.urlencode(qs) if qs else "")).decode()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("emr"); ap.add_argument("args", nargs="*")
    ap.add_argument("--dest", default=DEF); ap.add_argument("--say", type=int, default=40)
    ap.add_argument("--reng"); ap.add_argument("--olcu", type=int, default=512)
    ap.add_argument("--qovluq", default="."); ap.add_argument("--png", action="store_true"); ap.add_argument("--fayl", default="ikon_onizle.png")
    a = ap.parse_args()
    if a.emr == "axtar":
        for i in axtar(" ".join(a.args), a.dest, a.say): print(i)
    elif a.emr == "yukle":
        os.makedirs(a.qovluq, exist_ok=True)
        for ic in a.args:
            s = svg(ic, a.reng, a.olcu); base = os.path.join(a.qovluq, ic.replace(":", "__"))
            open(base + ".svg", "w").write(s)
            if a.png:
                import cairosvg; cairosvg.svg2png(bytestring=s.encode(), write_to=base + ".png", output_height=a.olcu)
            print(base + (".png" if a.png else ".svg"))
    elif a.emr == "onizle":
        import cairosvg, io
        from PIL import Image, ImageDraw
        ics = axtar(" ".join(a.args), a.dest, a.say); n = 6; cell = 190
        S = Image.new("RGB", (n * cell, ((len(ics) + n - 1) // n) * cell), "white"); d = ImageDraw.Draw(S)
        for k, ic in enumerate(ics):
            im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg(ic, a.reng or "#222222").encode(), output_height=110))).convert("RGBA")
            x, y = (k % n) * cell, (k // n) * cell; S.paste(im, (x + (cell - im.width) // 2, y + 18), im); d.text((x + 6, y + cell - 34), ic[:30], fill="black")
        S.save(a.fayl); print(a.fayl, len(ics), "ikon")
    elif a.emr == "lisenziya":
        c = json.loads(get(f"{API}/collections"))
        for p in a.args or a.dest.split(","):
            v = c.get(p); print(p, v and (v["name"], v["total"], v.get("license", {}).get("title"), v.get("author", {}).get("name")))
    else:
        print(__doc__)

main()
