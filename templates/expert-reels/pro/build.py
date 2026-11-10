"""PRO montaj qurucusu: danışığa sadiq mətn → sıx kəsim → səhnələr (sözə bağlı) → plan → render → QA.

İstifadə:  python3 build.py <video.json> [all|plan]
Ev qaydaları house.json-dan avtomatik qatılır (video konfiqi üstün gəlir).
Mühit: PRO_WORK (iş qovluğu), PRO_OUT (hazır videolar), MONTAJ_DATA_DIR."""
import json, re, sys, glob, copy, uuid, subprocess, difflib, os, shutil, time
from pathlib import Path
A = Path(__file__).resolve().parent
HOUSE = json.load(open(A / "house.json"))
_raw = json.load(open(sys.argv[1]))
def _brand(name):
    """Müştəri brend kiti: <PRO_BRANDS | repo/instagram-clients>/<ad>/brand_kit.json (müştəri faylları repoya düşmür)."""
    if not name: return {}
    for d in (os.environ.get("PRO_BRANDS"), str(A.parent.parent.parent / "instagram-clients")):
        f = Path(d or "", name, "brand_kit.json")
        if d and f.exists(): return json.load(open(f))
    raise SystemExit(f"Brend kiti tapılmadı: {name} (instagram-clients/{name}/brand_kit.json)")
BRAND = _brand(_raw.get("brand"))
THEME = _raw.get("theme") or BRAND.get("theme")
CFG = {**HOUSE["common"], **HOUSE["ad" if _raw.get("ad") or _raw.get("type") == "ad" else "talk"], **HOUSE.get("themes", {}).get(THEME, {}), **BRAND.get("cfg", {}), **_raw}
n = CFG["n"]; pid = CFG.get("pid") or f"xeyyam-video-{n}"
STEP = sys.argv[2] if len(sys.argv) > 2 else "all"
DATA = Path(os.environ.get("MONTAJ_DATA_DIR", "/root/montaj-data"))
P = DATA / "projects" / pid
WORK = Path(os.environ.get("PRO_WORK", str(DATA / "plans" / "pro"))); WORK.mkdir(parents=True, exist_ok=True)
W_DIR = WORK / f"v{n}"; W_DIR.mkdir(exist_ok=True)
SCR = os.environ.get("PRO_OUT", str(DATA / "out" / "pro")); Path(SCR).mkdir(parents=True, exist_ok=True)
REPO = A.parent.parent.parent
ENV = {**os.environ, "MONTAJ_DATA_DIR": str(DATA), "MONTAJ_OUT_DIR": str(DATA / "out")}
T_START = time.time()
def tick(msg): print(f"[{time.time() - T_START:6.1f}s] {msg}", flush=True)
def _crop():
    """Kadraj: konfiqdə 'crop' varsa o, yoxsa framefix nəticəsi (storyboard_draft.json)."""
    if CFG.get("crop"): return CFG["crop"]
    cj = WORK / "crops.json"
    if cj.exists() and str(n) in json.load(open(cj)): return json.load(open(cj))[str(n)]
    fr = next(iter(json.load(open(P / "storyboard_draft.json"))["frames"].values()))
    k = (fr.get("keys") or [{}])[0]
    return {"s": float(fr.get("s") or 0.88), "cx": float(k.get("cx", 0.5)), "cy": float(k.get("cy", 0.44))}
CROPS = {str(n): _crop()}
norm = lambda w: re.sub(r"[^\wəğıöüşç]", "", w.lower().replace("İ", "i").replace("I", "ı"))
af = [x for x in (P / "analysis").glob("*.json")][0]
src = sorted((P / "media/originals").glob(af.stem + ".*"))[0]  # əsas video — analizin media ID-si ilə (B-roll faylları qarışmasın)
bk = Path(str(af) + ".asr_backup")
if not bk.exists(): bk.write_bytes(af.read_bytes())
a = json.load(open(bk)); kw, ks, ke = ("word", "start", "end") if "word" in a["words"][0] else ("w", "s", "e")
ASR = [{"w": w[kw], "s": w[ks], "e": w[ke]} for w in a["words"]]
mid = a.get("mediaId") or af.stem
# 1) danışığa sadiq mətn — vaxtlar ASR-dən
S = CFG["text"].split(); Aw = [norm(w["w"]) for w in ASR]; Bw = [norm(x) for x in S]; WORDS = []
for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, Aw, Bw, autojunk=False).get_opcodes():
    if op == "equal" or (op == "replace" and i2 - i1 == j2 - j1):
        WORDS += [{**ASR[i1 + k], "w": S[j1 + k]} for k in range(i2 - i1)]
    elif op in ("replace", "insert"):
        lo, hi = (ASR[i1]["s"], ASR[i2 - 1]["e"]) if i2 > i1 else ((ASR[i1 - 1]["e"],) * 2 if i1 else (0, 0.2))
        toks = S[j1:j2]; tot = sum(len(t) + 1 for t in toks); x = lo
        for t in toks:
            d = (hi - lo) * (len(t) + 1) / tot; WORDS.append({"w": t, "s": round(x, 3), "e": round(x + d, 3)}); x += d
# 2) sıx kəsim: ölçülmüş sükutlar (≥0.3 s) 0.18 s-ə qədər qısaldılır, sonda 1 s
out = subprocess.run(["ffmpeg", "-v", "info", "-i", str(src), "-af", f"silencedetect=n=-42dB:d={CFG.get('tight',{}).get('d',0.3)}", "-f", "null", "-"], capture_output=True, text=True).stderr
ss = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", out)]; se = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", out)]
DUR = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)], capture_output=True, text=True).stdout)
last_e = WORDS[-1]["e"]; first_s = WORDS[0]["s"]
REM = []; start = 0.0
for s0, e0 in zip(ss, se):
    KA, KB = CFG.get("tight", {}).get("after", 0.2), CFG.get("tight", {}).get("before", 0.15)
    if s0 <= 0.05: start = max(0.0, e0 - KB); continue
    if s0 > last_e - 0.1: continue
    if (e0 - KB) - (s0 + KA) >= 0.06: REM.append((round(s0 + KA, 3), round(e0 - KB, 3)))  # sözün başı (B, P, T partlayışı) da qorunur  # sözün sonu (zəif samitlər) qorunur
for r in CFG.get("extraCut", []): REM.append(tuple(r))
REM.sort()
END = min(DUR, last_e + 1.0); HOLD = round(max(0.0, 1.0 - (DUR - last_e)), 2) if DUR - last_e < 1.0 else 0.0
def mk(rem):
    out_, x_ = [], start
    for s0, e0 in rem: out_.append((x_, s0)); x_ = e0
    out_.append((x_, END)); return out_
segs = mk(REM)
while any(e0 - s0 < 0.15 for s0, e0 in segs):  # çox qısa parça qalmasın — ondan əvvəlki kəsim ləğv olunur
    k = next(i for i, (s0, e0) in enumerate(segs) if e0 - s0 < 0.15); REM.pop(max(0, k - 1)); segs = mk(REM)
MAP = []; t = 0.0
for s0, e0 in segs: MAP.append((s0, e0, t)); t += e0 - s0
TOTAL = t
def clamp(w):
    s, e = w["s"], w["e"]
    if any(g0 - 0.01 <= s and e <= g1 + 0.01 for g0, g1 in segs): return w
    best = max(segs, key=lambda g: min(e, g[1]) - max(s, g[0])); ns, ne = max(s, best[0] + 0.005), min(e, best[1] - 0.005)
    if ne - ns < 0.08: ns, ne = (best[0] + 0.005, best[0] + 0.2) if s < best[0] else (best[1] - 0.2, best[1] - 0.005)
    return {**w, "s": round(ns, 3), "e": round(ne, 3)}
WORDS = [clamp(w) for w in WORDS]
def tl(v):
    for s0, e0, b in MAP:
        if s0 - 0.02 <= v <= e0 + 0.02: return round(b + min(max(v, s0), e0) - s0, 3)
    for s0, e0, b in MAP:
        if v < s0: return round(b, 3)
    return round(TOTAL, 3)
NW = [norm(w["w"]) for w in WORDS]
def find(phrase, after=0):
    toks = [norm(x) for x in phrase.split()]
    for i in range(after, len(NW) - len(toks) + 1):
        if NW[i:i + len(toks)] == toks: return i
    raise SystemExit(f"ifadə tapılmadı: {phrase}")
def at_word(ph, after=0): i = find(ph, after); return tl(WORDS[i]["s"]), i
def end_word(ph, after=0): i = find(ph, after) + len(ph.split()) - 1; return tl(WORDS[i]["e"]), i
if STEP in ("all", "prep", "render"):
    a2 = json.load(open(bk)); a2["words"] = [{kw: w["w"], ks: w["s"], ke: w["e"]} for w in WORDS]; a2["text"] = " ".join(w["w"] for w in WORDS)
    json.dump(a2, open(af, "w"), ensure_ascii=False)
    pj = json.load(open(P / "montaj.json"))
    if pj.get("subtitles") and pj["subtitles"].get("words"): pj["subtitles"]["words"][mid] = WORDS; pj["subtitles"]["corrections"] = []; json.dump(pj, open(P / "montaj.json", "w"), ensure_ascii=False)
    d = json.load(open(P / "storyboard_draft.json")); tpl = d["cards"][0]; cards = []
    rng = lambda lo, hi: [w for w in WORDS if w["s"] >= lo - 0.01 and w["e"] <= hi + 0.01]
    for s0, e0 in segs:
        c = copy.deepcopy(tpl); c.update(id="card_" + uuid.uuid4().hex[:8], srcIn=round(s0, 3), srcOut=round(e0, 3), include=True, role="body")
        c["words"] = rng(s0, e0); c["transcript"] = " ".join(w["w"] for w in c["words"])
        if "text" in c: c["text"] = c["transcript"]
        cards.append(c)
    d["cards"] = cards
    for c in d.get("candidates", {}).get(mid, []): c["words"] = rng(c["srcIn"], c["srcOut"]); c["text"] = " ".join(w["w"] for w in c["words"])
    cr = CROPS[str(n)]
    for k in d["frames"]: d["frames"][k] = {**d["frames"][k], "aspect": "source", "mode": "manual", "s": cr["s"], "baseW": 1, "baseH": 1, "keys": [{"t": 0.0, "cx": cr["cx"], "cy": cr["cy"]}], "autoFix": False}
    json.dump(d, open(P / "storyboard_draft.json", "w"), ensure_ascii=False)
    print(f"söz {len(WORDS)}/{sum(len(c['words']) for c in cards)}; müddət {TOTAL:.2f} s; son saxlama +{HOLD}")

# ---------------- PRO: səhnələr, kompozit, plan ----------------
PALS = {
 "forest": {"bg":"#16533F","bg2":"#0F3B2C","bg3":"#08241A","acc":"#6CC57E","txt":"#F4F8F5","ink":"#0F3B2C","paper":"#FFFFFF","paper2":"#E3F1E6","muted":"#9FB8A9"},
 "charcoal": {"bg":"#363D39","bg2":"#232826","bg3":"#121514","acc":"#6CC57E","txt":"#F2F4F2","ink":"#1D2220","paper":"#FFFFFF","paper2":"#E3EBE5","muted":"#9CA49F"},
 "lime": {"bg":"#8ED69C","bg2":"#6CC57E","bg3":"#4FAE63","acc":"#0F3B2C","txt":"#0F3B2C","ink":"#6CC57E","paper":"#0F3B2C","paper2":"#08241A","muted":"#2F6B45"},
 "adgreen": {"bg":"#1C6B50","bg2":"#0F3B2C","bg3":"#08241A","acc":"#6CC57E","txt":"#FFFFFF","ink":"#0F3B2C","paper":"#FFFFFF","paper2":"#E3F1E6","muted":"#A8C4B5"},
 "cream": {"bg":"#EAF4EC","bg2":"#FFFFFF","bg3":"#E1EEE4","acc":"#3E9E57","txt":"#0F3B2C","ink":"#0F3B2C","paper":"#FFFFFF","paper2":"#DCEBDF","muted":"#5E7266"},
 "teal": {"bg":"#1A6E69","bg2":"#0E4D4A","bg3":"#062C2A","acc":"#6CC57E","txt":"#F1F7F4","ink":"#0E4D4A","paper":"#FFFFFF","paper2":"#DDEBE6","muted":"#9CC2B9"},
 "sage": {"bg":"#5F7C56","bg2":"#3F5B3A","bg3":"#24361F","acc":"#B5E9CF","txt":"#F7FAF6","ink":"#2F4A2B","paper":"#FFFFFF","paper2":"#E0EBDD","muted":"#C3CFB4"},
 "midnight": {"bg":"#174A53","bg2":"#0B2E33","bg3":"#05181B","acc":"#6CC57E","txt":"#EEF6F5","ink":"#0B2E33","paper":"#FFFFFF","paper2":"#DCE8E6","muted":"#93B4B2"},
 "editorial": {"bg":"#2B1D1A","bg2":"#1E1412","bg3":"#120B0A","acc":"#7A1E3A","acc2":"#C9687F","txt":"#F4EDE4","ink":"#2B1D1A","paper":"#F3ECDF","paper2":"#E4D8C4","muted":"#A8968A"},
 "emerald": {"bg":"#1E8564","bg2":"#11604A","bg3":"#09382B","acc":"#9DDCAA","txt":"#F2FAF5","ink":"#0B4434","paper":"#FFFFFF","paper2":"#DDEEE3","muted":"#A9D6C2"}}
if BRAND.get("palette"):  # brend rəngləri seçilmiş palitranın üstünə yazılır
    PALS["brand"] = {**PALS[CFG.get("pal", "forest")], **BRAND["palette"]}; CFG["pal"] = "brand"
LOOKS = {  # rəng presetləri (yalnız danışan kadra; kartlara toxunmur)
    "warm_cinematic": {"temperature": 5700, "contrast": 1.06, "saturation": 0.92, "depth": 1.0, "highlights": 0.6, "shadows": 0.1, "sharpen": 0.25},
    "clean_studio": {"brightness": 0.015, "contrast": 1.03, "vibrance": 0.15, "highlights": 0.5, "sharpen": 0.3},
    "natural": {"vibrance": 0.1, "shadows": 0.3, "highlights": 0.3, "sharpen": 0.2},
    "moody": {"temperature": 5400, "contrast": 1.10, "saturation": 0.85, "depth": 1.5, "gamma": 0.97, "sharpen": 0.25}}
PAL = PALS[CFG["pal"]]; FPS = 30
OVER = {"lower", "top", "topchips", "equote", "esticker", "ename"}
SC = []; cur = 0
for i, sc in enumerate(CFG["scenes"]):
    t0, wi = at_word(sc["from"], cur); t0 = max(0.0, t0 - sc.get("lead", 0.1))
    t1 = (TOTAL + HOLD) if sc.get("toEnd") else t0 + sc["dur"]
    pal = PALS[sc["pal"]] if sc.get("pal") else PAL
    p = copy.deepcopy(sc.get("p", {})); p["pal"] = pal
    if CFG.get("softFx"): p["soft"] = True
    if CFG.get("safe"): p["safe"] = CFG["safe"]
    dur = t1 - t0
    for key in ("ts", "lineAt"):
        if key in p: p[key] = [round(max(0.05, at_word(v, wi)[0] - t0), 3) if isinstance(v, str) else v for v in p[key]]
    for key in ("dotAt", "switchAt", "start", "split", "hl", "u", "close", "btnAt", "badgeAt", "noteAt", "bwAt"):
        if isinstance(p.get(key), str): p[key] = round(max(0.05, at_word(p[key], wi)[0] - t0), 3)
    if "subTs" in p: p["subTs"] = [round(max(0.05, at_word(v, wi)[0] - t0), 3) if isinstance(v, str) else v for v in p["subTs"]]
    anc = [v for key in ("ts", "lineAt", "subTs") for v in p.get(key, [])] + [p[key] for key in ("dotAt", "switchAt", "split", "hl", "u", "close", "btnAt", "badgeAt", "noteAt", "bwAt") if isinstance(p.get(key), (int, float))]
    anc_s = [v for key in ("ts", "lineAt", "subTs") for v in p.get(key, [])]  # yalnız yazı anchor-ları (keçid nöqtələri yox)
    if anc_s and min(anc_s) > 0.6 and not sc.get("noshift") and sc["kind"] != "transform":  # kart ilk açar söz deyiləndə açılır
        sh = min(anc_s) - 0.2; t0 += sh; t1 = max(t1, t0 + 1.2) if not sc.get("toEnd") else t1
        for key in ("ts", "lineAt", "subTs"):
            if key in p: p[key] = [round(v - sh, 3) for v in p[key]]
        for key in ("dotAt", "switchAt", "split", "hl", "u", "close", "btnAt", "badgeAt", "noteAt", "bwAt"):
            if isinstance(p.get(key), (int, float)): p[key] = round(p[key] - sh, 3)
        anc = [a_ - sh for a_ in anc]
    if sc.get("until"): t1 = max(t1, end_word(sc["until"], wi)[0] + 0.35)
    TAIL = 1.0 + (0.45 if CFG.get("softFx") else 0.3)  # son bənd ən az 1 s tam görünsün + bağlanma keçidi
    if sc["kind"] not in (*OVER, "split", "eseries") and not sc.get("toEnd") and not sc.get("hold") and t1 - t0 > 4.5: t1 = t0 + 4.5  # tam ekran kart uzun qalmır
    if anc and not sc.get("toEnd"): t1 = max(t1, t0 + max(anc) + TAIL)  # kart yazı deyilib görünənə qədər qalır (limitdən üstündür)
    SC.append({"i": i, "kind": sc["kind"], "t0": round(t0, 3), "t1": round(t1, 3), "p": p, "sfx": sc.get("sfx", [])})
    cur = wi
for a_, b_ in zip(SC, SC[1:]):
    if a_["t1"] > b_["t0"] - 0.04:
        anc_ = [v for k in ("ts", "lineAt", "subTs") for v in a_["p"].get(k, []) if isinstance(v, (int, float))]
        need = a_["t0"] + (max(anc_) if anc_ else 0) + 1.0 + (0.45 if CFG.get("softFx") else 0.3)
        if need > b_["t0"] - 0.04 and b_["kind"] in OVER:  # növbəti kiçik kartı sürüşdür, bəndlər yarımçıq qalmasın
            sh = need + 0.04 - b_["t0"]; b_["t0"] = round(b_["t0"] + sh, 3); b_["t1"] = round(max(b_["t1"], b_["t0"] + 1.2), 3)
            for k in ("ts", "lineAt", "subTs"):
                if k in b_["p"]: b_["p"][k] = [round(max(0.05, v - sh), 3) if isinstance(v, (int, float)) else v for v in b_["p"][k]]
        a_["t1"] = round(min(a_["t1"], b_["t0"] - 0.04), 3)
for s_ in SC:
    s_["dur"] = round(s_["t1"] - s_["t0"], 3); s_["n"] = int(round(s_["dur"] * FPS)); s_["dir"] = str(W_DIR / f"fr_{s_['i']:02d}")
json.dump({"scenes": SC, "total": TOTAL, "hold": HOLD}, open(W_DIR / "scenes.json", "w"), ensure_ascii=False, indent=1)
for s_ in SC: print(f"{s_['t0']:6.2f}-{s_['t1']:6.2f} ({s_['dur']:.1f}) {s_['kind']:8s} {(s_['p'].get('type') or '')} {json.dumps({k:v for k,v in s_['p'].items() if k!='pal'}, ensure_ascii=False)[:80]}")
if STEP == "plan": raise SystemExit
sys.path.insert(0, str(REPO)); os.environ.update(ENV)
from montaj import store
from montaj.render import color_filters, sharpen_filter, _even, zoom_filter
def run(args, **kw):
    r = subprocess.run(args, cwd=str(REPO), env=ENV, capture_output=True, text=True, **kw)
    return r
# 4) köhnə B-roll / musiqi / səhnə mediasını təmizlə
q = store.load(pid); keep = {mid}
drop = [m for m in q["media"] if m["id"] != mid and not m["id"].startswith("sfx_")]
for m in drop:
    for f in [P / m.get("file", "x"), P / "media/derived" / f"{m['id']}.mp4", P / "media/derived" / f"{m['id']}.peaks.json"]:
        try: f.unlink()
        except Exception: pass
ids = {m["id"] for m in drop}
q["media"] = [m for m in q["media"] if m["id"] not in ids]; q["clips"] = [c for c in q["clips"] if c.get("media") not in ids]
store.save(pid, q, store.load(pid)["revision"]); print("təmizləndi:", len(drop), "media")
# 5) kadrlar (HTML)
tick("kart kadrları")
jobs = [{"scene": s_["kind"], "dur": s_["dur"], "p": s_["p"], "dir": s_["dir"]} for s_ in SC if not Path(s_["dir"], f"{s_['n']-1:05d}.png").exists()]
if jobs:
    jf = W_DIR / "jobs.json"; json.dump(jobs, open(jf, "w"), ensure_ascii=False)
    r = subprocess.run(["node", str(A / "render.js"), str(jf)], cwd=A, env=ENV, capture_output=True, text=True)
    if r.returncode: raise SystemExit("kadr render xətası: " + r.stderr[-800:])
tick("kart kadrları hazır")
# 6) son saxlama kadrı + plan (musiqisiz) + choose
cr = CROPS[str(n)]; endimg = W_DIR / f"v{n}_endhold.png"
if HOLD > 0:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-sseof", "-0.1", "-i", str(src), "-frames:v", "1", "-vf",
                    f"crop=iw*{cr['s']}:ih*{cr['s']}:max(0\\,min(iw-ow\\,iw*{cr['cx']}-ow/2)):max(0\\,min(ih-oh\\,ih*{cr['cy']}-oh/2)),hflip,scale=1080:1920:flags=lanczos", str(endimg)], check=True)
    run(["python", "-m", "montaj.session", "add-broll", pid, "--file", str(endimg)])
SFX = []
def sfx(kind, t, vol):
    t = round(max(0.0, t), 2)
    if all(abs(t - x["t"]) >= 0.18 for x in SFX): SFX.append({"kind": kind, "t": t, "vol": vol})
AD = CFG.get("ad", False)
sfx("impact", 0.0, 0.42 if AD else 0.32); sfx("shimmer", 0.05, 0.22)
for s_ in SC:
    k, t0, p = s_["kind"], s_["t0"], s_["p"]
    if k in OVER:
        for v in p.get("ts", []): sfx("pop", t0 + v, 0.28)
        if p.get("dot"): sfx("ding", t0 + p.get("dotAt", 0.8), 0.09)
        if p.get("btn"): sfx("pop", t0 + p.get("btnAt", 0.5), 0.35)
    elif k == "split":
        sfx("swish", t0, 0.32)
        for v in p.get("ts", []): sfx("pop" if AD else "tick2", t0 + v, 0.26)
        if p.get("type") == "blocks": sfx("pop", t0 + p["split"], 0.32)
    else:
        if AD: sfx("riser", t0 - 0.85, 0.18)
        sfx("whoosh2", t0 - 0.16, 0.24)
        if AD or k == "stack": sfx("impact", t0 + 0.05, 0.3)
        for v in p.get("ts", [])[1:]: sfx("tick2", t0 + v, 0.24)
        if p.get("switchAt") is not None: sfx("whoosh", t0 + p["switchAt"] - 0.1, 0.3)
        if p.get("u") is not None: sfx("swish", t0 + p["u"], 0.3)
    for e in s_.get("sfx", []): sfx(e[0], t0 + e[1], e[2])
if CFG.get("sfxset") == "premium":  # tonal, yumşaq, aşağı səviyyəli effektlər (küy/xışıltı yoxdur)
    MAPK = {"impact": "p_sub", "shimmer": "p_bloom", "whoosh2": "p_swell", "whoosh": "p_swell", "swish": "p_swell",
            "riser": "p_rise", "pop": "p_glint", "tick2": "p_tap", "ding": "p_glint"}
    VS = CFG.get("sfxScale", 0.5)
    SFX = [{**x, "kind": MAPK.get(x["kind"], x["kind"]), "vol": round(x["vol"] * VS, 3)} for x in SFX if x["kind"] != "riser"]
if CFG.get("sfxset") == "pro":  # küy əsaslı peşəkar effektlər: tonsuz whoosh, klik, yumşaq zərbə (melodik səs yoxdur)
    sys.path.insert(0, str(Path(__file__).resolve().parent)); import sfx_premium as _sp; _sp.ensure_pro()
    MAPK = {"impact": "pro_thump", "shimmer": "pro_air", "whoosh2": "pro_air", "whoosh": "pro_whoosh", "swish": "pro_paper",
            "pop": "pro_tick", "tick2": "pro_tick", "ding": "pro_tick"}
    VS = CFG.get("sfxScale", 0.5)
    SFX = [{**x, "kind": MAPK.get(x["kind"], x["kind"]), "vol": round(x["vol"] * VS, 3)} for x in SFX if x["kind"] != "riser"]
SFX = [x for x in SFX if x["kind"] not in CFG.get("dropSfx", [])]
SFX.sort(key=lambda x: x["t"])
plan = {"title": CFG["title"], "approach": "M01+M02+M03", "look": "W", "captions": {"enabled": True, "style": CFG["cap"]}, "zooms": [], "sfx": SFX, "graphics": [],
        "broll": ([{"name": endimg.name, "mode": "insert", "at": round(TOTAL - 0.06, 2), "dur": HOLD}] if HOLD > 0 else [])}
plan["corrections"] = list(BRAND.get("glossary", [])) + list(CFG.get("corrections", []))  # altyazı düzəliş lüğəti
MUS = CFG.get("music")
if MUS and MUS.get("file"):  # bütöv musiqi yatağı; danışıqda avtomatik aşağı enir (sidechain ducking)
    plan["music"] = [{"start": 0.0, "file": str(MUS["file"]), "volume": MUS.get("volume", 0.12), "fadeIn": MUS.get("fadeIn", 1.0), "fadeOut": MUS.get("fadeOut", 2.0), "duck": True}]
FULLR = [(s_["t0"], s_["t1"]) for s_ in SC if s_["kind"] not in OVER]
def _free(a, b): return all(b <= x0 or a >= x1 for x0, x1 in FULLR)
PUNCH = CFG.get("punch")
if PUNCH == "auto":  # cümlə başlanğıclarında, ən az 10 s aralıqla, tam ekran kartlardan kənarda yüngül yaxınlaşma
    last = -99.0
    for j, w in enumerate(WORDS[1:], 1):
        if WORDS[j - 1]["w"].rstrip().endswith((".", "?", "!")):
            a_ = tl(w["s"]); b_ = min(a_ + 2.2, TOTAL - 0.3)
            if a_ - last >= 10 and b_ - a_ > 1.0 and _free(a_, b_):
                plan["zooms"].append({"from": round(a_, 2), "to": round(b_, 2), "scale": CFG.get("punchScale", 1.08), "cy": 0.42}); last = a_
elif PUNCH:
    for z in PUNCH:
        a_, wi_ = at_word(z["from"]); b_ = end_word(z["until"], wi_)[0] + 0.2 if z.get("until") else a_ + z.get("dur", 2.0)
        if _free(a_, b_): plan["zooms"].append({"from": round(a_, 2), "to": round(min(b_, TOTAL - 0.3), 2), "scale": z.get("scale", 1.1), "cy": 0.42})
for br in CFG.get("broll", []):  # müştərinin öz kadrları (sinif, studiya) sözə bağlı
    r = run(["python", "-m", "montaj.session", "add-broll", pid, "--file", str(br["file"])])
    if r.returncode: raise SystemExit("b-roll: " + r.stderr[-400:])
    plan["broll"].append({"name": Path(br["file"]).name, "mode": br.get("mode", "cover"), "at": round(at_word(br["from"])[0], 2), "dur": br.get("dur", 2.5),
                          **({"srcIn": br["srcIn"]} if "srcIn" in br else {}), "volume": br.get("volume", 0)})
json.dump(plan, open(W_DIR / "plan.json", "w"), ensure_ascii=False, indent=1)
r = run(["python", "-m", "montaj.session", "choose", pid, str(W_DIR / "plan.json")])
print("\n".join(l for l in (r.stdout + r.stderr).splitlines() if "plan tətbiq" in l or "XƏTA" in l or "NƏ ET" in l or "Error" in l))
if r.returncode: raise SystemExit("choose xətası: " + r.stderr[-1500:])
# 7) güzgü + yumşaq kamera hərəkəti (push) — hər klip boyu yavaş yaxınlaşma
q = store.load(pid); PUSH = CFG.get("push", 1.045); k_ = 0
for c in q["clips"]:
    if c["track"] == "v1" and c["media"] == mid:
        c.setdefault("adjust", {})["mirror"] = True
        if CFG.get("look") in LOOKS: c["adjust"].update(LOOKS[CFG["look"]])
        fr = c.get("frame") or {}
        if fr.get("mode") in ("auto", "manual"):
            fr.pop("push", None); fr.pop("pull", None); fr["ease"] = True
            if CFG.get("glide"):  # bütün video boyu davamlı, bir istiqamətli yavaş yaxınlaşma
                fr.pop("z0", None); fr.pop("z1", None)
            elif k_ % 2 == 0: fr["push"] = PUSH   # yaxınlaşma …
            else: fr["pull"] = PUSH             # … növbəti klip həmin miqyasdan uzaqlaşır — kəsimdə sıçrayış yoxdur
            c["frame"] = fr
        k_ += 1
if CFG.get("glide"):
    G0, G1 = CFG["glide"]; acc_ = 0.0; vtot = sum(c["srcOut"] - c["srcIn"] for c in q["clips"] if c["track"] == "v1")
    for c in q["clips"]:
        if c["track"] != "v1": continue
        d_ = c["srcOut"] - c["srcIn"]; fr = c.get("frame") or {}
        if fr.get("mode") in ("auto", "manual") and c["media"] == mid:
            fr["z0"] = round(G0 + (G1 - G0) * acc_ / vtot, 5); fr["z1"] = round(G0 + (G1 - G0) * (acc_ + d_) / vtot, 5); c["frame"] = fr
        acc_ += d_
chain_ = CFG.get("speechChain") or ""
if CFG.get("muteGaps"):  # söz aralarında (danışan susanda) kənar səsləri −20 dB yumşaq azalt; danışığa toxunmur
    tw = sorted((tl(w["s"]), tl(w["e"])) for w in WORDS)
    gaps = [(e0 + 0.06, s1 - 0.04) for (_, e0), (s1, _) in zip(tw, tw[1:]) if s1 - e0 >= 0.18]
    gaps += [(tw[-1][1] + 0.08, TOTAL + HOLD + 1)] if tw else []
    r_ = 0.03; g_ = "+".join(f"clip(min((t-{a0:.3f})/{r_},({b0:.3f}-t)/{r_}),0,1)" for a0, b0 in gaps if b0 - a0 > 0.05)
    if g_: chain_ = f"volume='1-0.9*min(1,{g_})':eval=frame" + ("," + chain_ if chain_ else "")
if chain_: q["speechChain"] = chain_
else: q.pop("speechChain", None)
store.save(pid, q, store.load(pid)["revision"]); q = store.load(pid)
# 8) kompozit cover kliplər: danışan (əsas videonun eyni kadrı) + qrafika
from montaj import session as SS
vclips = SS.node_tl("videoClips", q); media = {m["id"]: m for m in q["media"]}
lay = []; acc = 0.0
for c in vclips: lay.append((c, acc)); acc += c["srcOut"] - c["srcIn"]
FY = CFG.get("fy", 0.41)
def piece_chain(c, a, b, cs, mode):
    m = media[c["media"]]; off = a - cs; d0 = c["srcIn"] + off; d1 = d0 + (b - a)
    adj = c.get("adjust") or {}; fr = c.get("frame") or {}
    if m.get("isImage"):
        f = [f"trim=duration={b-a:.4f}", "setpts=PTS-STARTPTS", "scale=1080:1920"]
        f += ["crop=1080*0.82:1080*0.82*1100/1080:1080*0.09:1920*" + f"{FY-0.42*0.82*1100/1920:.4f}", "scale=1080:1100:flags=lanczos"] if mode == "B" else []
        return f, "img"
    sk = d0 - max(0.0, d0 - 1.0)  # giriş -ss (d0-1) ilə açılır
    f = [f"trim=start={sk:.4f}:end={sk + (d1 - d0):.4f}", "setpts=PTS-STARTPTS"]
    if mode == "A":
        s = float(fr.get("s") or 1); k0 = (fr.get("keys") or [{}])[0]; cx, cy = k0.get("cx", .5), k0.get("cy", .45)
        f.append(f"crop=w=iw*{s:.5f}:h=ih*{s:.5f}:x='max(0,min(iw-ow,iw*{cx}-ow/2))':y='max(0,min(ih-oh,ih*{cy}-oh/2))'")
        pu = float(fr.get("push") or 1); pl = float(fr.get("pull") or 1)
        if fr.get("z0") is not None:
            D = max(0.1, c["srcOut"] - c["srcIn"]); z0, z1 = float(fr["z0"]), float(fr["z1"])
            f.append(zoom_filter(f"({z0:.5f}+{z1 - z0:.5f}*min(n_/30+{off:.4f},{D:.3f})/{D:.3f})"))
        elif pu > 1.005 or pl > 1.005:
            cwp, chp = _even(m["width"] * s), _even(m["height"] * s); D = max(0.1, c["srcOut"] - c["srcIn"])
            uu = f"min(n_/30+{off:.4f},{D:.3f})/{D:.3f}"; ee = f"(3*pow({uu},2)-2*pow({uu},3))" if fr.get("ease") else uu
            kk = f"(1+{pu-1:.4f}*{ee})" if pu > 1.005 else f"({pl:.4f}-{pl-1:.4f}*{ee})"
            f.append(zoom_filter(kk))
        if adj.get("mirror"): f.append("hflip")
        f += color_filters(adj) + ["scale=1080:1920:flags=lanczos"] + sharpen_filter(adj)
    else:
        cw = 0.80; ch = cw * m["width"] / m["height"] * 1100 / 1080 * (1080 / 1080)
        cx = CROPS[str(n)]["cx"]; ty = FY - 0.42 * ch
        f.append(f"crop=w=iw*{cw}:h=iw*{cw}*1100/1080:x='max(0,min(iw-ow,iw*{cx}-ow/2))':y='max(0,min(ih-oh,ih*{FY}-oh*0.42))'")
        if adj.get("mirror"): f.append("hflip")
        f += color_filters(adj) + ["scale=1080:1100:flags=lanczos"] + sharpen_filter(adj)
    return f, "vid"
def normalize_pngs(d):
    """Tam qeyri-şəffaf kadrlar RGB, qalanları RGBA saxlanılır; ffmpeg format dəyişəndə filtr qrafını sıfırlayıb
    danışan videonu dondururdu. Hamısını RGBA edirik."""
    from PIL import Image
    fs = sorted(glob.glob(f"{d}/*.png"))
    modes = {Image.open(f).mode for f in (fs[0], fs[len(fs) // 2], fs[-1])} if fs else set()
    if len(modes) == 1 and "RGBA" in modes and all(Image.open(f).mode == "RGBA" for f in fs[::5]): return
    for f in fs:
        im = Image.open(f)
        if im.mode != "RGBA": im.convert("RGBA").save(f, compress_level=1)
def composite(s_):
    T0, T1, N = s_["t0"], s_["t0"] + s_["n"] / FPS, s_["n"]; out = W_DIR / f"v{n}_c{s_['i']:02d}.mp4"
    pieces = [(c, max(T0, cs), min(T1, cs + c["srcOut"] - c["srcIn"]), cs) for c, cs in lay if cs < T1 - 0.001 and cs + c["srcOut"] - c["srcIn"] > T0 + 0.001]
    modes = ["A"] + (["B"] if s_["kind"] == "split" else [])
    inputs = ["-i", str(src)]; img_idx = None
    if any(media[c["media"]].get("isImage") for c, *_ in pieces):
        inputs += ["-loop", "1", "-framerate", "30", "-i", str(endimg)]; img_idx = 1
    g_idx = len(inputs) // 2 if img_idx is None else 2
    normalize_pngs(s_["dir"])
    inputs += ["-framerate", "30", "-start_number", "0", "-i", f"{s_['dir']}/%05d.png"]
    fl = []; nv = sum(1 for c, *_ in pieces if not media[c["media"]].get("isImage")) * len(modes); ni = sum(1 for c, *_ in pieces if media[c["media"]].get("isImage")) * len(modes)
    # hər video parçası öz girişi ilə (-ss dəqiq axtarış): tək girişin split+trim ilə bölünməsi parçaların sonunu "dondururdu"
    vin = []
    for md in modes:
        for c, a, b, cs in pieces:
            if media[c["media"]].get("isImage"): continue
            d0 = c["srcIn"] + (a - cs); vin.append(inputs.count("-i"))
            inputs[0:0] = []; inputs += ["-ss", f"{max(0.0, d0 - 1.0):.4f}", "-t", f"{(b - a) + 1.3:.4f}", "-i", str(src)]
    VIN = iter(vin)
    if ni: fl.append(f"[{img_idx}:v]split={ni}" + "".join(f"[si{i}]" for i in range(ni)) if ni > 1 else f"[{img_idx}:v]null[si0]")
    vi = ii = 0
    for md in modes:
        labs = []
        for j, (c, a, b, cs) in enumerate(pieces):
            ch, kind = piece_chain(c, a, b, cs, md)
            inl = f"{next(VIN)}:v" if kind == "vid" else f"si{ii}"
            if kind == "vid": vi += 1
            else: ii += 1
            lab = f"{md}{j}"; fl.append(f"[{inl}]" + ",".join(ch + ["setsar=1", "settb=1/90000,setpts=N/30/TB" if kind == "vid" else "fps=30,settb=1/90000,setpts=PTS-STARTPTS", "format=yuv420p"]) + f"[{lab}]"); labs.append(f"[{lab}]")
        fl.append("".join(labs) + f"concat=n={len(labs)}:v=1:a=0,tpad=stop_mode=clone:stop_duration=2,trim=end_frame={N},setpts=PTS-STARTPTS[{md}]")
    if "B" in modes:
        # sərt keçid (üst-üstə yarışəffaf üz yoxdur): B planı yalnız panel tam açıq olanda görünür
        fl.append(f"[B]pad=1080:1920:0:0:color={PAL['bg3']},format=rgba[Bf]")
        fl.append(f"[A][Bf]overlay=0:0:format=auto:ts_sync_mode=nearest:enable='between(t,0.2,{max(0.3, N/FPS-0.22):.3f})'[AB]"); base = "AB"
    else: base = "A"
    fl.append(f"[{g_idx}:v]format=rgba,settb=1/90000,setpts=N/30/TB[G]"); fl.append(f"[{base}][G]overlay=0:0:format=auto:ts_sync_mode=nearest,format=yuv420p[o]")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fl), "-map", "[o]", "-frames:v", str(N), "-r", "30",
                        "-c:v", "libx264", "-crf", "14", "-preset", os.environ.get("PRO_COMP_PRESET", "faster"), "-pix_fmt", "yuv420p", "-an", str(out)], capture_output=True, text=True)
    if r.returncode: raise SystemExit(f"kompozit xətası {out.name}: {r.stderr[-1500:]}")
    return out
tick("kompozitlər")
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=int(os.environ.get("PRO_COMP_JOBS", "2"))) as ex_:  # səhnə kompozitləri paralel
    outs = list(ex_.map(composite, SC))
for s_, o in zip(SC, outs):
    r = run(["python", "-m", "montaj.session", "add-broll", pid, "--file", str(o)])
    if r.returncode: raise SystemExit("add-broll: " + r.stderr[-500:])
    shutil.rmtree(s_["dir"], ignore_errors=True)
print("kompozit:", len(outs))
q = store.load(pid); W, H = int(q["width"]), int(q["height"])
names = {m["name"]: m for m in q["media"]}
for s_, o in zip(SC, outs):
    m = names[o.name]
    q["clips"].append({"id": "b_" + uuid.uuid4().hex[:10], "track": "v2", "media": m["id"], "srcIn": 0.0, "srcOut": round(min(s_["n"] / FPS, float(m["duration"]) - 0.001), 3),
                       "start": s_["t0"], "mode": "cover", "origin": "plan", "manual": False, "frame": SS._cover_frame(m, W, H)})
R = [(s_["t0"], s_["t0"] + s_["n"] / FPS) for s_ in SC]
caps = [c for c in q["clips"] if c["track"] == "c1" and c.get("autoSub")]
rm = [c["id"] for c in caps if any(c["start"] < b0 - 0.02 and c["start"] + (c["srcOut"] - c["srcIn"]) > a0 + 0.02 for a0, b0 in R)]  # səhnə ilə istənilən üst-üstə düşmə
q["subtitles"]["removed"] = sorted(set((q["subtitles"].get("removed") or []) + rm)); q["clips"] = [c for c in q["clips"] if c["id"] not in rm]
store.save(pid, q, store.load(pid)["revision"]); print("altyazı gizlədildi", len(rm))
for m in store.load(pid)["media"]:  # təkrar qurulmada add-broll eyni faylı köhnə ID ilə qeyd edə bilər — fayl yerində olsun
    f_ = P / m.get("file", "")
    if m.get("file") and not f_.exists() and (W_DIR / m["name"]).exists(): shutil.copyfile(W_DIR / m["name"], f_); print("bərpa:", m["name"])
tick("yekun render")
r = run(["python", "-m", "montaj.session", "render", pid]); print((r.stdout.strip().splitlines() or [r.stderr[-800:]])[-1])
if r.returncode: raise SystemExit("render xətası: " + r.stderr[-1500:])
f = sorted((DATA / "out" / pid).glob(f"{pid}_r*.mp4"), key=lambda p: p.stat().st_mtime)[-1]
dst = f"{SCR}/PRO_{CFG['file']}.mp4"
if Path(dst).exists():  # əvvəlki versiya itmir: versiyalar/PRO_x_v1.mp4, v2 …
    vd = Path(SCR) / "versiyalar"; vd.mkdir(exist_ok=True); k_ = len(list(vd.glob(f"PRO_{CFG['file']}_v*.mp4"))) + 1
    shutil.move(dst, vd / f"PRO_{CFG['file']}_v{k_}.mp4"); print(f"əvvəlki versiya → versiyalar/PRO_{CFG['file']}_v{k_}.mp4")
subprocess.run(["cp", str(f), dst]); print("HAZIR", dst)
if MUS and MUS.get("file"):  # musiqi lisenziyası qeydi (reklamda vacibdir)
    (W_DIR / "musiqi_lisenziya.txt").write_text(f"fayl: {MUS['file']}\nmənbə: {MUS.get('source', '?')}\nlisenziya: {MUS.get('license', '?')}\nvideo: {dst}\n", encoding="utf-8")
if BRAND.get("handle") and CFG.get("watermark", BRAND.get("watermark", False)):
    subprocess.run([sys.executable, str(A / "postfx.py"), "watermark", sys.argv[1], dst], check=True)
tick("render bitdi")
# 9) QA darvazası: keçməsə çıxış kodu 3 (video göndərilmir)
qa = subprocess.run([sys.executable, str(A / "qa.py"), sys.argv[1], dst], capture_output=True, text=True)
print(qa.stdout.strip()); tick("QA")
if qa.returncode: raise SystemExit(3)
for step in ("exports", "cover", "brief"):  # QA keçəndən sonra: əlavə formatlar, üz qabığı, caption/hook paketi
    if step == "exports" and not CFG.get("exports", BRAND.get("exports")): continue
    pr = subprocess.run([sys.executable, str(A / ("brief.py" if step == "brief" else "postfx.py")), *([] if step == "brief" else [step]), sys.argv[1], dst], capture_output=True, text=True)
    print((pr.stdout.strip().splitlines() or [pr.stderr[-300:]])[-1])
for old in sorted((DATA / "out" / pid).glob(f"{pid}_r*.mp4"), key=lambda p: p.stat().st_mtime)[:-1]: old.unlink()
for o in outs: o.unlink(missing_ok=True)
r = run(["python", "-m", "montaj.session", "verify", pid])
print("\n".join(l for l in r.stdout.splitlines() if l.startswith(("!", "?")) or "uyğunluq" in l or "üzü" in l))
