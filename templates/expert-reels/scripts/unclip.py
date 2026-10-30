#!/usr/bin/env python3
"""Give back speech that a cut clipped, and re-time everything after it.

Usage:
    python templates/expert-reels/scripts/unclip.py <project-dir> [<source.mp4>]

Pause shortening (tighten.py) looks for silence in the DeepFilterNet-cleaned voice, and that
model sometimes treats a soft syllable as noise ("Daha" -> "...ha"). This script listens to
the RAW source audio inside every short gap between kept ranges (artifacts/keep.json,
source timeline): voiced audio touching either edge of a gap is put back by growing the
neighbouring range. Gaps longer than MAX_GAP are deliberate retake cuts and are left alone.
words.json and spec.json are shifted onto the new cut timeline (old files kept as *_pre_unclip).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

MAX_GAP = 1.6
proj = Path(sys.argv[1])
src = Path(sys.argv[2]) if len(sys.argv) > 2 else proj / "assets/source/flipped.mp4"
ART = proj / "artifacts"
SR, HOP = 16000, 160  # 10 ms frames

raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                     capture_output=True, check=True).stdout
x = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
n = len(x) // HOP
db = 20 * np.log10(np.sqrt((x[: n * HOP].reshape(n, HOP) ** 2).mean(1)) + 1)
floor = np.percentile(db, 12)
speech = np.percentile(db, 80)
voiced = db > floor + 0.45 * (speech - floor)  # well above the room noise


def f(t: float) -> int:
    return min(n - 1, max(0, int(round(t * SR / HOP))))


keep = json.load(open(ART / "keep.json"))
new = [list(r) for r in keep]
fixed = []
for i in range(len(new) - 1):
    g0, g1 = keep[i][1], keep[i + 1][0]
    if g1 - g0 <= 0.01 or g1 - g0 > MAX_GAP:
        continue
    seg = voiced[f(g0): f(g1)]
    if not seg.any():
        continue
    # voiced run attached to the left edge (a word tail) and to the right edge (a word onset)
    left = 0
    while left < len(seg) and seg[left:left + 3].any():
        left += 1
    right = 0
    while right < len(seg) and seg[len(seg) - 1 - right - 2: len(seg) - right].any():
        right += 1
    if left >= len(seg) - 3 or right >= len(seg) - 3:  # voiced across the whole gap: keep it all
        new[i][1] = g1
        fixed.append((round(g0, 2), round(g1, 2), "whole"))
        continue
    if left > 2:
        new[i][1] = round(g0 + (left + 4) * HOP / SR, 3)
        fixed.append((round(g0, 2), round(new[i][1], 2), "tail"))
    if right > 2:
        new[i + 1][0] = round(g1 - (right + 6) * HOP / SR, 3)
        fixed.append((round(new[i + 1][0], 2), round(g1, 2), "onset"))

# merge ranges that now touch
merged = []
for r in new:
    if merged and r[0] <= merged[-1][1] + 1e-3:
        merged[-1][1] = max(merged[-1][1], r[1])
    else:
        merged.append(r)

# old cut time -> new cut time (ranges only grew; each old range keeps its content)
old_starts, c = [], 0.0
for a, b in keep:
    old_starts.append(c)
    c += b - a
old_dur = c


def to_src(t: float) -> float:
    for (a, b), c0 in zip(keep, old_starts):
        if t <= c0 + (b - a) + 1e-6:
            return a + max(0.0, t - c0)
    return keep[-1][1]


def src_to_new(s: float) -> float:
    c = 0.0
    for a, b in merged:
        if s < a:
            return round(c, 3)
        if s <= b:
            return round(c + s - a, 3)
        c += b - a
    return round(c, 3)


def remap(t: float) -> float:
    return src_to_new(to_src(t))


TIME_KEYS = {"in", "out", "strike", "t", "headAt"}


def walk(o, key=None):
    if isinstance(o, dict):
        return {k: (remap(v) if isinstance(v, (int, float)) and (k in TIME_KEYS or key == "at" or k == "at") else walk(v, k))
                for k, v in o.items()}
    if isinstance(o, list):
        return [walk(v, key) for v in o]
    return o


if not fixed:
    print("no clipped speech found")
    sys.exit(0)
shutil.copy(ART / "keep.json", ART / "keep_pre_unclip.json")
# keep.json stays in cut_takes' input form (it adds the 1 s closing hold itself)
json.dump(merged, open(ART / "keep.json", "w"))

wp = ART / "words.json"
shutil.copy(wp, ART / "words_pre_unclip.json")
segs = json.load(open(wp))
for s in segs:
    for w in s["words"]:
        w["start"], w["end"] = remap(w["start"]), remap(w["end"])
json.dump(segs, open(wp, "w"), ensure_ascii=False)
sp = proj / "spec.json"
if sp.exists():
    shutil.copy(sp, proj / "spec_pre_unclip.json")
    spec = json.load(open(sp))
    zoom = spec.pop("zoom", [])
    spec = walk(spec)
    spec["zoom"] = [[remap(z[0])] + z[1:] for z in zoom]
    json.dump(spec, open(sp, "w"), ensure_ascii=False, indent=1)
new_dur = sum(b - a for a, b in merged)
print(f"{len(fixed)} clipped spots restored, cut {old_dur:.2f}s -> {new_dur:.2f}s")
for fx in fixed:
    print("  ", fx)
