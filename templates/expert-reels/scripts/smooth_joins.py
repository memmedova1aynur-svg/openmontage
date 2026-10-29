#!/usr/bin/env python3
"""Soften the jump cuts of a tightened edit: every join of the cut gets a short cross-dissolve
(picture and sound), so pauses removed from a talking head no longer read as hard cuts.

Usage: smooth_joins.py <project-dir> [fade=0.16]

Joins come from artifacts/keep.json (the frame-snapped source ranges of assets/video/cut.mp4).
Each dissolve overlaps the two pieces by `fade` seconds, so the cut gets shorter by that much per
join: artifacts/words.json and spec.json (in/out/at/strike/t/headAt, zoom, caption_shift) are moved
to the new timeline. Writes assets/video/cut.mp4 (the hard-cut original is kept as cut_hard.mp4)
and *_hard backups of words/spec. Run it once, after the last cut_takes and before setup_workspace.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

proj = Path(sys.argv[1])
F = float(sys.argv[2]) if len(sys.argv) > 2 else 0.16
cut = proj / "assets/video/cut.mp4"
hard = proj / "assets/video/cut_hard.mp4"
if not hard.exists():
    shutil.copy(cut, hard)
keep = json.load(open(proj / "artifacts/keep.json"))
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(hard)],
                           capture_output=True, text=True).stdout)
joins, c = [], 0.0
for a, b in keep[:-1]:
    c += b - a
    joins.append(round(c * 30) / 30)
bounds = [0.0] + joins + [dur]
n = len(bounds) - 1
if n < 2:
    print("no joins")
    sys.exit(0)
fc, acc = [], 0.0
for i in range(n):
    fc.append(f"[0:v]trim={bounds[i]}:{bounds[i + 1]},setpts=PTS-STARTPTS[v{i}];[0:a]atrim={bounds[i]}:{bounds[i + 1]},asetpts=PTS-STARTPTS[a{i}]")
v, a = "v0", "a0"
for i in range(1, n):
    acc += bounds[i] - bounds[i - 1] - (F if i > 1 else 0)
    off = acc - F
    fc.append(f"[{v}][v{i}]xfade=transition=fade:duration={F}:offset={off:.4f}[vx{i}];[{a}][a{i}]acrossfade=d={F}:c1=tri:c2=tri[ax{i}]")
    v, a = f"vx{i}", f"ax{i}"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(hard), "-filter_complex", ";".join(fc), "-map", f"[{v}]", "-map", f"[{a}]",
                "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", str(cut)], check=True)


def remap(x):  # each join before x pulls it F seconds earlier; inside a dissolve it lands mid-fade
    return round(x - F * sum(1 for j in joins if x >= j), 3)


for name in ("artifacts/words.json", "spec.json"):
    p = proj / name
    bk = p.with_name(p.stem + "_hard.json")
    if not bk.exists():
        shutil.copy(p, bk)
    d = json.load(open(bk))
    if name.endswith("words.json"):
        for g in d:
            for w in g["words"]:
                w["start"], w["end"] = remap(w["start"]), remap(w["end"])
    else:
        K = {"in", "out", "strike", "t", "headAt", "at"}

        def walk(o):
            if isinstance(o, dict):
                return {k: (remap(v) if k in K and isinstance(v, (int, float)) else walk(v)) for k, v in o.items()}
            if isinstance(o, list):
                return [walk(v) for v in o]
            return o
        z, cs = d.pop("zoom", []), d.pop("caption_shift", [])
        d = walk(d)
        d["zoom"] = [[remap(e[0])] + e[1:] for e in z]
        d["caption_shift"] = [[remap(s[0]), remap(s[1])] + s[2:] for s in cs]
        d["smooth_joins"] = F
    json.dump(d, open(p, "w"), ensure_ascii=False, indent=1)
print(f"{len(joins)} joins dissolved ({F}s), {dur:.2f}s -> {dur - F * len(joins):.2f}s")
