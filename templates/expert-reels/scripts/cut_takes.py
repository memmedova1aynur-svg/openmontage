#!/usr/bin/env python3
"""Cut retakes out of the footage and re-time the approved words to match.

Usage:
    python templates/expert-reels/scripts/cut_takes.py <source> <words.json> <keep.json> <out_video> <out_words.json>

<keep.json> is a list of [start, end] seconds in the source to keep, in order,
chosen by reading the transcript: when a sentence is said more than once keep
the best complete take and drop the false starts. Every kept piece gets a 40 ms
audio fade in/out so the joins don't click; put boundaries in the pauses
between words (use the word timings, padded ~0.08 s).
"""
from __future__ import annotations

import json
import subprocess
import sys

src, words_path, keep_path, out_video, out_words = sys.argv[1:6]
keep = json.load(open(keep_path, encoding="utf-8"))
segs = json.load(open(words_path, encoding="utf-8"))
if isinstance(segs, dict):  # raw transcriber output
    words = segs["word_timestamps"]
else:  # aligned segments ([{words: [...]}]) or a flat word list
    words = [w for s in segs for w in s["words"]] if segs and "words" in segs[0] else segs

# video: trim + concat with tiny audio fades at every join
parts, labels = [], []
for i, (a, b) in enumerate(keep):
    d = b - a
    parts.append(
        f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];"
        f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.04,afade=t=out:st={max(0, d - 0.04):.3f}:d=0.04[a{i}]"
    )
    labels.append(f"[v{i}][a{i}]")
fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(keep)}:v=1:a=1[v][a]"
subprocess.run(
    ["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
     "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p", "-r", "30",
     "-c:a", "aac", "-b:a", "256k", out_video],
    check=True,
)

# words: keep those whose midpoint falls inside a kept range, shifted onto the new timeline
out, offset = [], 0.0
for a, b in keep:
    for w in words:
        mid = (w["start"] + w["end"]) / 2
        if a <= mid < b:
            out.append({"word": w["word"], "start": round(max(a, w["start"]) - a + offset, 3), "end": round(min(b, w["end"]) - a + offset, 3)})
    offset += b - a
json.dump([{"id": 0, "start": out[0]["start"], "end": out[-1]["end"], "text": " ".join(w["word"] for w in out), "words": out}],
          open(out_words, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"kept {len(keep)} ranges, {offset:.2f}s total, {len(out)} words -> {out_video}")
