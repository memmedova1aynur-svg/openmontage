"""Hazır videodan sonra işlər.

  python3 postfx.py watermark <video.json> <hazır.mp4>   küncdə @handle işarəsi (yerində yenilənir, QA-dan əvvəl)
  python3 postfx.py exports   <video.json> <hazır.mp4>   4:5 lent versiyası + 15 s qısa kəsim (cümlə sonunda)
  python3 postfx.py cover     <video.json> <hazır.mp4>   üz qabığı: ən kəskin, üzü aydın kadr + brend başlığı
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import kit

CMD, CFG_PATH, MP4 = sys.argv[1], sys.argv[2], Path(sys.argv[3])
CFG, B, PAL = kit.load(CFG_PATH)
stem = MP4.with_suffix("")


def ff(*a): subprocess.run(["ffmpeg", "-y", "-v", "error", *a], check=True)
def dur(f): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)], capture_output=True, text=True).stdout)


def watermark():
    h = B["handle"].lstrip("@"); f = ImageFont.truetype(kit.FONT, 26)
    tw = int(ImageDraw.Draw(Image.new("L", (1, 1))).textlength("@" + h, font=f))
    W, H = tw + 64, 44; im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, W - 1, H - 1], 22, fill=(0, 0, 0, 70))
    d.rounded_rectangle([12, 10, 36, 34], 7, outline=(255, 255, 255, 235), width=3); d.ellipse([18, 16, 30, 28], outline=(255, 255, 255, 235), width=3)
    d.text((46, 7), "@" + h, font=f, fill=(255, 255, 255, 235))
    png = Path(tempfile.mkdtemp()) / "wm.png"; im.save(png); tmp = stem.parent / (stem.name + "_wm.mp4")
    # Instagram-ın yuxarı UI zolağından aşağı, üz bölgəsindən kənarda (sağ yuxarı)
    ff("-i", str(MP4), "-i", str(png), "-filter_complex", f"[0:v][1:v]overlay=W-w-60:{B.get('handleY', 170)}:format=auto",
       "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(tmp))
    tmp.replace(MP4); print("işarə:", "@" + h)


def exports():
    want = CFG.get("exports", B.get("exports")) or []; made = []
    if "4x5" in want:  # lent üçün 1080x1350: altyazı (y≈0.74–0.8) və kartlar kadrda qalır
        o = f"{stem}_4x5.mp4"; ff("-i", str(MP4), "-vf", "crop=1080:1350:0:285", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "copy", "-movflags", "+faststart", o); made.append(o)
    if "short15" in want:  # 12–18 s arası ilk fasilədə (cümlə sonu) kəs
        sd = subprocess.run(["ffmpeg", "-v", "info", "-i", str(MP4), "-af", "silencedetect=n=-32dB:d=0.25", "-f", "null", "-"], capture_output=True, text=True).stderr
        st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", sd)]
        cut = next((x for x in st if 12 <= x <= 18), min(15.0, dur(MP4)))
        o = f"{stem}_15s.mp4"
        ff("-i", str(MP4), "-t", f"{cut + 0.25:.2f}", "-af", f"afade=t=out:st={cut - 0.1:.2f}:d=0.35", "-vf", f"fade=t=out:st={cut - 0.05:.2f}:d=0.3",
           "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", o); made.append(o)
    print("formatlar:", ", ".join(Path(m).name for m in made) or "—")


def cover():
    import cv2
    sys.path.insert(0, str(kit.A.parent.parent.parent)); from montaj.reframe import detect_faces  # montajın üz modeli (blaze_face)
    full = [(s["t0"], s["t0"] + s["n"] / 30) for s in kit.scenes(CFG) if s["kind"] not in kit.OVER]
    D = dur(MP4); best = (-1, None, 0)
    for fr in ([] if CFG.get("coverAt") is not None else detect_faces(MP4, 0.6, D - 0.6, 0.4)):
        t = fr["t"]
        if not fr["faces"] or any(a - 0.3 <= t <= b + 0.3 for a, b in full): continue
        f = max(fr["faces"], key=lambda q: q["w"] * q["h"])
        if f["w"] < 0.15 or f["score"] < 0.6: continue
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(MP4), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
        if len(raw) != 1080 * 1920 * 3: continue
        img = np.frombuffer(raw, np.uint8).reshape(1920, 1080, 3)
        x, y, w, h = int(f["x"] * 1080), int(f["y"] * 1920), int(f["w"] * 1080), int(f["h"] * 1920)
        roi = cv2.cvtColor(img[max(0, y):y + h, max(0, x):x + w], cv2.COLOR_BGR2GRAY)
        if roi.size == 0: continue
        sc = cv2.Laplacian(roi, cv2.CV_64F).var() * f["score"] * (1 - abs(f["x"] + f["w"] / 2 - 0.5))  # kəskin, əmin, mərkəzdə
        if sc > best[0]: best = (sc, img.copy(), t)
    if CFG.get("coverAt") is not None:  # konfiqdə konkret saniyə verilibsə — o kadr
        t = float(CFG["coverAt"]); raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(MP4), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
        best = (1, np.frombuffer(raw, np.uint8).reshape(1920, 1080, 3).copy(), t)
    if best[1] is None: print("üz qabığı: uyğun kadr tapılmadı (konfiqə \"coverAt\": <saniyə> yaz)"); return
    bg = stem.parent / (stem.name + "_cover_bg.jpg"); cv2.imwrite(str(bg), best[1])
    title = CFG.get("coverTitle") or re.sub(r"^\d+\s*|\s*—\s*PRO$", "", CFG.get("title", ""))
    html = Path(tempfile.mkdtemp()) / "c.html"
    html.write_text(f'''<!doctype html><html><head><meta charset="utf-8"><link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@800;900&display=block" rel="stylesheet">
<style>*{{margin:0}}body{{width:1080px;height:1920px;background:url("{bg.as_uri()}") center/cover;font-family:Montserrat;position:relative;overflow:hidden}}
.g{{position:absolute;inset:0;background:linear-gradient(transparent 45%,rgba(0,0,0,.72) 82%)}}
.t{{position:absolute;left:80px;right:80px;top:1180px;color:#fff;font-weight:900;font-size:96px;line-height:1.02;letter-spacing:-.02em;text-shadow:0 6px 30px rgba(0,0,0,.4)}}
.t span{{background:{PAL["acc"]};color:{"#FFFFFF" if sum(int(PAL["acc"][i:i+2],16)*w for i,w in ((1,.299),(3,.587),(5,.114))) < 150 else PAL["ink"]};padding:0 .14em;border-radius:.1em}}</style></head>
<body><div class="g"></div><div class="t">{title.replace("*", "<span>", 1).replace("*", "</span>", 1)}</div><script>document.fonts.ready.then(()=>document.title="done")</script></body></html>''', encoding="utf-8")
    out = f"{stem}_cover.jpg"
    js = f"""const {{chromium}}=require('/opt/node22/lib/node_modules/playwright');(async()=>{{const b=await chromium.launch();const p=await b.newPage({{viewport:{{width:1080,height:1920}}}});
await p.goto('{html.as_uri()}');await p.waitForFunction(()=>document.title==='done');await p.screenshot({{path:'{out}',type:'jpeg',quality:92}});await b.close()}})();"""
    subprocess.run(["node", "-e", js], check=True)
    Image.open(out).crop((0, 240, 1080, 1680)).save(f"{stem}_cover_grid.jpg", quality=92)  # profil gridində 3:4 görünüş
    bg.unlink(missing_ok=True); print(f"üz qabığı: {Path(out).name} (kadr {best[2]:.1f} s)")


{"watermark": watermark, "exports": exports, "cover": cover}[CMD]()
