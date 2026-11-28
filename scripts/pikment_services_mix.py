#!/usr/bin/env python3
"""Assemble the Pikment services-ad audio.

Takes the chosen per-sentence voice takes (ElevenLabs, downloaded to TAKES),
trims each to its spoken span, levels them, runs one shared voice-processing
chain, lays them out with natural pauses, then mixes a ducked music bed and
real sound effects. Writes the timing JSON the Remotion composition reads.

Usage (from repo root):  python3 scripts/pikment_services_mix.py
"""
import json
import re
import subprocess
import tempfile

import numpy as np
from scipy.io import wavfile

SR = 48000
TAKES = "/tmp/claude-0/pik/takes/"
SFX = "/tmp/claude-0/pik/sfx2/"
MUSIC = "/tmp/claude-0/pik/music/m953.mp3"
OUT_WAV = "remotion-composer/public/pikment/audio_services_v5.wav"
TIMING = "remotion-composer/src/pikmentServicesTiming.json"
ROOT = "remotion-composer/src/Root.tsx"

SEL = ["s1_c", "s2_a", "s3_a", "s4_b", "s5_a", "s6_a", "s7_a", "s8_d"]
GAPS = [0.45, 0.30, 0.30, 0.30, 0.30, 0.30, 0.42]
LEAD = 0.35
TAIL = 2.5

CHAIN = (
    "highpass=f=75,lowpass=f=15000,"
    "equalizer=f=110:t=q:w=1:g=1.5,equalizer=f=3200:t=q:w=1.1:g=2.2,equalizer=f=9500:t=q:w=1:g=1.0,"
    "deesser=i=0.35:m=0.5:f=0.5,"
    "acompressor=threshold=-21dB:ratio=3:attack=6:release=110:makeup=3,"
    "aecho=0.9:0.88:22|41:0.10|0.06"
)


def dec(path: str) -> np.ndarray:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
        capture_output=True, check=True,
    ).stdout
    return np.frombuffer(raw, np.float32).copy()


def speech_span(x: np.ndarray) -> tuple[float, float]:
    w = int(0.02 * SR)
    n = len(x) // w
    db = 20 * np.log10(np.sqrt((x[: n * w].reshape(n, w) ** 2).mean(1)) + 1e-6)
    idx = np.where(db > np.percentile(db, 90) - 25)[0]
    return idx[0] * 0.02, (idx[-1] + 1) * 0.02


def process(x: np.ndarray) -> tuple[np.ndarray, float]:
    a, b = speech_span(x)
    s0, s1 = max(int((a - 0.04) * SR), 0), min(int((b + 0.10) * SR), len(x))
    seg = x[s0:s1].copy()
    # level every sentence to the same voiced RMS
    voiced = seg[int(0.04 * SR): int((b - a + 0.04) * SR)]
    rms = np.sqrt((voiced ** 2).mean()) + 1e-9
    seg *= (10 ** (-21 / 20)) / rms
    fi, fo = int(0.01 * SR), int(0.045 * SR)
    seg[:fi] *= np.linspace(0, 1, fi)
    seg[-fo:] *= np.linspace(1, 0, fo)
    with tempfile.TemporaryDirectory() as d:
        wavfile.write(f"{d}/in.wav", SR, seg)
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", f"{d}/in.wav", "-af", CHAIN, "-ar", str(SR), "-c:a", "pcm_f32le", f"{d}/out.wav"],
            check=True,
        )
        _, y = wavfile.read(f"{d}/out.wav")
    return y.astype(np.float32), b - a


def main() -> None:
    processed = [process(dec(f"{TAKES}{n}.mp3")) for n in SEL]
    t = LEAD
    starts, durs, placed = [], [], []
    for i, (y, spoken) in enumerate(processed):
        starts.append(round(t + 0.04, 2))
        durs.append(round(spoken, 2))
        placed.append((t, y))
        t += len(y) / SR + (GAPS[i] if i < len(GAPS) else 0)
    voice_end = starts[-1] + durs[-1]
    total = round(voice_end + TAIL, 2)
    json.dump({"voiceStarts": starts, "voiceDurs": durs, "total": total}, open(TIMING, "w"))
    print("starts", starts, "durs", durs, "total", total)

    voice = np.zeros(int(total * SR) + SR, np.float32)
    for pos, y in placed:
        i = int(pos * SR)
        voice[i: i + len(y)] += y
    wavfile.write("/tmp/claude-0/pik/voice_track_v5.wav", SR, voice)

    # --- sound effects (real Mixkit recordings), aligned to scene boundaries and reveals ---
    lead = 0.15
    bounds = [
        (0 if i == 0 else s - lead, (total if i == len(starts) - 1 else starts[i + 1] - lead))
        for i, s in enumerate(starts)
    ]

    def load(k: int) -> np.ndarray:
        out = f"{SFX}s{k}_48k.wav"
        subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", f"{SFX}s{k}.mp3", "-ac", "1", "-ar", str(SR), "-c:a", "pcm_f32le", out])
        return wavfile.read(out)[1].astype(np.float32)

    snd = {k: load(k) for k in [1490, 1492, 2356, 2357, 2577, 2573, 2903, 951]}

    def peak_t(x: np.ndarray) -> float:
        w = int(0.01 * SR)
        n = len(x) // w
        return float(np.argmax(np.sqrt((x[: n * w].reshape(n, w) ** 2).mean(1))) * 0.01)

    track = np.zeros(int(total * SR) + SR * 4, np.float32)

    def put(k: int, at: float, gain: float, align: bool = False) -> None:
        x = snd[k] * gain
        if align:
            at -= peak_t(snd[k])
        at = max(at, 0)
        i = int(at * SR)
        track[i: i + len(x)] += x[: len(track) - i]

    put(1492, 0.45, 0.22, True)
    for i in range(1, len(bounds)):
        put(1490, bounds[i][0], 0.26, True)
    f1 = bounds[1][0]
    for k in range(6):
        put(2356, f1 + 0.5 + 0.28 * k, 0.30)
    put(2577, f1 + 1.2, 0.2)
    put(2577, f1 + 1.6, 0.2)
    for b, n in {2: 4, 3: 2, 4: 2, 5: 4}.items():
        f = bounds[b][0]
        ln = bounds[b][1] - bounds[b][0]
        span = max(ln - 2.4, 1)
        for i in range(n):
            at = 1.0 + ((i * span / (n - 1)) * 0.8 if n > 1 else 0)
            put(2356 if i % 2 == 0 else 2357, f + at, 0.30)
    f6 = bounds[6][0]
    put(2356, f6 + 0.8, 0.3)
    put(2573, f6 + 3.2, 0.22)
    f7 = bounds[7][0]
    put(2903, f7 + 0.35, 0.34, True)
    put(951, f7 + 1.3, 0.24)
    pk = np.max(np.abs(track))
    if pk > 0.95:
        track /= pk / 0.95
    wavfile.write("/tmp/claude-0/pik/sfx_track_v5.wav", SR, track)

    # --- final mix: voice + music bed (gently ducked) + effects ---
    fo = round(total - 3, 2)
    fc = (
        f"[0]aresample=48000,loudnorm=I=-14:TP=-1.5:LRA=7,asplit=2[v1][v2];"
        f"[1]aresample=48000,atrim=0:{total},afade=t=in:d=1.2,afade=t=out:st={fo}:d=3,loudnorm=I=-19:TP=-3[m];"
        f"[m][v2]sidechaincompress=threshold=0.05:ratio=3:attack=30:release=450:makeup=1[md];"
        f"[2]aresample=48000,atrim=0:{total}[s];"
        f"[v1][md][s]amix=inputs=3:normalize=0:duration=longest,loudnorm=I=-14.5:TP=-1.5:LRA=9,atrim=0:{total},aresample=48000[o]"
    )
    subprocess.check_call(
        ["ffmpeg", "-v", "error", "-y", "-i", "/tmp/claude-0/pik/voice_track_v5.wav", "-i", MUSIC,
         "-i", "/tmp/claude-0/pik/sfx_track_v5.wav", "-filter_complex", fc, "-map", "[o]", OUT_WAV]
    )

    frames = int(round(total * 30))
    r = open(ROOT).read()
    r = re.sub(r"(component=\{PikmentServicesAd\}\s*durationInFrames=\{)\d+(\})", lambda m: m.group(1) + str(frames) + m.group(2), r)
    r = re.sub(r"pikment/audio_services_v\d+\.wav", "pikment/audio_services_v5.wav", r)
    open(ROOT, "w").write(r)
    print("frames", frames)


if __name__ == "__main__":
    main()
