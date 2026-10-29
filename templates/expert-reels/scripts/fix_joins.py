#!/usr/bin/env python3
"""Check every cut point of an edit against the ORIGINAL audio and move it into silence.

Usage: fix_joins.py <project-dir> [--apply]

For each kept source range (artifacts/keep.json):
  * an end that lands on speech is pushed forward until the voice has died away, then a natural
    tail of TAIL seconds is kept (never past the next speech);
  * a start that lands on speech is pulled back the same way, keeping LEAD seconds before the word.
Speech = 10 ms frames more than 10 dB above the source's own floor (raw audio, no denoiser).

The edit's timings are kept in step: spec.json / words.json are read on the current timeline
(un-doing smooth_joins.py when spec["smooth_joins"] is set), moved to the corrected cut, and written
as spec_hard.json / words_hard.json (and spec.json / words.json). Afterwards re-run cut_takes.py and,
for a dissolved edit, smooth_joins.py. Without --apply it only reports.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

TAIL, LEAD, MAXMOVE = 0.17, 0.11, 0.45
proj = Path(sys.argv[1])
apply = "--apply" in sys.argv
ART = proj / "artifacts"
src = proj / "assets/source/flipped.mp4"
if not src.exists():
    src = next((proj / "assets/source").glob("*.mp4"))

raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.int16).astype(np.float32)
H = 160
n = len(x) // H
db = 20 * np.log10(np.sqrt((x[: n * H].reshape(n, H) ** 2).mean(1)) + 1)
floor = np.percentile(db, 10)
sp = db > floor + 10
fr = lambda t: min(n - 1, max(0, int(round(t * 100))))
speech = lambda t: sp[max(0, fr(t) - 2): fr(t) + 3].any()


def last_speech_before(t, lim):
    i = fr(t)
    while i > fr(lim) and not sp[i]:
        i -= 1
    return i / 100 if sp[i] else None


def next_speech_after(t, lim):
    i = fr(t)
    while i < fr(lim) and not sp[i]:
        i += 1
    return i / 100 if sp[i] else None


keep = json.load(open(ART / "keep.json"))
new = [list(r) for r in keep]
log = []
for k, (a, b) in enumerate(keep):
    nxt_a = keep[k + 1][0] if k + 1 < len(keep) else None
    prv_b = keep[k - 1][1] if k > 0 else None
    if k + 1 < len(keep):  # the last end gets the closing hold from cut_takes anyway
        e = b
        while speech(e) and e < b + MAXMOVE:
            e += 0.01
        ls = last_speech_before(e, b - 0.6)
        if ls is not None:
            ns = next_speech_after(e, e + 1.0)
            want = ls + 0.01 + TAIL
            if ns is not None:
                want = min(want, ns - 0.04)
            e = max(e, min(want, b + MAXMOVE))
        if nxt_a is not None and nxt_a > b:  # never run into the next kept range
            e = min(e, nxt_a - 0.05)
        if abs(e - b) > 0.005:
            new[k][1] = round(e, 3)
            log.append(f"end   {b:7.2f} -> {e:7.2f}" + ("  (was ON speech)" if speech(b) else "  (tail room)"))
    if k > 0:
        s = a
        while speech(s) and s > a - MAXMOVE:
            s -= 0.01
        fs = next_speech_after(s, a + 0.6)
        if fs is not None:
            ps = last_speech_before(s, s - 1.0)
            want = fs - LEAD
            if ps is not None:
                want = max(want, ps + 0.04)
            s = min(s, max(want, a - MAXMOVE))
        if prv_b is not None and prv_b < a:
            s = max(s, new[k - 1][1] + 0.05)
        if abs(s - a) > 0.005:
            new[k][0] = round(s, 3)
            log.append(f"start {a:7.2f} -> {s:7.2f}" + ("  (was ON speech)" if speech(a) else "  (lead room)"))

# PIN='{"64.7": 64.7}': hand-checked cut points (e.g. a retake's last word right before a start)
import os
for k_, v_ in json.loads(os.environ.get("PIN", "{}")).items():
    for r_o, r_n in zip(keep, new):
        for j in (0, 1):
            if abs(r_o[j] - float(k_)) < 0.02:
                r_n[j] = v_
                log.append(f"pinned {r_o[j]:.2f} -> {v_}")
print(f"{proj.name}: {len(keep) - 1} joins, {len(log)} moved")
for line in log:
    print("  " + line)
if not apply or not log:
    sys.exit(0)

# ---------------------------------------------------------------- timings: current -> hard -> new hard
spec = json.load(open(proj / "spec.json"))
F = spec.get("smooth_joins", 0)
joins, c = [], 0.0
for a, b in keep[:-1]:
    c += b - a
    joins.append(round(c * 30) / 30)
sj = [j - F * (i + 1) for i, j in enumerate(joins)]
to_hard = (lambda y: y + F * sum(1 for s in sj if y >= s)) if F else (lambda y: y)
FR = 30
snap = lambda r: [round(r[0] * FR) / FR, round(r[1] * FR) / FR]
old_s, new_s = [snap(r) for r in keep], [snap(r) for r in new]
starts_old, starts_new, co, cn = [], [], 0.0, 0.0
for (a, b), (a2, b2) in zip(old_s, new_s):
    starts_old.append(co)
    starts_new.append(cn)
    co += b - a
    cn += b2 - a2


def move(y):
    h = to_hard(y)
    for i, ((a, b), (a2, b2)) in enumerate(zip(old_s, new_s)):
        if h < starts_old[i] + (b - a) + 1e-6 or i == len(old_s) - 1:
            s = a + (h - starts_old[i])
            return round(starts_new[i] + min(max(s, a2), b2 + (1.0 if i == len(old_s) - 1 else 0)) - a2, 3)


K = {"in", "out", "strike", "t", "headAt", "at", "flag", "a", "b", "c"}


def walk(o):
    if isinstance(o, dict):
        return {k: (move(v) if k in K and isinstance(v, (int, float)) else walk(v)) for k, v in o.items()}
    if isinstance(o, list):
        return [walk(v) for v in o]
    return o


z = spec.pop("zoom", [])
spec.pop("caption_shift", None)
spec.pop("smooth_joins", None)
spec = walk(spec)
spec["zoom"] = [[move(e[0])] + e[1:] for e in z]
words = json.load(open(ART / "words.json"))
for g in words:
    for w in g["words"]:
        w["start"], w["end"] = move(w["start"]), move(w["end"])
for p, d in ((proj / "spec_hard.json", spec), (proj / "spec.json", spec), (ART / "words_hard.json", words), (ART / "words.json", words)):
    json.dump(d, open(p, "w"), ensure_ascii=False, indent=1)
json.dump(new, open(ART / "keep.json", "w"))
hard = proj / "assets/video/cut_hard.mp4"
if hard.exists():
    hard.unlink()
print(f"applied; dissolve was {F}s - re-run cut_takes.py" + (" and smooth_joins.py" if F else ""))
