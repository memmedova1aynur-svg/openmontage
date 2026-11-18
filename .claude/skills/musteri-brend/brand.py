#!/usr/bin/env python3
"""Müştəri brendini çap edir və şəkil rənglərini palitra ilə yoxlayır.
İstifadə: brand.py <müştəri> [--check şəkil.png]"""
import json, sys, glob, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
CL = ROOT / "instagram-clients"
AZ = "ƏəĞğİıŞşÇçÖöÜü"
FONT_DIRS = ["/root/.fonts", "/root/montaj-data/fonts", "/usr/share/fonts", str(ROOT / "remotion-composer/public/montaj-fonts")]

def hx(c): c = c.lstrip("#"); return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))

def find_font(fam):
    from PIL import ImageFont
    for d in FONT_DIRS:
        for f in glob.glob(d + "/**/*.[ot]tf", recursive=True):
            try:
                if ImageFont.truetype(f, 10).getname()[0].lower().startswith(fam.lower()):
                    return f
            except Exception:
                pass
    return None

def az_ok(path):
    try:
        from fontTools.ttLib import TTFont
        cmap = TTFont(path).getBestCmap()
        return all(ord(ch) in cmap for ch in AZ)
    except Exception:
        return None

def main():
    if len(sys.argv) < 2:
        print("müştərilər:", ", ".join(sorted(p.parent.name for p in CL.glob("*/brand_kit.json")))); return
    c = sys.argv[1]; p = CL / c / "brand_kit.json"
    if not p.exists(): sys.exit(f"{p} yoxdur")
    d = json.load(open(p)); pr = d.get("profile", {})
    print(f"# {d.get('name', c)}  ({'TƏSDİQLİ' if pr.get('paletteApproved') else 'təsdiq gözləyir'})")
    if pr.get("paletteNote"): print("  qeyd:", pr["paletteNote"])
    print("## palitra"); [print(f"  {k:7} {v}") for k, v in d.get("palette", {}).items()]
    if d.get("forbiddenColors"): print("  qadağan:", d["forbiddenColors"])
    print("## şriftlər")
    for role, fam in (pr.get("fonts") or {}).items():
        if not fam: continue
        f = find_font(fam); ok = az_ok(f) if f else None
        print(f"  {role:6} {fam:22} {'fayl: ' + os.path.basename(f) if f else 'FAYL YOXDUR (Google Fonts-dan endir)'}  Ə-dəstəyi: {ok}")
    for k in ("field", "audience", "colorDirection"):
        if pr.get(k): print(f"## {k}: {pr[k]}")
    if d.get("rules"): print("## qaydalar"); [print("  -", r) for r in d["rules"]]
    for extra in ("strategiya.md", "brand.md", "voice.md"):
        if (CL / c / extra).exists(): print(f"## oxu: instagram-clients/{c}/{extra}")
    if "--check" in sys.argv:
        from PIL import Image
        img = Image.open(sys.argv[sys.argv.index("--check") + 1]).convert("RGB").resize((200, 200))
        pal = [hx(v) for v in d.get("palette", {}).values()] + [(255, 255, 255)]
        cols = sorted(img.getcolors(40000), reverse=True)[:12]
        print("## şəkil rəngləri → ən yaxın palitra rəngi (məsafə)")
        for n, col in cols:
            dist, near = min((sum((a - b) ** 2 for a, b in zip(col, q)) ** .5, q) for q in pal)
            flag = "" if dist < 30 else "  <-- palitradan kənar?"
            print(f"  {'#%02X%02X%02X' % col} {n:6}px → {'#%02X%02X%02X' % near} ({dist:.0f}){flag}")

main()
