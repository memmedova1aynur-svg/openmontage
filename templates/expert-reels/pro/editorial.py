"""Sənədli/redaksiya üslublu reel: kadraj + kamera hərəkəti + qrafik overlay + qısa keçid bulanıqlığı
+ danışıq altında musiqi (ducking) + SFX → Instagram ixracı → QA.

İstifadə:  python3 editorial.py plan.json
plan.json:
{
  "src": "video.mov", "words": "analysis.json",       # söz vaxtları (s/e və ya start/end)
  "brand": "musteri-adi",                             # brand_kit.json → "talk": base kadraj, hflip, color
  "T": 54.4,                                           # yekun müddət (mənbə qısadırsa son kadr dondurulur)
  "cam": [[0, 2.3, 1.0, 1.025], [2.3, 9.6, 1.12, 1.15]],  # [başlanğıc, son, zoom0, zoom1] — seqment içində ease, sərhəddə kəsik
  "focus": [0.505, 0.41],                              # zoom mərkəzi (üz), kadrın nisbəti
  "overlay": "gfx/fr/%05d.png",                        # RGBA kadr ardıcıllığı (30 fps), qrafik səhnələr
  "blur": [[10.35, 15.0], [20.05, 25.0]],              # tam ekran səhnə aralıqları: girişdə və çıxışda 0.1 s bulanıqlıq
  "music": {"file": "mus.mp3", "level": -29, "end_up": [52.1, 7]},
  "sfx": [["paper1.wav", 10.25, -27]],
  "out": "out/Ad.mp4"
}
"""
import json, sys, os
from pathlib import Path
import numpy as np
A = Path(__file__).resolve().parent; sys.path.insert(0, str(A))
import avkit as K

P = json.load(open(sys.argv[1])); ROOT = Path(sys.argv[1]).resolve().parent
rp = lambda x: str((ROOT / x).resolve()) if x and not os.path.isabs(x) else x
def brand_talk(name):
    if not name: return {}
    for d in (os.environ.get("PRO_BRANDS"), str(A.parents[2] / "instagram-clients")):
        f = Path(d or "", name, "brand_kit.json")
        if d and f.exists(): return json.load(open(f)).get("talk", {})
    raise SystemExit(f"brand_kit tapılmadı: {name}")
B = {**brand_talk(P.get("brand")), **P}
SRC = rp(B["src"]); T = float(B.get("T") or K.probe_dur(SRC)); OUT = K.next_version(rp(B["out"]))
WORK = OUT.parent / (OUT.stem + "_work"); WORK.mkdir(parents=True, exist_ok=True)
COLOR = B.get("color", "eq=contrast=1.04:saturation=0.94:gamma=0.99,curves=master='0/0 0.06/0.05 0.6/0.6 0.92/0.9 1/0.97',colortemperature=temperature=6300:mix=0.6")
bc = B["base"]

# 1) baza keçidi: CFR 30, güzgü, rəng, kadraj (mov vaxt damğası problemlərini də aradan qaldırır)
BASE = WORK / "base.mp4"
crop = f"crop=w=iw*{bc['s']}:h=ih*{bc['s']}:x='max(0,min(iw-ow,iw*{bc['cx']:.4f}-ow/2))':y='max(0,min(ih-oh,ih*{bc['cy']:.4f}-oh/2))'"
K.run(["ffmpeg", "-y", "-v", "error", "-i", SRC, "-vf", ("hflip," if B.get("hflip") else "") + f"setsar=1,{COLOR},{crop},scale=1080:1920:flags=lanczos,tpad=stop_mode=clone:stop_duration=3",
       "-an", "-fps_mode", "cfr", "-r", "30", "-t", str(T), "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-pix_fmt", "yuv420p", str(BASE)])

# 2) kamera: seqment içində smoothstep zoom, sərhəddə kəsik
def kexpr():
    e = "1"
    for a, b, k0, k1 in B.get("cam", []):
        d = min(b, T) - a; u = f"clip((it-{a})/{d:.3f},0,1)"
        e = f"if(gte(it,{a}),{k0}+{k1 - k0:.4f}*(3*pow({u},2)-2*pow({u},3)),{e})"
    return e.replace("it", "(in/30)")
Kx = kexpr(); PX, PY = B.get("focus", [0.5, 0.42])
x0 = f"{PX}*W*(1-1/({Kx}))"; y0 = f"{PY}*H*(1-1/({Kx}))"
persp = (f"perspective=x0='{x0}':y0='{y0}':x1='{x0}+W/({Kx})':y1='{y0}':x2='{x0}':y2='{y0}+H/({Kx})':x3='{x0}+W/({Kx})':y3='{y0}+H/({Kx})'"
         ":interpolation=cubic:eval=frame")
en = "+".join(f"between(t,{a + 0.25:.2f},{a + 0.35:.2f})+between(t,{b - 0.3:.2f},{b - 0.2:.2f})" for a, b in B.get("blur", [])) or "0"
inputs = ["-i", str(BASE)]; fc = f"[0:v]setpts=N/30/TB,{persp},scale=1080:1920:flags=lanczos,gblur=sigma=18:enable='{en}'[sp];"
if B.get("overlay"):
    inputs += ["-framerate", "30", "-i", rp(B["overlay"])]
    fc += "[1:v]format=rgba,setpts=N/30/TB[ov];[sp][ov]overlay=0:0:format=auto:eof_action=pass[c];"
else: fc += "[sp]null[c];"
fc += "[c]noise=c0s=5:c0f=t+u,unsharp=3:3:0.25,format=yuv420p[v]"
VID = WORK / "v.mp4"
K.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fc, "-map", "[v]", "-t", str(T), "-r", "30", "-c:v", "libx264", "-preset", "medium",
       "-crf", "19", "-maxrate", "4.5M", "-bufsize", "9M", "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p", "-g", "60", str(VID)])

# 3) səs: danışıq −16 → musiqi (danışıq maskası ilə ducking) → SFX → −14 LUFS
RAW, SP = WORK / "sp_raw.wav", WORK / "sp.wav"
K.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-vn", "-ac", "1", "-ar", str(K.SR), "-t", str(T), str(RAW)])
K.loudnorm_2pass(RAW, SP, I=-16, pre=K.SPEECH_CHAIN)
N = int(T * K.SR); sp = np.zeros((N, 2)); s = K.load(SP, 1); sp[:min(N, len(s))] = np.repeat(s[:N], 2, 1)
mask = np.zeros(N, bool)
if B.get("words"):
    for w in json.load(open(rp(B["words"])))["words"]:
        a = w.get("s", w.get("start")); b = w.get("e", w.get("end"))
        if a is not None and b is not None: mask[int(a * K.SR):int(b * K.SR)] = True
mix = sp
if B.get("music"):
    mu = B["music"]; mix = mix + K.music_bed(K.load(rp(mu["file"])), N, mask, level=mu.get("level", -29), duck_db=mu.get("duck", 4), end_up=mu.get("end_up"))
if B.get("sfx"): mix = K.place_sfx(mix, [(rp(f), at, lv) for f, at, lv in B["sfx"]])
MIX, FIN = WORK / "mix.wav", WORK / "final.wav"; K.save(mix, MIX); K.finalize(MIX, FIN)
K.export_ig(VID, FIN, OUT, copy_video=True)
K.cover(BASE, B.get("cover_t", 1.0), OUT.parent / (OUT.stem + "_kadr_altyazisiz.jpg"))  # üz qabığı üçün təmiz kadr
if B.get("story"): K.story_clips(OUT, B["story"], OUT.parent / "story", label=B.get("story_label"))
q = K.qa(OUT); json.dump(q, open(OUT.parent / (OUT.stem + "_qa.json"), "w"), ensure_ascii=False, indent=1)
print(f"{'OK' if q['ok'] else 'YOXLA'} {OUT} {q}")
