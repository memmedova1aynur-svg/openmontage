"""Hər reeldən story paketi: 1) qısa tizer (ilk cümlə, "tam video profildə"), 2) sorğu kadrı, 3) kart kadrı.

  python3 story_pack.py <video.json> <hazır.mp4>
Çıxış: <hazır>_story/1_tizer.mp4, 2_sorgu.png (stiker yeri boş), 3_kart.png (videodakı ən güclü kart).
"""
import re, subprocess, sys, tempfile, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import kit

CFG, B, PAL = kit.load(sys.argv[1]); MP4 = Path(sys.argv[2]); stem = MP4.with_suffix(""); O = Path(f"{stem}_story"); O.mkdir(exist_ok=True)
# 1) tizer: 6–10 s arası ilk fasilədə kəs, aşağıda "Tam video profildə"
sd = subprocess.run(["ffmpeg", "-v", "info", "-i", str(MP4), "-af", "silencedetect=n=-32dB:d=0.25", "-f", "null", "-"], capture_output=True, text=True).stderr
cut = next((float(x) for x in re.findall(r"silence_start: ([\d.]+)", sd) if 6 <= float(x) <= 10), 8.0)
ban = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(ban); f = ImageFont.truetype(kit.FONT, 44)
t = "Tam video profildə  →"; w = d.textlength(t, font=f)
d.rounded_rectangle([(1080 - w) / 2 - 36, 1520, (1080 + w) / 2 + 36, 1610], 45, fill=PAL.get("acc", "#6CC57E")); d.text(((1080 - w) / 2, 1538), t, font=f, fill=kit.on_acc(PAL))
bp = Path(tempfile.mkdtemp()) / "b.png"; ban.save(bp)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(MP4), "-i", str(bp), "-t", f"{cut + 0.2:.2f}", "-filter_complex",
                f"[0:v][1:v]overlay=0:0:enable='gte(t,{max(0, cut - 3):.2f})'[v]", "-map", "[v]", "-map", "0:a", "-af", f"afade=t=out:st={cut - 0.2:.2f}:d=0.4",
                "-c:v", "libx264", "-crf", "19", "-preset", "medium", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(O / "1_tizer.mp4")], check=True)
# 2) sorğu kadrı: videonun əsas sualı + stiker üçün boş yer
txt = CFG.get("text", ""); q = next((s.strip() for s in re.split(r"(?<=[.?!])\s+", txt) if s.strip().endswith("?") and len(s.split()) >= 3), CFG.get("pollQ") or "Sən necə edirsən?")
q = CFG.get("pollQ") or q
im = Image.new("RGB", (1080, 1920), PAL.get("ink", "#1d1d1b")); d = ImageDraw.Draw(im); f = ImageFont.truetype(kit.FONT, 72); lines, cur = [], ""
for wd in q.split():
    if d.textlength(cur + " " + wd, font=f) > 880: lines.append(cur); cur = wd
    else: cur = (cur + " " + wd).strip()
lines.append(cur)
for i, l in enumerate(lines): w = d.textlength(l, font=f); d.text(((1080 - w) / 2, 520 + i * 92), l, font=f, fill="#FFFFFF")
d.rounded_rectangle([140, 1000, 940, 1300], 36, outline=PAL.get("acc", "#6CC57E"), width=4)
fs = ImageFont.truetype(kit.FONT_R, 30); t = "sorğu stikerini bura qoy"; w = d.textlength(t, font=fs); d.text(((1080 - w) / 2, 1135), t, font=fs, fill="#777777")
im.save(O / "2_sorgu.png")
# 3) kart kadrı (karusel kartlarından birincisi)
kd = Path(f"{stem}_kartlar")
if not kd.exists(): subprocess.run([sys.executable, str(kit.A / "carousel_from_cards.py"), sys.argv[1], str(MP4)], check=True)
ks = sorted(kd.glob("*.png"))
if ks: shutil.copy(ks[0], O / "3_kart.png")
print(f"story paketi: tizer {cut:.1f} s, sorğu, {'kart' if ks else 'kart yoxdur'} → {O.name}")
