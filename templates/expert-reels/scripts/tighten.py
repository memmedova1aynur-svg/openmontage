#!/usr/bin/env python3
"""Shorten every pause in an edit and re-time everything that hangs off the cut.

Usage:
    python templates/expert-reels/scripts/tighten.py <project-dir> [<source.mp4>]

Reads the cleaned voice (artifacts/dn/out/voice.wav, from denoise.sh) of the current
cut (assets/video/cut.mp4), finds silences with ffmpeg silencedetect, and keeps only
~0.14 s after the last word and ~0.10 s before the next one. The opening silence is
trimmed too; the closing one (the 1 s hold after the last word) is left alone.

The new cut is re-made from the source (default assets/source/flipped.mp4) through
artifacts/keep.json, so there is no extra generation of re-encoding. words.json and
spec.json (overlay/cutaway/panel/sfx/zoom times) are mapped onto the new timeline;
the old files are kept as *_v1.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

LEAD, TRAIL, MIN_CUT = 0.14, 0.10, 0.08
TIME_KEYS = {"in", "out", "strike", "t", "headAt"}

proj = Path(sys.argv[1])
src = Path(sys.argv[2]) if len(sys.argv) > 2 else proj / "assets/source/flipped.mp4"
ART = proj / "artifacts"


def dur(p: Path) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True, check=True).stdout)


cut_dur = dur(proj / "assets/video/cut.mp4")
log = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(ART / "dn/out/voice.wav"), "-af", "silencedetect=noise=-40dB:d=0.25",
                      "-f", "null", "-"], capture_output=True, text=True).stderr
starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
removed = []
# REMOVE='[[a,b],...]' (cut timeline): drop exactly these spans (a false start the
# silence detector cannot see) instead of shortening pauses; their words are dropped too.
manual = json.loads(os.environ["REMOVE"]) if os.environ.get("REMOVE") else None
if manual:
    starts, ends = [], []
    removed = [tuple(x) for x in sorted(manual)]
for s, e in zip(starts, ends):
    if e >= cut_dur - 0.05:  # closing hold stays
        continue
    a, b = (0.0, e - TRAIL) if s <= 0.01 else (s + LEAD, e - TRAIL)
    if b - a >= MIN_CUT:
        removed.append((a, b))

# kept pieces on the old cut timeline, and where each one starts on the new timeline
kept, t = [], 0.0
for a, b in removed:
    if a > t:
        kept.append((t, a))
    t = b
kept.append((t, cut_dur))
new_start, acc = [], 0.0
for a, b in kept:
    new_start.append(acc)
    acc += b - a


def remap(x: float) -> float:
    for (a, b), n in zip(kept, new_start):
        if x < a:  # inside a removed pause: snap to the next kept piece
            return round(n, 3)
        if x <= b:
            return round(n + x - a, 3)
    return round(acc, 3)


# old cut timeline -> source timeline through the previous keep list
old_keep = json.load(open(ART / "keep.json"))
src_dur = dur(src)
old_keep[-1][1] = min(src_dur, old_keep[-1][1] + 1.0)  # cut_takes added the 1 s hold
pieces, c = [], 0.0
for a, b in old_keep:
    pieces.append((c, c + b - a, a))
    c += b - a


def to_src(x: float) -> float:
    for c0, c1, s0 in pieces:
        if x <= c1 + 1e-6:
            return s0 + max(0.0, x - c0)
    return pieces[-1][2] + pieces[-1][1] - pieces[-1][0]


new_keep = []
for a, b in kept:
    # split a kept piece where it crosses an old join
    cur = a
    for c0, c1, s0 in pieces:
        if c1 <= cur or c0 >= b:
            continue
        lo, hi = max(cur, c0), min(b, c1)
        if hi - lo > 0.02:
            new_keep.append([round(s0 + lo - c0, 3), round(s0 + hi - c0, 3)])
        cur = hi
# the last piece already holds 1 s after the last word; cut_takes adds 1 s again (capped at the source end)
new_keep[-1][1] = round(new_keep[-1][1] - 1.0, 3)

shutil.copy(ART / "keep.json", ART / "keep_v1.json")
json.dump(new_keep, open(ART / "keep.json", "w"))

words_p = ART / "words.json"
shutil.copy(words_p, ART / "words_v1.json")
segs = json.load(open(words_p))
for seg in segs:
    if manual and not os.environ.get("KEEPWORDS"):  # KEEPWORDS=1: the spans are pauses, keep every word
        seg["words"] = [w for w in seg["words"] if not any(a <= w["start"] < b for a, b in removed)]
    for w in seg["words"]:
        w["start"], w["end"] = remap(w["start"]), max(remap(w["start"]) + 0.05, remap(w["end"]))
json.dump(segs, open(words_p, "w"), ensure_ascii=False)


def walk(o, key=None):
    if isinstance(o, dict):
        return {k: (remap(v) if isinstance(v, (int, float)) and (k in TIME_KEYS or key == "at" or k == "at")
                    else walk(v, k)) for k, v in o.items()}
    if isinstance(o, list):
        return [walk(v, key) for v in o]
    return o


spec_p = proj / "spec.json"
if spec_p.exists():  # tightening before the spec is written is fine too
    shutil.copy(spec_p, proj / "spec_v1.json")
    spec = json.load(open(spec_p))
    zoom = spec.pop("zoom", [])
    spec = walk(spec)
    spec["zoom"] = [[remap(z[0])] + z[1:] for z in zoom]
    json.dump(spec, open(spec_p, "w"), ensure_ascii=False, indent=1)

print(f"{len(removed)} pauses shortened, {cut_dur:.2f}s -> {acc:.2f}s; new keep: {len(new_keep)} ranges")

# the cleaned voice can hide soft syllables; give back anything voiced in the raw audio
if not manual:  # hand-picked spans are trusted as they are
    subprocess.run([sys.executable, str(Path(__file__).with_name("unclip.py")), str(proj), str(src)], check=True)
