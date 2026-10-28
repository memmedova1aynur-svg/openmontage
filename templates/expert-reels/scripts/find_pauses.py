#!/usr/bin/env python3
"""List the pauses worth shortening in a cut, as a REMOVE list for tighten.py.

Usage: find_pauses.py <cut.mp4> [min_pause=0.4] [keep_each_side=0.12]

Works on the RAW audio (no denoiser, which can hide soft syllables): a pause is a run of
10 ms frames within 9 dB of the room floor. Each pause keeps `keep_each_side` seconds next
to the speech on both sides; the opening and the last 1.2 s (closing hold) are left alone.
Prints JSON: [[start, end], ...] on the cut timeline.
"""
import json
import subprocess
import sys

import numpy as np

src = sys.argv[1]
min_pause = float(sys.argv[2]) if len(sys.argv) > 2 else 0.4
side = float(sys.argv[3]) if len(sys.argv) > 3 else 0.12
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                     capture_output=True, check=True).stdout
x = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
H = 160
n = len(x) // H
db = 20 * np.log10(np.sqrt((x[: n * H].reshape(n, H) ** 2).mean(1)) + 1)
quiet = db < np.percentile(db, 12) + 9
out, i = [], 0
while i < n:
    if quiet[i]:
        j = i
        while j < n and quiet[j]:
            j += 1
        a, b = i / 100, j / 100
        if b - a >= min_pause and a > 0.2 and b < n / 100 - 1.2:
            out.append([round(a + side, 2), round(b - side, 2)])
        i = j
    else:
        i += 1
print(json.dumps(out))
