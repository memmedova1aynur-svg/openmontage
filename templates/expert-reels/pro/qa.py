"""QA darvazası: hazır video göndərilməzdən əvvəl ölçülə bilən bütün səhvləri yoxlayır.

İstifadə: python3 qa.py <video.json> <hazır.mp4>
Çıxış kodu 0 = KEÇDİ, 1 = KEÇMƏDİ. Nəticə həm ekrana, həm <W_DIR>/qa.json-a yazılır.

Yoxlamalar (hər biri bu layihədə real rast gəlinmiş səhvdən doğub):
  freeze    danışan görünərkən görüntü donur (səs gedir)       → FAIL
  cut       kəsim danışığın ortasına düşür (söz yarımçıq)        → FAIL
  loud      ümumi səs səviyyəsi / pik / klik                     → FAIL
  sfx       qadağan səs effekti (pop, "öskürək" və s.)           → FAIL
  color     qadağan rəng (laym) konfiqdə                         → FAIL
  card      kartdakı son bənd < minItemShow saniyə görünür       → FAIL
  dup       tək təkrarlanan kadr (ilişmə hissi)                  → WARN
"""
import json, os, re, subprocess, sys
from pathlib import Path
import numpy as np

A = Path(__file__).resolve().parent
HOUSE = json.load(open(A / "house.json")); Q = HOUSE["qa"]
raw = json.load(open(sys.argv[1])); MP4 = sys.argv[2]
CFG = {**HOUSE["common"], **HOUSE["ad" if raw.get("ad") or raw.get("type") == "ad" else "talk"], **raw}
n = CFG["n"]; pid = CFG.get("pid") or f"xeyyam-video-{n}"
DATA = Path(os.environ.get("MONTAJ_DATA_DIR", "/root/montaj-data"))
WORK = Path(os.environ.get("PRO_WORK", str(DATA / "plans" / "pro"))); W_DIR = WORK / f"v{n}"
FULL_OVER = {"lower", "top", "topchips"}
res = {"fail": [], "warn": [], "info": {}}


def ff_raw(args, shape):
    p = subprocess.run(["ffmpeg", "-v", "error", *args, "-f", "rawvideo", "-"], capture_output=True)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, *shape).astype(np.int16)


# --- səhnələr: tam ekran kart intervalları (danışan görünmür) ---
SC = json.load(open(W_DIR / "scenes.json"))["scenes"]
full = [(s["t0"] + 0.2, s["t0"] + s["n"] / 30 - 0.2) for s in SC if s["kind"] not in FULL_OVER and s["kind"] != "split"]
in_full = lambda t: any(a <= t <= b for a, b in full)

# --- 1. donma: üz bölgəsi (yuxarı-orta) hərəkətsiz, amma tam ekran kart deyil ---
face = ff_raw(["-i", MP4, "-vf", "crop=480:520:300:250,scale=96:104,format=gray"], (104, 96))
d = np.abs(np.diff(face, axis=0)).mean(axis=(1, 2))
dur = len(face) / 30
runs, run = [], 0
for i, v in enumerate(d):
    t = (i + 1) / 30
    if v < 0.25 and not in_full(t) and t < dur - 1.2: run += 1
    else:
        if run >= Q["freezeFrames"]: runs.append((round((i - run + 1) / 30, 2), run))
        run = 0
if runs: res["fail"].append({"freeze": runs})
dups = [round((i + 1) / 30, 2) for i in range(1, len(d) - 1) if d[i] < 0.12 and d[i - 1] > 0.6 and d[i + 1] > 0.6 and not in_full((i + 1) / 30)]
if dups: res["warn"].append({"dup": dups})

# --- 2. kəsimlər: mənbədə kəsim nöqtəsi danışığa düşürmü ---
pj = json.load(open(DATA / "projects" / pid / "montaj.json"))
def find(o, key):
    if isinstance(o, dict):
        if key in o: return o[key]
        for v in o.values():
            r = find(v, key)
            if r is not None: return r
md = find(pj, "media"); md = {m["id"]: m for m in (md if isinstance(md, list) else md.values())}
cl = [c for c in find(pj, "clips") if c.get("track") == "v1" and not md[c["media"]].get("isImage")]
if cl:
    src = DATA / "projects" / pid / md[cl[0]["media"]]["file"]
    au = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    s = np.frombuffer(au, np.int16).astype(float) / 32768
    db = lambda a, b: 20 * np.log10(np.sqrt((s[max(0, int(a * 16000)):int(b * 16000)] ** 2).mean()) + 1e-9)
    bad, t = [], 0.0
    for i, c in enumerate(cl):
        L = c["srcOut"] - c["srcIn"]
        if i > 0 and db(c["srcIn"], c["srcIn"] + 0.03) > -30: bad.append(("başlanğıc", round(t, 2)))
        if i < len(cl) - 1 and db(c["srcOut"] - 0.03, c["srcOut"]) > -30: bad.append(("son", round(t + L, 2)))
        t += L
    if bad: res["fail"].append({"cut": bad})
    res["info"]["cuts"] = len(cl) - 1

# --- 3. səs: LUFS, pik, klik ---
ln = subprocess.run(["ffmpeg", "-v", "info", "-i", MP4, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", ln)[-1]); pk = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", ln)[-1])
res["info"].update(lufs=I, peak=pk)
if not (Q["lufs"][0] <= I <= Q["lufs"][1]) or pk > Q["peakMax"]: res["fail"].append({"loud": [I, pk]})
au = subprocess.run(["ffmpeg", "-v", "error", "-i", MP4, "-ac", "1", "-ar", "48000", "-f", "s16le", "-"], capture_output=True).stdout
x = np.frombuffer(au, np.int16).astype(float) / 32768
clicks = int((np.abs(np.diff(x)) > 0.5).sum())
if clicks: res["fail"].append({"click": clicks})

# --- 4. səs effektləri ---
plan = json.load(open(W_DIR / "plan.json"))
badsfx = [(x["kind"], x["t"]) for x in plan.get("sfx", []) if x["kind"] in HOUSE["forbiddenSfx"]]
if badsfx: res["fail"].append({"sfx": badsfx})
res["info"]["sfx"] = len(plan.get("sfx", []))

# --- 5. qadağan rəng ---
txt = open(sys.argv[1]).read().upper() + json.dumps([s["p"].get("pal", {}) for s in SC]).upper()
badc = [c for c in HOUSE["forbiddenColors"] if c.upper() in txt]
if badc: res["fail"].append({"color": badc})

# --- 6. kart bəndləri kifayət qədər görünür ---
short = []
for s_ in SC:
    p = s_["p"]; end = s_["n"] / 30 - (0.45 if p.get("soft") else 0.3)
    anc = [v for k in ("ts", "lineAt", "subTs") for v in p.get(k, []) if isinstance(v, (int, float))]
    if anc and end - max(anc) < Q["minItemShow"]: short.append((s_["i"], s_["kind"], round(end - max(anc), 2)))
if short: res["fail"].append({"card": short})

res["info"]["duration"] = round(dur, 2)
json.dump(res, open(W_DIR / "qa.json", "w"), ensure_ascii=False, indent=1)
status = "KEÇDİ" if not res["fail"] else "KEÇMƏDİ"
print(f"QA {status}: {Path(MP4).name} | {json.dumps(res, ensure_ascii=False)}")
sys.exit(1 if res["fail"] else 0)
