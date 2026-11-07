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
def style(name):
    if re.fullmatch(r"S\d{2}", name or ""):  # agentliyin S-kod kataloqu (instagram-clients/_agency/s_kodlar.json)
        m = Path(os.environ.get("PRO_AGENCY", str(Path(__file__).resolve().parents[3] / "instagram-clients" / "_agency"))) / "s_kodlar.json"
        if not m.exists(): raise SystemExit(f"S-kod xəritəsi tapılmadı: {m}")
        e = json.load(open(m)).get(name) or {}
        if not e.get("preset"):
            raise SystemExit(f"{name} {e.get('ad', '')}: talk.py ilə alınmır (alət: {e.get('alət')}, status: {e.get('status')}). Material: {e.get('material', '—')}")
        print(f"{name} {e['ad']} → tərz: {e['preset']} ({e['status']})"); name = e["preset"]
    f = Path(__file__).resolve().parent / "styles" / f"{name}.json"
    if not f.exists(): raise SystemExit(f"tərz tapılmadı: {name} (styles/ qovluğuna bax)")
    return {k: v for k, v in json.load(open(f)).items() if not k.startswith("_")}
# sıra: default < müştəri (kim: kadraj, güzgü, rəng) < tərz (necə: montaj) < video planı
B = {**{"zooms": [1.0, 1.1], "cy": 0.45, "gap": 0.6, "mv": 560, "fontsize": 68, "sub": "lines", "accent": "#FFD84D", "font": "Montserrat"},
     **brand_talk(P.get("brand")), **style(P.get("style", "sade")), **P}


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
    if nx is None or nx["k"] != w["k"] or (not short and (re.search(r"[.,?!:;]$", w["t"]) or len(txt) >= B.get("max_chars", 16) or len(cur) >= B.get("max_words", 3) or nx["s"] - w["e"] > 0.35)):
        chunks.append(cur); cur = []
chunks = [[x for x in c if x["t"]] for c in chunks]; chunks = [c for c in chunks if c]
m = []
for c in chunks:
    if m and len(" ".join(x["t"] for x in c)) <= 4 and m[-1][-1]["k"] == c[0]["k"] and len(m[-1]) < 4: m[-1] += c
    else: m.append(c)
chunks = m
ts = lambda x: f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"
def bgr(h, a="00"): h = h.lstrip("#"); return f"&H{a}{h[4:6]}{h[2:4]}{h[0:2]}"
ACC = B["accent"]; ev = []
if B["sub"] == "lines":
    for j, c in enumerate(chunks):
        s0, e = c[0]["s"], c[-1]["e"] + 0.25
        if j + 1 < len(chunks): e = min(e, chunks[j + 1][0]["s"])
        sp_on = any(m != "full" and a0 - 0.05 <= s0 < b0 for a0, b0, _, m in B.get("inserts", []))  # split ekranda sərhədə
        ev.append(f"Dialogue: 1,{ts(s0)},{ts(min(e, T))},S,,0,0,0,,{'{\\an5\\pos(540,962)}' if sp_on else ''}{' '.join(x['t'] for x in c).rstrip(',.;:')}")
elif B["sub"] == "words":  # dinamik: iri, söz-söz, aktiv söz vurğu rəngində "pop"
    for j, c in enumerate(chunks):
        endc = min(c[-1]["e"] + 0.2, chunks[j + 1][0]["s"] if j + 1 < len(chunks) else T)
        for i, w in enumerate(c):
            e = c[i + 1]["s"] if i + 1 < len(c) else endc
            U = (lambda x: x.upper().replace("i", "İ") if B.get("upper") else x)
            KW = set(k.lower() for k in B.get("keywords", []))
            parts = [(f"{{\\c{bgr(ACC)}\\t(0,90,\\fscx112\\fscy112)\\t(90,180,\\fscx100\\fscy100)}}{U(x['t'])}{{\\r}}" if x is w else
                      (f"{{\\c{bgr(B.get('accent2', '#7CE0A3'))}}}{U(x['t'])}{{\\r}}" if re.sub(r"[^\\w]", "", x["t"].lower()) in KW else U(x["t"]))) for x in c]
            ev.append(f"Dialogue: 1,{ts(w['s'])},{ts(e)},D,,0,0,0,,{' '.join(parts).rstrip(',.;:')}")
for t0, dur, txt in B.get("questions", []):  # müsahibə: sual kartı
    ev.append(f"Dialogue: 2,{ts(t0)},{ts(t0 + dur)},Q,,0,0,0,,{{\\fad(220,220)}}{txt}")
for t0, t1, txt in B.get("statements", []):  # mif/fakt: iddia kartı
    ev.append(f"Dialogue: 2,{ts(t0)},{ts(t1)},L,,0,0,0,,{{\\fad(200,150)}}MİF, YOXSA FAKT?")
    ev.append(f"Dialogue: 2,{ts(t0)},{ts(t1)},Q,,0,0,0,,{{\\fad(200,150)}}{txt}")
VC = {"mif": ("#E5484D", "MİF ✕"), "fakt": ("#30A46C", "FAKT ✓"), "yari": ("#F5B700", "ASILIDIR")}
for t0, kind in B.get("verdicts", []):
    col, lab = VC[kind]
    ev.append(f"Dialogue: 0,{ts(t0)},{ts(t0 + 0.9)},F,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\c{bgr(col)}\\alpha&H70&\\t(0,900,\\alpha&HFF&)}}m 0 0 l 1080 0 l 1080 1920 l 0 1920{{\\p0}}")
    ev.append(f"Dialogue: 3,{ts(t0)},{ts(t0 + 1.8)},V,,0,0,0,,{{\\pos(540,{B.get('verdict_y', 430)})\\3c{bgr(col)}\\fad(0,250)\\fscx40\\fscy40\\t(0,180,\\fscx110\\fscy110)\\t(180,300,\\fscx100\\fscy100)}}{lab}")
for t0, t1, txt in B.get("cards", []):  # minimal: açar söz kartı
    ev.append(f"Dialogue: 2,{ts(t0)},{ts(t1)},C,,0,0,0,,{{\\fad(300,300)\\blur0.6}}{txt}")
def rrect(x, y, w, h, r):  # yuvarlaq künclü düzbucaqlı (ASS çizimi)
    k = r * 0.45
    return (f"m {x+r} {y} l {x+w-r} {y} b {x+w-k} {y} {x+w} {y+k} {x+w} {y+r} l {x+w} {y+h-r} b {x+w} {y+h-k} {x+w-k} {y+h} {x+w-r} {y+h} "
            f"l {x+r} {y+h} b {x+k} {y+h} {x} {y+h-k} {x} {y+h-r} l {x} {y+r} b {x} {y+k} {x+k} {y} {x+r} {y}")
def circ(cx, cy, r):
    k = r * 0.552
    return (f"m {cx} {cy-r} b {cx+k} {cy-r} {cx+r} {cy-k} {cx+r} {cy} b {cx+r} {cy+k} {cx+k} {cy+r} {cx} {cy+r} "
            f"b {cx-k} {cy+r} {cx-r} {cy+k} {cx-r} {cy} b {cx-r} {cy-k} {cx-k} {cy-r} {cx} {cy-r}")
if B.get("progress"):  # yuxarıda izləmə xətti (sona qədər baxmağa təşviq)
    ev.append(f"Dialogue: 6,{ts(0)},{ts(T)},F,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\c{bgr(ACC)}\\fscx0\\t(0,{int(T*1000)},\\fscx100)}}m 0 0 l 1080 0 l 1080 10 l 0 10{{\\p0}}")
if B.get("headline"):  # bütün video boyu sabit başlıq
    ev.append(f"Dialogue: 4,{ts(B.get('headline_from', 0))},{ts(T)},H,,0,0,0,,{{\\fad(200,0)}}{B['headline']}")
items = B.get("items", [])  # siyahı: hər bənd ekranda qalır
for i, (t0, txt) in enumerate(items):
    y = B.get("items_y", 330) + i * B.get("items_step", 104)
    ev.append(f"Dialogue: 4,{ts(t0)},{ts(B.get('items_end', T))},I,,0,0,0,,{{\\an7\\pos(80,{y})\\fad(150,0)\\fscx70\\fscy70\\t(0,160,\\fscx104\\fscy104)\\t(160,260,\\fscx100\\fscy100)}}{{\\c{bgr(ACC)}}}{i+1}{{\\r}}  {txt}")
cm = B.get("comment")  # şərhə cavab: Instagram şərh balonu
if cm:
    x0, y0, w0, h0 = 70, 250, 940, cm.get("h", 190); lay = f"{ts(cm['t0'])},{ts(cm['t1'])}"
    ev.append(f"Dialogue: 4,{lay},F,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\c&HFFFFFF&\\fad(200,200)\\shad3\\4a&HA0&}}{rrect(x0, y0, w0, h0, 34)}{{\\p0}}")
    ev.append(f"Dialogue: 5,{lay},F,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\c{bgr(ACC)}\\fad(200,200)}}{circ(x0+70, y0+70, 34)}{{\\p0}}")
    ev.append(f"Dialogue: 6,{lay},CU,,0,0,0,,{{\\an7\\pos({x0+124},{y0+30})\\fad(200,200)}}{cm['user']}  {{\\c&H8A8A8A&\\b0\\fs30}}şərhinə cavab")
    ev.append(f"Dialogue: 6,{lay},CT,,0,0,0,,{{\\an7\\pos({x0+124},{y0+78})\\fad(200,200)}}{cm['text']}")
tm = B.get("timer")  # çağırış taymeri
if tm:
    for k in range(int(tm["dur"])):
        a = tm["t0"] + k
        ev.append(f"Dialogue: 5,{ts(a)},{ts(min(a + 1, T))},TM,,0,0,0,,{{\\an9\\pos(1010,250)}}{int(tm['dur']) - k}")
    ev.append(f"Dialogue: 5,{ts(tm['t0'])},{ts(min(tm['t0'] + tm['dur'], T))},TL,,0,0,0,,{{\\an9\\pos(1010,214)}}{tm.get('label', '')}")
FONT = B.get("font", "Montserrat"); K.ensure_font(FONT); K.ensure_font(B.get("ui_font", "Montserrat")); UI = B.get("ui_font", "Montserrat")
ASS = WORK / "sub.ass"
ASS.write_text(f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: S,{FONT},{B['fontsize']},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,{B.get('sub_bold', -1)},{B.get('sub_italic', 0)},0,0,100,100,0,0,1,{B.get('sub_outline', 3.2)},1.5,2,90,90,{B['mv']},1
Style: D,{UI},{B.get('word_size', 92)},&H00FFFFFF,&H00FFFFFF,&H00101010,&H78000000,-1,0,0,0,100,100,0,0,1,6,2,2,70,70,{B.get('word_mv', 640)},1
Style: Q,{UI},{B.get('q_size', 54)},&H00FFFFFF,&H00FFFFFF,{bgr(B.get('q_bg', '#0B2A20'))},{bgr(B.get('q_bg', '#0B2A20'))},-1,0,0,0,100,100,0,0,3,26,0,8,110,110,{B.get('q_mv', 330)},1
Style: L,JetBrains Mono,30,{bgr(ACC)},&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,4,0,1,0,0,8,110,110,250,1
Style: V,{UI},110,&H00FFFFFF,&H00FFFFFF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,3,34,0,5,80,80,0,1
Style: F,{UI},20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: H,{UI},{B.get('h_size', 58)},{bgr(B.get('h_fg', '#0B2A20'))},&H00FFFFFF,{bgr(ACC)},{bgr(ACC)},-1,0,0,0,100,100,0,0,3,22,0,8,90,90,{B.get('h_mv', 260)},1
Style: I,{UI},{B.get('i_size', 50)},&H00FFFFFF,&H00FFFFFF,&H00141414,&H96000000,-1,0,0,0,100,100,0,0,3,18,0,7,0,0,0,1
Style: CU,{UI},34,&H00262626,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: CT,{UI},40,&H00141414,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: TM,JetBrains Mono,96,&H00FFFFFF,&H00FFFFFF,{bgr(ACC)},&H00000000,-1,0,0,0,100,100,0,0,3,20,0,9,0,0,0,1
Style: TL,{UI},30,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,9,0,0,0,1
Style: C,{UI},{B.get('card_size', 104)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H50000000,-1,0,0,0,100,100,-2,0,1,0,6,5,90,90,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(ev) + "\n")
(OUT.parent / (OUT.stem + "_altyazi.txt")).write_text("\n".join(" ".join(x["t"] for x in c) for c in chunks))

# --- storyboard (render-dən əvvəl təsdiq üçün): python3 talk.py plan.json storyboard
if len(sys.argv) > 2 and sys.argv[2] == "storyboard":
    from PIL import Image, ImageDraw, ImageFont
    bc0 = B.get("base"); vf0 = ("hflip," if B.get("hflip") else "")
    if bc0: vf0 += f"crop=iw*{bc0['s']}:ih*{bc0['s']}:iw*{bc0['cx'] - bc0['s'] / 2:.4f}:ih*{bc0['cy'] - bc0['s'] / 2:.4f},"
    fb = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 20); fr = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Medium.otf", 17)
    cols = 4; Wt, Ht = 270, 480; rows = (len(segs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * Wt, rows * (Ht + 120) + 70), "white"); d = ImageDraw.Draw(sheet)
    d.text((12, 18), f"Storyboard · tərz: {P.get('style', 'sade')} · {T:.1f} san · {len(segs)} seqment", fill="black", font=fb)
    md = [f"# Storyboard: {OUT.stem}", "", f"Tərz: {P.get('style', 'sade')} · müddət {T:.1f} s", "", "| # | Vaxt | Mənbə | Mətn |", "|---|---|---|---|"]
    off = 0.0
    for i, (a, b, z) in enumerate(segs):
        fj = WORK / f"sb{i}.jpg"
        K.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{(a + b) / 2:.3f}", "-i", SRC, "-frames:v", "1", "-vf", f"{vf0}scale={Wt}:{Ht}", str(fj)])
        txt = " ".join(w["t"] for w in nw if w["k"] == i and w["t"])
        x, y = (i % cols) * Wt, 70 + (i // cols) * (Ht + 120); sheet.paste(Image.open(fj), (x, y))
        d.rectangle([x, y, x + 64, y + 30], fill="black"); d.text((x + 8, y + 5), f"{i + 1:02d}", fill="white", font=fb)
        d.text((x + 6, y + Ht + 6), f"{off:.1f}–{off + b - a:.1f} s", fill="#555", font=fr)
        lines, cur = [], ""
        for wd in txt.split():
            if len(cur) + len(wd) > 26: lines.append(cur); cur = wd
            else: cur = (cur + " " + wd).strip()
        lines.append(cur)
        for j, ln in enumerate(lines[:4]): d.text((x + 6, y + Ht + 30 + j * 21), ln, fill="black", font=fr)
        md.append(f"| {i + 1} | {off:.1f}–{off + b - a:.1f} | {a:.2f}–{b:.2f} | {txt} |"); off += b - a
    for k_ in ("headline", "items", "questions", "statements", "verdicts", "cards", "comment", "inserts", "timer"):
        if B.get(k_): md.append(f"\n**{k_}:** `{json.dumps(B[k_], ensure_ascii=False)}`")
    SB = OUT.parent / (OUT.stem + "_storyboard.jpg"); sheet.save(SB, quality=88)
    (OUT.parent / (OUT.stem + "_storyboard.md")).write_text("\n".join(md) + "\n")
    print("STORYBOARD", SB); sys.exit()

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
nxt = len(segs); cur_v = "vc"; post = [f"[vc]{COLOR}[g0]"]; cur_v = "g0"
for j, (t0, t1, img, mode) in enumerate(B.get("inserts", [])):  # şəkil/ekran görüntüsü əlavəsi
    INP += ["-loop", "1", "-t", f"{T:.3f}", "-i", rp(img)]; en = f"between(t,{t0},{t1})"
    if mode == "full":  # tam ekran şəkil + dairəvi PiP (danışan)
        post.append(f"[{nxt}:v]scale=960:780:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:{B.get('full_img_y', 480)}:color={B.get('full_bg', '0x0B2A20')},format=yuva420p,fade=t=in:st={t0}:d=0.2:alpha=1[im{j}]")
        post.append(f"[{cur_v}]split[b{j}][p{j}]")
        post.append(f"[p{j}]crop=760:760:160:{B.get('pip_y', 330)},scale=320:320,format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(lte(hypot(X-160,Y-160),156),255,0)'[pc{j}]")
        post.append(f"[b{j}][im{j}]overlay=0:0:enable='{en}'[o{j}];[o{j}][pc{j}]overlay=700:{B.get('pip_top', 130)}:enable='{en}'[q{j}]")
        cur_v = f"q{j}"
    else:  # split ekran: şəkil yuxarı yarımda, danışanın üzü aşağı yarımda
        bg = B.get("split_bg", "0xF4F2EC")
        post.append(f"[{nxt}:v]scale=1000:880:force_original_aspect_ratio=decrease,pad=1080:960:(ow-iw)/2:(oh-ih)/2+40:color={bg},format=yuva420p,fade=t=in:st={t0}:d=0.2:alpha=1[im{j}]")
        post.append(f"[{cur_v}]split[b{j}][p{j}];[p{j}]crop=1080:960:0:{B.get('split_y', 560)}[pf{j}]")
        post.append(f"[b{j}][pf{j}]overlay=0:960:enable='{en}'[o{j}];[o{j}][im{j}]overlay=0:0:enable='{en}'[q{j}]"); cur_v = f"q{j}"
    nxt += 1
if B.get("letterbox"):
    lb = B["letterbox"]; post.append(f"[{cur_v}]drawbox=x=0:y=0:w=iw:h={lb}:color=black:t=fill,drawbox=x=0:y=ih-{lb}:w=iw:h={lb}:color=black:t=fill[lbx]"); cur_v = "lbx"
if B.get("grain"): post.append(f"[{cur_v}]noise=c0s={B['grain']}:c0f=t+u,vignette=PI/5[gr]"); cur_v = "gr"
post.append(f"[{cur_v}]subtitles={ASS}:fontsdir=/usr/share/fonts/opentype/inter,format=yuv420p[v]")
fc += post
VID, RAW = WORK / "v.mp4", WORK / "speech_raw.wav"
K.run(["ffmpeg", "-v", "error", "-y", *INP, "-filter_complex", ";".join(fc), "-map", "[v]", "-r", "30", "-c:v", "libx264", "-preset", "slow",
       "-crf", "20", "-maxrate", "4.5M", "-bufsize", "9M", "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p", "-g", "60", "-an", str(VID),
       "-map", "[ac]", str(RAW)])

# --- səs
SP = WORK / "speech.wav"; K.loudnorm_2pass(RAW, SP, I=-16, pre=K.SPEECH_CHAIN)
FINAL = WORK / "final.wav"
sp = K.load(SP); n = len(sp); mix = sp.copy()
if B.get("cut_sfx"):  # dinamik: hər kəsikdə yüngül swoosh
    off = 0.0
    for a, b, z in segs[:-1]:
        off += b - a; mix = K.add_sfx(mix, K.synth("swoosh"), off - 0.12, B.get("cut_sfx_db", -30))
for t0, kind in B.get("verdicts", []):
    mix = K.add_sfx(mix, K.synth({"mif": "buzz", "fakt": "ding", "yari": "wobble"}[kind]), t0, -22)
for q in B.get("questions", []): mix = K.add_sfx(mix, K.synth("pop"), q[0], -30)
for it in B.get("items", []): mix = K.add_sfx(mix, K.synth("pop"), it[0], -29)
for ins in B.get("inserts", []): mix = K.add_sfx(mix, K.synth("swoosh"), ins[0] - 0.1, -31)
if B.get("comment"): mix = K.add_sfx(mix, K.synth("pop"), B["comment"]["t0"], -28)
for c in B.get("statements", []): mix = K.add_sfx(mix, K.synth("pop"), c[0], -28)
if B.get("music"):
    mask = np.zeros(n, bool)
    for w in nw: mask[int(w["s"] * K.SR):int(w["e"] * K.SR)] = True
    mu = B["music"]; mix = mix + K.music_bed(K.load(rp(mu["file"])), n, mask, level=mu.get("level", -29), duck_db=mu.get("duck", 4))
MIX = WORK / "mix.wav"; K.save(mix, MIX); K.finalize(MIX, FINAL)
K.export_ig(VID, FINAL, OUT, copy_video=True)

# --- story, üz qabığı, QA
st = B.get("story") or [[0, min(10, T)]]
K.story_clips(OUT, st, OUT.parent / "story", label=B.get("story_label"))
K.cover(OUT, B.get("cover_t", 1.0), OUT.parent / (OUT.stem + "_kadr.jpg"))
q = K.qa(OUT); json.dump({"seqmentlər": segs, "qa": q}, open(OUT.parent / (OUT.stem + "_qa.json"), "w"), ensure_ascii=False, indent=1)
print(f"{'OK' if q['ok'] else 'YOXLA'} {OUT}  {T:.1f}s  {len(segs)} seqment  {len(chunks)} altyazı  {q}")
