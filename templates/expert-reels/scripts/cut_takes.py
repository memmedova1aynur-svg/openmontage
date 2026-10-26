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
import os
import shutil
import subprocess
import sys
import tempfile

src, words_path, keep_path, out_video, out_words = sys.argv[1:6]
keep = json.load(open(keep_path, encoding="utf-8"))
segs = json.load(open(words_path, encoding="utf-8"))
if isinstance(segs, dict):  # raw transcriber output
    words = segs["word_timestamps"]
else:  # aligned segments ([{words: [...]}]) or a flat word list
    words = [w for s in segs for w in s["words"]] if segs and "words" in segs[0] else segs

# video: encode each kept range on its own (accurate seek, tiny audio fades so joins
# don't click), then join with the concat demuxer. One filter graph with many trim
# branches buffers every decoded frame and gets OOM-killed on long phone footage.
tmp = tempfile.mkdtemp(prefix="cut_takes_")
listfile = os.path.join(tmp, "list.txt")
with open(listfile, "w") as lf:
    for i, (a, b) in enumerate(keep):
        d = b - a
        piece = os.path.join(tmp, f"p{i:03d}.mp4")
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-ss", f"{a}", "-i", src, "-t", f"{d}",
             "-af", f"afade=t=in:d=0.04,afade=t=out:st={max(0, d - 0.04):.3f}:d=0.04",
             "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p", "-r", "30",
             "-c:a", "aac", "-b:a", "256k", "-ar", "48000", piece],
            check=True,
        )
        lf.write(f"file '{piece}'\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", listfile, "-c", "copy",
                "-movflags", "+faststart", out_video], check=True)
shutil.rmtree(tmp)

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
