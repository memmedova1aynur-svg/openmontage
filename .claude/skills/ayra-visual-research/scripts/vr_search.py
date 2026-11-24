#!/usr/bin/env python3
"""Real vizual axtarış: əvvəl lokal kitabxana, sonra Openverse. Namizədləri yükləyib contact sheet qurur.

  python3 vr_search.py "wooden montessori toy" "shape sorter wooden" --out /tmp/vr/montessori --n 12

Nəticə: <out>/candidates.json + <out>/sheet.jpg (nömrəli). Sheet-ə BAX — fayl adına güvənmə.
"""
import argparse, io, json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).parent))
import vr_lib as L

ap = argparse.ArgumentParser()
ap.add_argument("queries", nargs="+")
ap.add_argument("--out", required=True)
ap.add_argument("--n", type=int, default=12, help="hər sorğu üçün nəticə")
ap.add_argument("--source", default=None, help="wikimedia/flickr/stocksnap/rawpixel ...")
ap.add_argument("--any-category", action="store_true", help="yalnız foto yox, illüstrasiya da")
ap.add_argument("--min-width", type=int, default=900)
a = ap.parse_args()

out = Path(a.out); (out / "c").mkdir(parents=True, exist_ok=True)
cands, seen = [], set()
for q in a.queries:
    for m in L.library_search(q)[:4]:
        if m["id"] not in seen:
            seen.add(m["id"]); m = dict(m, local=True); cands.append(m)
    try:
        res = L.openverse(q, n=a.n, source=a.source, category=None if a.any_category else "photograph")
    except Exception as e:
        print(f"[!] Openverse '{q}': {e}"); res = []
    for m in res:
        if m["id"] in seen or (m.get("w") and m["w"] < a.min_width):
            continue
        seen.add(m["id"]); cands.append(m)

ok = []
for i, m in enumerate(cands):
    p = out / "c" / f"{i:02d}.jpg"
    try:
        if m.get("local"):
            Image.open(L.LIB / m["file"]).convert("RGB").save(p, quality=85)
        else:
            raw, ct = L.http(m["download"], timeout=40, retries=2)
            if "image" not in ct:
                raise ValueError(ct)
            im = Image.open(io.BytesIO(raw)).convert("RGB"); im.save(p, quality=90)
            m["w"], m["h"] = im.size
        m["preview"] = str(p); m["n"] = len(ok); ok.append(m)
    except Exception as e:
        print(f"[skip] {m.get('source')} {m['title'][:40]}: {e}")

(out / "candidates.json").write_text(json.dumps(ok, ensure_ascii=False, indent=1))
# contact sheet
T, cols = 300, 4
rows = (len(ok) + cols - 1) // cols or 1
sheet = Image.new("RGB", (cols * T, rows * (T + 34)), "white"); d = ImageDraw.Draw(sheet)
try:
    f = ImageFont.truetype("/root/.fonts/ayra/DMSans-500.ttf", 15)
except Exception:
    f = ImageFont.load_default()
for m in ok:
    im = Image.open(m["preview"]); im.thumbnail((T, T))
    x, y = (m["n"] % cols) * T, (m["n"] // cols) * (T + 34)
    sheet.paste(im, (x + (T - im.width) // 2, y + (T - im.height) // 2))
    d.text((x + 6, y + T + 6), f"#{m['n']} {m['license']} · {m['source']} · {m['w']}px", fill="black", font=f)
sheet.save(out / "sheet.jpg", quality=85)
print(f"{len(ok)} namizəd → {out/'sheet.jpg'}")
