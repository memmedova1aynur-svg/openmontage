"""Sadə danışıq reeli: kəsim + kadraj + yüngül zoom + sadə altyazı + təmiz səs (+ istəyə görə musiqi).

İstifadə:  python3 talk.py plan.json
plan.json:
{
  "src": "video.mov",                  # mənbə
  "words": "t.json",                   # söz vaxtları (ElevenLabs Scribe formatı); yoxdursa avtomatik yazılır
  "brand": "musteri-adi",             # instagram-clients/<ad>/brand_kit.json → "talk" bölməsi (kadraj, güzgü, zoom)
  "keep": [[40.8, 50.3], [3.7, 40.0]], # saxlanılan aralıqlar (sıra = montaj sırası; hook-u önə çəkmək olar)
  "segs": [[a, b, zoom], ...],         # və ya əl ilə seqmentlər (keep əvəzinə)
  "fix": {"söz": "düzəliş", "söz@12.34": "yalnız bu an", "söz@1.2": ""},  # "" = altyazıdan sil
  "cap_first": true,
  "music": {"file": "mus.mp3", "level": -29},   # istəyə görə
  "story": [[0, 10]],                  # hazır videonun vaxtı ilə story parçaları (default: ilk 10 s)
  "out": "out/Ad.mp4"                  # nəticə: out/Ad_vN.mp4 (köhnə versiyalar qorunur)
}
"""
import json, re, sys, subprocess, os
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import avkit as K

P = json.load(open(sys.argv[1])); ROOT = Path(sys.argv[1]).resolve().parent
rp = lambda x: str((ROOT / x).resolve()) if x and not os.path.isabs(x) else x
SRC = rp(P["src"]); OUT = K.next_version(rp(P["out"])); WORK = OUT.parent / (OUT.stem + "_work"); WORK.mkdir(parents=True, exist_ok=True)


def brand_talk(name):
    if not name: return {}
    for d in (os.environ.get("PRO_BRANDS"), str(Path(__file__).resolve().parents[3] / "instagram-clients")):
        f = Path(d or "", name, "brand_kit.json")
        if d and f.exists(): return json.load(open(f)).get("talk", {})
    raise SystemExit(f"brand_kit tapılmadı: {name}")
B = {**{"zooms": [1.0, 1.1], "cy": 0.45, "gap": 0.6, "mv": 560, "fontsize": 68}, **brand_talk(P.get("brand")), **P}


def transcribe(src, out):
    """ElevenLabs Scribe (aze); alınmasa faster-whisper (lokal)."""
    wav = WORK / "a16.wav"; K.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", str(wav)])
    key = os.environ.get("ELEVENLABS_API_KEY")
    if key:
        r = subprocess.run(["curl", "-sS", "-X", "POST", "https://api.elevenlabs.io/v1/speech-to-text", "-H", f"xi-api-key: {key}",
                            "-F", "model_id=scribe_v1", "-F", "language_code=aze", "-F", "timestamps_granularity=word",
                            "-F", "tag_audio_events=false", "-F", f"file=@{wav}"], capture_output=True, text=True).stdout
        try:
            d = json.loads(r)
            if "words" in d: json.dump(d, open(out, "w"), ensure_ascii=False); return
            print("Scribe alınmadı:", r[:200])
        except Exception: print("Scribe cavabı oxunmadı")
    from faster_whisper import WhisperModel
    segs, _ = WhisperModel("small", compute_type="int8").transcribe(str(wav), language="az", word_timestamps=True)
    words = [{"type": "word", "text": w.word.strip(), "start": w.start, "end": w.end} for s in segs for w in s.words]
    json.dump({"words": words}, open(out, "w"), ensure_ascii=False)


WJ = rp(P.get("words")) if P.get("words") else str(WORK / "words.json")
if not Path(WJ).exists(): transcribe(SRC, WJ)
W = [w for w in json.load(open(WJ))["words"] if w.get("type", "word") == "word"]
FIX = B.get("fix", {})

# --- seqmentlər
segs = B.get("segs")
if not segs:
    Z = B["zooms"]; segs = []
    for a, b in B["keep"]:
        ws = [w for w in W if w["start"] >= a - 0.02 and w["end"] <= b + 0.02]
        if not ws: continue
        grp = [[ws[0]]]
        for w in ws[1:]:
            (grp.append([w]) if w["start"] - grp[-1][-1]["end"] > B["gap"] else grp[-1].append(w))
        for g in grp:
            i0, i1 = W.index(g[0]), W.index(g[-1])
            s0 = g[0]["start"] - 0.08; e0 = g[-1]["end"] + 0.12
            if i0 > 0: s0 = max(s0, (W[i0 - 1]["end"] + g[0]["start"]) / 2)
            if i1 + 1 < len(W): e0 = min(e0, (g[-1]["end"] + W[i1 + 1]["start"]) / 2)
            segs.append([round(max(0, s0), 3), round(e0, 3), Z[len(segs) % len(Z)]])

# --- altyazı (yeni zaman xətti)
nw, off = [], 0.0
for k, (a, b, z) in enumerate(segs):
    for w in W:
        if w["start"] >= a - 0.02 and w["end"] <= b + 0.02:
            t = FIX.get(f'{w["text"]}@{w["start"]:.2f}', FIX.get(w["text"], w["text"]))
            nw.append(dict(t=t, s=w["start"] - a + off, e=min(w["end"], b) - a + off, k=k))
    off += b - a
T = off
if B.get("cap_first") and nw and nw[0]["t"]: nw[0]["t"] = nw[0]["t"][0].upper() + nw[0]["t"][1:]
chunks, cur = [], []
for i, w in enumerate(nw):
    cur.append(w); txt = " ".join(x["t"] for x in cur if x["t"]); nx = nw[i + 1] if i + 1 < len(nw) else None
    short = len(txt) <= 4 and nx is not None and nx["k"] == w["k"]
    if nx is None or nx["k"] != w["k"] or (not short and (re.search(r"[.,?!:;]$", w["t"]) or len(txt) >= 16 or len(cur) >= 3 or nx["s"] - w["e"] > 0.35)):
        chunks.append(cur); cur = []
chunks = [[x for x in c if x["t"]] for c in chunks]; chunks = [c for c in chunks if c]
m = []
for c in chunks:
    if m and len(" ".join(x["t"] for x in c)) <= 4 and m[-1][-1]["k"] == c[0]["k"] and len(m[-1]) < 4: m[-1] += c
    else: m.append(c)
chunks = m
ts = lambda x: f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"
ev = []
for j, c in enumerate(chunks):
    s, e = c[0]["s"], c[-1]["e"] + 0.25
    if j + 1 < len(chunks): e = min(e, chunks[j + 1][0]["s"])
    ev.append(f"Dialogue: 0,{ts(s)},{ts(min(e, T))},S,,0,0,0,,{' '.join(x['t'] for x in c).rstrip(',.;:')}")
ASS = WORK / "sub.ass"
ASS.write_text(f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: S,Inter,{B['fontsize']},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,3.2,1.5,2,90,90,{B['mv']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(ev) + "\n")
(OUT.parent / (OUT.stem + "_altyazi.txt")).write_text("\n".join(" ".join(x["t"] for x in c) for c in chunks))

# --- video (hər seqment ayrıca giriş: uzun mənbədə yaddaş partlamır)
bc = B.get("base")
pre = ("hflip," if B.get("hflip") else "")
if bc: pre += f"crop=iw*{bc['s']}:ih*{bc['s']}:iw*{bc['cx'] - bc['s'] / 2:.4f}:ih*{bc['cy'] - bc['s'] / 2:.4f},scale=1080:1920:flags=lanczos,"
COLOR = B.get("color", "eq=contrast=1.04:saturation=0.96:gamma=0.99,curves=master='0/0 0.06/0.05 0.6/0.6 0.92/0.9 1/0.97',colortemperature=temperature=6300:mix=0.6")
fc, cat, INP = [], "", []
for i, (a, b, z) in enumerate(segs):
    INP += ["-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", SRC]
    fc.append(f"[{i}:v]setpts=PTS-STARTPTS,{pre}scale=iw*{z}:ih*{z}:flags=lanczos,crop=1080:1920:(iw-1080)/2:(ih-1920)*{B['cy']},setsar=1[v{i}]")
    fc.append(f"[{i}:a]asetpts=PTS-STARTPTS,aresample={K.SR},afade=t=in:d=0.012,afade=t=out:st={b - a - 0.015:.3f}:d=0.015[a{i}]")
    cat += f"[v{i}][a{i}]"
fc.append(f"{cat}concat=n={len(segs)}:v=1:a=1[vc][ac]")
fc.append(f"[vc]{COLOR},subtitles={ASS}:fontsdir=/usr/share/fonts/opentype/inter,format=yuv420p[v]")
VID, RAW = WORK / "v.mp4", WORK / "speech_raw.wav"
K.run(["ffmpeg", "-v", "error", "-y", *INP, "-filter_complex", ";".join(fc), "-map", "[v]", "-r", "30", "-c:v", "libx264", "-preset", "slow",
       "-crf", "20", "-maxrate", "4.5M", "-bufsize", "9M", "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p", "-g", "60", "-an", str(VID),
       "-map", "[ac]", str(RAW)])

# --- səs
SP = WORK / "speech.wav"; K.loudnorm_2pass(RAW, SP, I=-16, pre=K.SPEECH_CHAIN)
FINAL = WORK / "final.wav"
if B.get("music"):
    sp = K.load(SP); n = len(sp); mask = np.zeros(n, bool)
    for w in nw: mask[int(w["s"] * K.SR):int(w["e"] * K.SR)] = True
    mu = B["music"]; bed = K.music_bed(K.load(rp(mu["file"])), n, mask, level=mu.get("level", -29), duck_db=mu.get("duck", 4))
    MIX = WORK / "mix.wav"; K.save(sp + bed, MIX); K.finalize(MIX, FINAL)
else:
    K.finalize(SP, FINAL)
K.export_ig(VID, FINAL, OUT, copy_video=True)

# --- story, üz qabığı, QA
st = B.get("story") or [[0, min(10, T)]]
K.story_clips(OUT, st, OUT.parent / "story", label=B.get("story_label"))
K.cover(OUT, B.get("cover_t", 1.0), OUT.parent / (OUT.stem + "_kadr.jpg"))
q = K.qa(OUT); json.dump({"seqmentlər": segs, "qa": q}, open(OUT.parent / (OUT.stem + "_qa.json"), "w"), ensure_ascii=False, indent=1)
print(f"{'OK' if q['ok'] else 'YOXLA'} {OUT}  {T:.1f}s  {len(segs)} seqment  {len(chunks)} altyazı  {q}")
