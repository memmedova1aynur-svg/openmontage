"""Hook A/B testi: eyni videonun ilk 2.8 saniyəsinə fərqli açılış yazısı → B versiyası.

  python3 ab_hook.py <video.json> <hazır.mp4> "Hook B mətni" [--dur 2.8]
B versiyası Instagram Trial Reel (yalnız izləməyənlərə) kimi paylaşılır; hansı açılışın 3 saniyədən sonra
daha çox saxladığı (Reel view rate) metrics_report.py ilə müqayisə olunur.
"""
import subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import kit

CFG, B, PAL = kit.load(sys.argv[1]); MP4 = Path(sys.argv[2]); TXT = sys.argv[3]
DUR = float(sys.argv[sys.argv.index("--dur") + 1]) if "--dur" in sys.argv else 2.8
im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
for y in range(0, 900):  # yuxarıdan yumşaq qaralma — üz açıq qalır
    d.line([(0, y), (1080, y)], fill=(0, 0, 0, int(150 * (1 - y / 900) ** 1.5)))
f = ImageFont.truetype(kit.FONT, 84); lines, cur = [], ""
for w in TXT.split():
    if d.textlength(cur + " " + w, font=f) > 900: lines.append(cur); cur = w
    else: cur = (cur + " " + w).strip()
lines.append(cur)
for i, l in enumerate(lines):
    w = d.textlength(l, font=f); x, y = (1080 - w) / 2, 250 + i * 100
    if i == len(lines) - 1: d.rounded_rectangle([x - 18, y - 6, x + w + 18, y + 96], 14, fill=PAL.get("acc", "#6CC57E"))
    d.text((x, y), l, font=f, fill=kit.on_acc(PAL) if i == len(lines) - 1 else "#FFFFFF")
png = Path(tempfile.mkdtemp()) / "h.png"; im.save(png); out = MP4.with_name(MP4.stem + "_B.mp4")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(MP4), "-loop", "1", "-t", f"{DUR:.2f}", "-i", str(png), "-filter_complex",
                f"[1:v]format=rgba,fade=t=out:st={DUR - 0.35:.2f}:d=0.35:alpha=1[h];[0:v][h]overlay=0:0:eof_action=pass[v]", "-map", "[v]", "-map", "0:a",
                "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "copy", "-movflags", "+faststart", str(out)], check=True)
print(f"B versiyası: {out.name} (açılış: “{TXT}”, {DUR} s) — Trial Reel kimi paylaş")
