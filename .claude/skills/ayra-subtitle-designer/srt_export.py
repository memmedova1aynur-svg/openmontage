#!/usr/bin/env python3
"""Ayrıca SRT faylı: video (faster-whisper söz vaxtları) və ya engine words.json-dan.
  srt_export.py <video|words.json> <out.srt> [--ref təsdiqli_mətn.txt] [--max-words 4] [--max-chars 22]
--ref verilsə ASR sözləri təsdiqli mətnin sözləri ilə ardıcıl uyğunlaşdırılıb əvəz olunur (yazılış düzəlişi)."""
import sys, json, re, argparse, difflib
ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("out"); ap.add_argument("--ref")
ap.add_argument("--max-words", type=int, default=4); ap.add_argument("--max-chars", type=int, default=22); a = ap.parse_args()
if a.src.endswith(".json"):
    W = [(w.get("w") or w.get("word") or w.get("text"), float(w["start"]), float(w["end"])) for w in json.load(open(a.src))]
else:
    import subprocess, numpy as np
    from faster_whisper import WhisperModel
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", a.src, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
    audio = np.frombuffer(pcm, np.float32)
    m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    segs, _ = m.transcribe(audio, language="az", word_timestamps=True, vad_filter=False)
    W = [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]
if a.ref:
    ref = open(a.ref).read().split(); norm = lambda s: re.sub(r"[^\wəğıöüşç]", "", s.lower())
    sm = difflib.SequenceMatcher(a=[norm(w[0]) for w in W], b=[norm(r) for r in ref], autojunk=False); out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal" or (tag == "replace"):
            seg = W[i1:i2]; refw = ref[j1:j2]
            if not seg: continue
            if len(seg) == len(refw): out += [(r, s[1], s[2]) for r, s in zip(refw, seg)]
            else:  # say fərqlidirsə vaxtı bərabər payla
                t0, t1 = seg[0][1], seg[-1][2]; n = len(refw) or 1
                out += [(r, t0 + (t1 - t0) * k / n, t0 + (t1 - t0) * (k + 1) / n) for k, r in enumerate(refw)]
        elif tag == "insert":
            t = W[i1 - 1][2] if i1 else 0; out += [(r, t, t + 0.2) for r in ref[j1:j2]]
        # delete: ASR-də artıq söz → atılır
    W = out
G, cur = [], []
for w in W:
    if cur and (len(cur) >= a.max_words or len(" ".join(x[0] for x in cur + [w])) > a.max_chars): G.append(cur); cur = []
    cur.append(w)
    if w[0][-1:] in ".?!": G.append(cur); cur = []
if cur: G.append(cur)
ts = lambda t: f"{int(t//3600):02}:{int(t%3600//60):02}:{int(t%60):02},{int(round(t%1*1000)):03}"
with open(a.out, "w") as f:
    for i, g in enumerate(G, 1):
        s = max(0, g[0][1] - 0.08); e = max(g[-1][2], s + 0.6)
        if i < len(G): e = min(e, G[i][0][1] - 0.02)
        f.write(f"{i}\n{ts(s)} --> {ts(e)}\n{' '.join(x[0] for x in g)}\n\n")
print(a.out, len(G), "blok")
