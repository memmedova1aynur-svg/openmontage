"""Çəkilişdən əvvəl sınaq: 10–20 s sınaq kadrı → səs, fon küyü, işıq, kadraj yoxlaması.

  python3 preflight.py <sınaq.mp4>
Hər yoxlama üçün HAZIR / DİQQƏT / DÜZƏLT və nə etmək lazım olduğunu yazır (Azərbaycan dilində, çəkiliş komandası üçün).
"""
import json, re, subprocess, sys
import numpy as np
from pathlib import Path

F = Path(sys.argv[1]); R = []
def add(ok, name, val, fix): R.append(("HAZIR" if ok == 2 else "DİQQƏT" if ok == 1 else "DÜZƏLT", name, val, fix))
pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(F)], capture_output=True, text=True).stdout)
v = next((s for s in pr["streams"] if s["codec_type"] == "video"), None); a = next((s for s in pr["streams"] if s["codec_type"] == "audio"), None)
rot = abs(int((v.get("side_data_list") or [{}])[0].get("rotation", 0) or 0)) if v else 0
w, h = (v["height"], v["width"]) if rot in (90, 270) else (v["width"], v["height"])
add(2 if h > w else 0, "Kadr istiqaməti", f"{w}x{h}", "Telefonu şaquli tutun (9:16)." if h <= w else "")
add(2 if min(w, h) >= 1080 else 1, "Keyfiyyət", f"{min(w, h)}p", "Kameranı 1080p və ya 4K-ya qoyun." if min(w, h) < 1080 else "")
fps = eval(v.get("r_frame_rate", "30/1")); add(2 if 24 <= fps <= 31 else 1, "Kadr tezliyi", f"{fps:.0f} fps", "25 və ya 30 fps seçin (60 lazım deyil)." if fps > 31 else "")
if not a: add(0, "Səs", "yoxdur", "Səs yazılmır — mikrofonu yoxlayın.")
else:
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(F), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout, np.int16).astype(float) / 32768
    fr = np.array([20 * np.log10(np.sqrt((x[i:i + 1600] ** 2).mean()) + 1e-9) for i in range(0, len(x) - 1600, 1600)])
    speech, floor, peak = np.percentile(fr, 90), np.percentile(fr, 10), 20 * np.log10(np.abs(x).max() + 1e-9)
    snr = speech - floor
    add(2 if -24 <= speech <= -10 else 1 if -32 <= speech else 0, "Danışıq səviyyəsi", f"{speech:.0f} dB",
        "Mikrofonu ağıza yaxınlaşdırın (taxma mikrofon ən yaxşısıdır)." if speech < -24 else "Səs çox ucadır, mikrofon həssaslığını azaldın." if speech > -10 else "")
    add(2 if snr >= 25 else 1 if snr >= 15 else 0, "Fon küyü", f"danışıq/küy fərqi {snr:.0f} dB",
        "Otaq küylüdür: kondisioner/ventilyatoru söndürün, qapını bağlayın, mikrofonu yaxınlaşdırın." if snr < 25 else "")
    add(0 if peak > -0.5 else 2, "Səs partlaması (klip)", f"pik {peak:.1f} dB", "Səs kəsilir (klip) — mikrofon səviyyəsini aşağı salın." if peak > -0.5 else "")
    sd = subprocess.run(["ffmpeg", "-v", "info", "-i", str(F), "-af", "highpass=f=300,lowpass=f=3400,astats=metadata=1:reset=0", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.findall(r"RMS level dB: (-?[\d.]+)", sd)
    if m and speech - float(m[-1]) > 12: add(1, "Səs tembri", "boğuq", "Səs boğuq çıxır: mikrofonu paltarın altında gizlətməyin, üzə yaxın taxın.")
# işıq və üz
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from montaj.reframe import detect_faces
dur = float(pr["format"]["duration"]); faces = [f for f in detect_faces(F, 0.5, max(1.0, dur - 0.5), 1.0) if f["faces"]]
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{dur / 2:.2f}", "-i", str(F), "-frames:v", "1", "-vf", "scale=270:480,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
g = np.frombuffer(raw, np.uint8).astype(float)
if g.size: add(2 if 70 <= g.mean() <= 180 else 1, "İşıq", f"orta parlaqlıq {g.mean():.0f}/255",
               "Kadr qaranlıqdır: pəncərəyə üzbəüz durun və ya işıq əlavə edin." if g.mean() < 70 else "Kadr çox işıqlıdır: birbaşa günəşdən çəkilin." if g.mean() > 180 else "")
if not faces: add(0, "Üz", "tapılmadı", "Üz kadrda görünmür və ya çox kiçikdir — kameranı yaxınlaşdırın.")
else:
    f = max(faces[len(faces) // 2]["faces"], key=lambda q: q["w"] * q["h"]); cx, top = f["x"] + f["w"] / 2, f["y"]
    add(2 if 0.12 <= f["w"] <= 0.45 else 1, "Üzün ölçüsü", f"kadr eninin {f['w'] * 100:.0f}%-i", "Bir az yaxınlaşın — üz kiçik görünür." if f["w"] < 0.12 else "Bir az uzaqlaşın — çiyinlər də görünsün." if f["w"] > 0.45 else "")
    add(2 if 0.38 <= cx <= 0.62 else 1, "Mərkəz", f"üz mərkəzi {cx * 100:.0f}%", "Kameranı ortaya düzəldin." if not 0.38 <= cx <= 0.62 else "")
    add(2 if 0.12 <= top <= 0.35 else 1, "Baş üstü boşluq", f"{top * 100:.0f}%", "Başın üstündə çox boşluq var — kameranı aşağı endirin." if top > 0.35 else
        "Baş kəsilir/yuxarıya çox yaxındır — kameranı bir az qaldırın və ya uzaqlaşın." if top < 0.12 else "")
    add(2 if len(faces) >= 0.8 * max(1, int(dur - 1)) else 1, "Üz sabitliyi", f"{len(faces)} yoxlamada görünür", "Kadrdan çıxmayın, tripod işlədin." if len(faces) < 0.8 * max(1, int(dur - 1)) else "")
bad = [r for r in R if r[0] == "DÜZƏLT"]; warn = [r for r in R if r[0] == "DİQQƏT"]
print(f"YEKUN: {'ÇƏKİLİŞƏ HAZIRDIR' if not bad and not warn else 'DÜZƏLİŞ LAZIMDIR' if bad else 'ÇƏKMƏK OLAR, AMMA YAXŞILAŞDIRIN'}\n")
for s, n, val, fix in R: print(f"[{s:6}] {n}: {val}" + (f"\n         → {fix}" if fix else ""))
json.dump([dict(zip(("status", "check", "value", "fix"), r)) for r in R], open(F.with_suffix(".preflight.json"), "w"), ensure_ascii=False, indent=1)
