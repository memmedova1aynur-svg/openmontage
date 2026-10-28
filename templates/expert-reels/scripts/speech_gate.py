#!/usr/bin/env python3
"""Turn the voice track down between the speaker's own words.

Usage: speech_gate.py <in.wav> <words.json> <out.wav> [floor_db=-30]

words.json: aligned segments ([{words: [{start, end}]}]) or a flat word list, in the
same timeline as the wav. Each word is padded (0.10 s before, 0.15 s after) and gaps
shorter than 0.25 s stay open, so breaths and word tails are not chopped; outside
the speech the gain ramps (40 ms) down to the floor.
"""
import json
import subprocess
import sys

import numpy as np

src, words_p, out = sys.argv[1:4]
floor = 10 ** (float(sys.argv[4]) / 20) if len(sys.argv) > 4 else 10 ** (-30 / 20)
sr = 48000
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
x = np.frombuffer(raw, dtype=np.float32)
segs = json.load(open(words_p, encoding="utf-8"))
words = [w for s in segs for w in s["words"]] if segs and "words" in segs[0] else segs
spans = []
for w in sorted(words, key=lambda w: w["start"]):
    a, b = max(0.0, w["start"] - 0.10), w["end"] + 0.15
    if spans and a - spans[-1][1] < 0.25:
        spans[-1][1] = max(spans[-1][1], b)
    else:
        spans.append([a, b])
g = np.full(len(x), floor, dtype=np.float32)
for a, b in spans:
    g[int(a * sr): int(b * sr)] = 1.0
ramp = int(0.04 * sr)
g = np.convolve(g, np.ones(ramp) / ramp, mode="same").astype(np.float32)
y = (x * g).astype(np.float32)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-", "-c:a", "pcm_s16le", out], input=y.tobytes(), check=True)
print(f"gated {len(spans)} speech spans")
