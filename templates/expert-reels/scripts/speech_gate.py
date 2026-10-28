#!/usr/bin/env python3
"""Turn the voice track down between the speaker's own words.

Usage: speech_gate.py <in.wav> <words.json> <out.wav> [floor_db=-30] [raw.wav]

raw.wav (the voice before the denoiser): inside each word, wherever the denoiser took a
voiced stretch of the raw voice down by more than 12 dB (a soft vowel onset such as the
"Ə" of "Əsas" right after a cut), the raw voice is put back, so no syllable goes missing.

words.json: aligned segments ([{words: [{start, end}]}]) or a flat word list, in the
same timeline as the wav. Each word is padded (0.12 s before, 0.25 s after) and gaps
shorter than 0.25 s stay open, so breaths and word tails are not chopped; outside
the speech the gain ramps (40 ms) down to the floor. After the last word nothing is
gated, so the final word and the closing hold keep their natural tail.
"""
import json
import subprocess
import sys

import numpy as np

src, words_p, out = sys.argv[1:4]
floor = 10 ** (float(sys.argv[4]) / 20) if len(sys.argv) > 4 else 10 ** (-30 / 20)
sr = 48000


def load(p):
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(b, dtype=np.float32)


x = load(src)
segs = json.load(open(words_p, encoding="utf-8"))
words = [w for s in segs for w in s["words"]] if segs and "words" in segs[0] else segs
spans = []
for w in sorted(words, key=lambda w: w["start"]):
    a, b = max(0.0, w["start"] - 0.12), w["end"] + 0.25
    if spans and a - spans[-1][1] < 0.25:
        spans[-1][1] = max(spans[-1][1], b)
    else:
        spans.append([a, b])
# the closing tail stays open: word timings often end before the last word has died away
if spans:
    spans[-1][1] = len(x) / sr + 1
if len(sys.argv) > 5:  # give back syllables the denoiser swallowed
    r = load(sys.argv[5])[: len(x)]
    r = np.pad(r, (0, len(x) - len(r)))
    H = sr // 100
    n = len(x) // H
    db = lambda v: 20 * np.log10(np.sqrt((v[: n * H].reshape(n, H) ** 2).mean(1)) + 1e-9)
    rd, cd = db(r), db(x)
    inword = np.zeros(n, bool)
    for w in words:
        inword[max(0, int((w["start"] - 0.05) * 100)): int((w["end"] + 0.05) * 100)] = True
    loud = rd > np.median(rd[inword]) - 20 if inword.any() else np.zeros(n, bool)
    lost = inword & loud & (rd - cd > 12)
    wgt = np.convolve(np.repeat(lost.astype(np.float32), H), np.ones(H * 2) / (H * 2), mode="same")
    wgt = np.pad(wgt, (0, len(x) - len(wgt)))[: len(x)]
    x = (x * (1 - wgt) + r * wgt).astype(np.float32)
    print(f"restored {lost.sum() * 10} ms the denoiser swallowed inside words")
g = np.full(len(x), floor, dtype=np.float32)
for a, b in spans:
    g[int(a * sr): int(b * sr)] = 1.0
ramp = int(0.04 * sr)
g = np.convolve(g, np.ones(ramp) / ramp, mode="same").astype(np.float32)
y = (x * g).astype(np.float32)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-", "-c:a", "pcm_s16le", out], input=y.tobytes(), check=True)
print(f"gated {len(spans)} speech spans")
