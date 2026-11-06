"""Videonun tam ekran kartlarından karusel (1080x1350) + story kadrları (1080x1920).

  python3 carousel_from_cards.py <video.json> <hazır.mp4> [--max 6]
Kartlar videodakı kimi (eyni lib.html, eyni palitra) son vəziyyətdə render olunur.
1-ci slayd: üz qabığı (varsa _cover.jpg), sonuncu: çağırış slaydı. Çıxış: <hazır>_karusel/01.png …, <hazır>_kartlar/*.png
"""
import json, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image
import kit

CFG, B, PAL = kit.load(sys.argv[1]); MP4 = Path(sys.argv[2]); MAX = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 6
SC = [s for s in kit.scenes(CFG) if s["kind"] not in kit.OVER and s["kind"] != "split"]
stem = MP4.with_suffix(""); cdir = Path(f"{stem}_kartlar"); kdir = Path(f"{stem}_karusel"); cdir.mkdir(exist_ok=True); kdir.mkdir(exist_ok=True)
jobs = [{"kind": s["kind"], "D": s["n"] / 30, "p": s["p"], "out": str(cdir / f"{i:02d}_{s['kind']}.png")} for i, s in enumerate(SC[:MAX])]
js = Path(tempfile.mkdtemp()) / "r.js"; js.write_text(f"""const {{chromium}}=require('/opt/node22/lib/node_modules/playwright');const J={json.dumps(jobs, ensure_ascii=False)};
(async()=>{{const b=await chromium.launch();const p=await b.newPage({{viewport:{{width:1080,height:1920}}}});await p.goto('{(kit.A / "lib.html").as_uri()}');await p.evaluate(()=>document.fonts.ready);
for(const j of J){{const pp={{...j.p}};delete pp.noIn;await p.evaluate(([n,t,D,pp])=>{{document.body.style.background='transparent';renderAt(n,t,D,pp)}},[j.kind,Math.max(0.5,j.D-0.75),j.D,pp]);
await p.waitForTimeout(60);await p.screenshot({{path:j.out}});}}await b.close()}})();""", encoding="utf-8")
subprocess.run(["node", str(js)], check=True)
slides = []
cov = Path(f"{stem}_cover.jpg")
if cov.exists(): slides.append(Image.open(cov).convert("RGB").crop((0, 285, 1080, 1635)))
for j in jobs: slides.append(Image.open(j["out"]).convert("RGB").crop((0, 250, 1080, 1600)))  # kart məzmunu y≈470–1150 → 4:5 içində qalır
# çağırış slaydı
cta = CFG.get("cta") or B.get("cfg", {}).get("cta") or ""
end = Image.new("RGB", (1080, 1350), PAL.get("ink", "#1d1d1b")); from PIL import ImageDraw, ImageFont
d = ImageDraw.Draw(end); fb = ImageFont.truetype(kit.FONT, 76); fr = ImageFont.truetype(kit.FONT_R, 40)
lines = ["Yadda saxla", "və paylaş"] + ([f"Direct: {cta}"] if cta else [])
for i, l in enumerate(lines):
    f = fb if i < 2 else fr; w = d.textlength(l, font=f); d.text(((1080 - w) / 2, 520 + i * 100), l, font=f, fill=PAL.get("acc") if i == 2 else "#FFFFFF")
if B.get("handle"): w = d.textlength("@" + B["handle"].lstrip("@"), font=fr); d.text(((1080 - w) / 2, 1180), "@" + B["handle"].lstrip("@"), font=fr, fill="#BBBBBB")
slides.append(end)
for i, s in enumerate(slides, 1): s.save(kdir / f"{i:02d}.png")
print(f"karusel: {len(slides)} slayd → {kdir.name} · story kartları: {len(jobs)} → {cdir.name}")
