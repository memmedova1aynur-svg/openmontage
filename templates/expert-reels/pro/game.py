"""Animasiyalı oyun videosu: HTML şablon → kadrlar → sintez səslər → (musiqi) → Instagram ixracı → QA.

İstifadə:  python3 game.py plan.json
plan.json:
{
  "page": "yaddas_anbari",            # games/<ad>.html (yaddas_anbari, stroop_sprint, diqqet_telesi, bosluqlari_doldur)
  "name": "Ekspertin adı",             # yuxarıdakı ad nişanı
  "music": "mus.mp3",                 # istəyə görə: gərgin fon musiqisi (oyun səslərinin altında)
  "out": "out/Oyun_Yaddas_anbari.mp4" # nəticə: _vN versiyası
}
Test: python3 game.py plan.json test 1.5,8,20   → yalnız göstərilən saniyələrin kadrları
"""
import json, sys, subprocess, shutil, urllib.parse
from pathlib import Path
import numpy as np
A = Path(__file__).resolve().parent; sys.path.insert(0, str(A))
import avkit as K

P = json.load(open(sys.argv[1])); ROOT = Path(sys.argv[1]).resolve().parent
rp = lambda x: str((ROOT / x).resolve()) if x and not Path(x).is_absolute() else x
PAGE = A / "games" / f"{P['page']}.html"
Q = "name=" + urllib.parse.quote(P.get("name", "")) if P.get("name") else ""
if len(sys.argv) > 2 and sys.argv[2] == "test":
    d = Path(rp(P["out"])).parent / "game_test"; K.run(["node", str(A / "games/render.js"), str(PAGE), str(d), Q, sys.argv[3]]); print("test kadrları:", d); sys.exit()
OUT = K.next_version(rp(P["out"])); WORK = OUT.parent / (OUT.stem + "_work"); FR = WORK / "fr"
K.run(["node", str(A / "games/render.js"), str(PAGE), str(FR), Q])
J = json.load(open(FR / "events.json")); D = J["T"]["TOTAL"]

# --- sintez səslər (hadisə siyahısından, kadrla dəqiq sinxron)
SR = K.SR; N = int(D * SR); o = np.zeros(N); rng = np.random.default_rng(3)
def add(sig, at, g=1.0):
    i = int(at * SR); n = min(len(sig), N - i)
    if n > 0: o[i:i + n] += sig[:n] * g
def env(n, a=.002, dec=.05): t = np.arange(n) / SR; return np.minimum(1, t / a) * np.exp(-t / dec)
def tone(fr, dur, dec, a=.003): n = int(dur * SR); t = np.arange(n) / SR; return sum(np.sin(2 * np.pi * f * t) * w for f, w in fr) * env(n, a, dec)
def tick(f):
    n = int(.05 * SR); t = np.arange(n) / SR; nz = np.convolve(rng.standard_normal(n), [1, -1], 'same')
    return .5 * nz * env(n, .0005, .004) + np.sin(2 * np.pi * f * t) * env(n, .0005, .012)
def sweep(dur, f0, f1):
    n = int(dur * SR); nz = rng.standard_normal(n); f = np.linspace(f0, f1, n); s = nz * .35 + np.sin(2 * np.pi * np.cumsum(f) / SR) * .25
    return np.convolve(s, np.ones(24) / 24, 'same') * np.sin(np.pi * np.linspace(0, 1, n)) ** 2
SC = [523.25, 587.33, 659.25, 783.99, 880, 1046.5, 1174.66, 1318.5, 1567.98, 1760, 2093, 2349.3]
for e in J["E"]:
    t, ty, v = e["t"], e["type"], e["v"]
    if ty == "pop": add(tone([(330, 1), (660, .4)], .2, .06), t, .25)
    elif ty == "pop2": add(tone([(520 + v * 25, 1), (1040 + v * 50, .3)], .12, .03), t, .12)
    elif ty == "tick": add(tick(2000), t, .3)
    elif ty == "tickhi": add(tick(2700), t, .5); add(tone([(1200, 1)], .08, .02), t, .12)
    elif ty.startswith("tick"): k = int(ty[4:]); add(tick([1900, 2300, 2800][k]), t, [.3, .38, .45][k])
    elif ty == "whoosh": add(sweep(.35, 300, 1500), t, .5)
    elif ty == "swish": add(sweep(.25, 500, 2000), t, .35)
    elif ty == "flip": add(sweep(.12, 1500, 3000), t, .4); add(tick(1500), t + .1, .2)
    elif ty == "ding": f = SC[min(v * 2 + 2, len(SC) - 1)]; add(tone([(f, 1), (f * 2, .25), (f * 1.5, .2)], .8, .25), t, .3)
    elif ty == "note": f = SC[v % len(SC)]; add(tone([(f, 1), (f * 2, .25)], .5, .13), t, .2)
    elif ty == "bell": add(tone([(523.25, 1), (659.25, .8), (783.99, .7), (1046.5, .35)], 1.6, .45), t, .3)
o[-int(.4 * SR):] *= np.linspace(1, 0, int(.4 * SR))
sfx = np.stack([o, o], 1); sfx *= 10 ** ((-20 - K.rms_db(sfx[np.abs(sfx).max(1) > 1e-4])) / 20)  # səsli hissə ≈ −20 dBFS RMS
mix = sfx
if P.get("music"):
    mus = K.load(rp(P["music"])); bed = K.music_bed(mus, N, None, level=P.get("music_level", -27), fade_in=.4, fade_out=1.6)
    mix = sfx + bed
MIX, FIN = WORK / "mix.wav", WORK / "final.wav"; K.save(mix, MIX); K.finalize(MIX, FIN, I=-15)

VID = WORK / "v.mp4"
K.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", str(FR / "%05d.jpg"), "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "4.5M",
       "-bufsize", "9M", "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p", "-r", "30", "-g", "60", str(VID)])
K.export_ig(VID, FIN, OUT, copy_video=True)
K.cover(OUT, P.get("cover_t", 3.0), OUT.parent / (OUT.stem + "_kadr.jpg"))
shutil.rmtree(FR)  # kadrlar böyükdür, nəticədən sonra silinir
q = K.qa(OUT); json.dump(q, open(OUT.parent / (OUT.stem + "_qa.json"), "w"), ensure_ascii=False, indent=1)
print(f"{'OK' if q['ok'] else 'YOXLA'} {OUT} {q}")
