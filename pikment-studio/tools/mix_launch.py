#!/usr/bin/env python3
"""Pikment 001 launch: assemble voice takes on a fixed beat-aligned timeline, beat-locked music, SFX.

Reads  remotion-composer/src/productions/pikment001.timeline.json
Takes  /tmp/claude-0/pik/lt/<take>.mp3 (ElevenLabs, chosen per sentence)
Writes remotion-composer/public/pikment_launch/audio_001.wav  (+ preview stems)
Music is time-stretched to exactly 120 BPM so scene changes land on the beat grid.
"""
import json, subprocess, tempfile, sys
import numpy as np
from scipy.io import wavfile

SR = 48000
ROOT = "remotion-composer/"
TL = json.load(open(ROOT + "src/productions/pikment001.timeline.json"))
TAKES = "/tmp/claude-0/pik/lt/"
SFX = "/tmp/claude-0/pik/sfx2/"
MUSIC = "/tmp/claude-0/pik/music/m770.mp3"
SRC_BPM, FIRST_BEAT = 117.0, 0.029
OUT = ROOT + "public/pikment_launch/audio_001.wav"
TOTAL = TL["total"]

CHAIN = ("highpass=f=75,lowpass=f=15000,"
         "equalizer=f=110:t=q:w=1:g=1.5,equalizer=f=3200:t=q:w=1.1:g=2.2,equalizer=f=9500:t=q:w=1:g=1.0,"
         "deesser=i=0.35:m=0.5:f=0.5,"
         "acompressor=threshold=-21dB:ratio=3:attack=6:release=110:makeup=3,"
         "aecho=0.9:0.88:22|41:0.10|0.06")


def dec(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def span(x):
    w = int(0.02 * SR); n = len(x) // w
    db = 20 * np.log10(np.sqrt((x[: n * w].reshape(n, w) ** 2).mean(1)) + 1e-6)
    idx = np.where(db > np.percentile(db, 90) - 25)[0]
    return idx[0] * 0.02, (idx[-1] + 1) * 0.02


def process(x):
    a, b = span(x)
    s0, s1 = max(int((a - 0.02) * SR), 0), min(int((b + 0.10) * SR), len(x))
    seg = x[s0:s1].copy()
    lead = a - s0 / SR  # seconds from segment start to speech onset
    voiced = seg[int(0.04 * SR): int((lead + b - a) * SR)]
    seg *= (10 ** (-21 / 20)) / (np.sqrt((voiced ** 2).mean()) + 1e-9)
    fi, fo = int(0.01 * SR), int(0.045 * SR)
    seg[:fi] *= np.linspace(0, 1, fi); seg[-fo:] *= np.linspace(1, 0, fo)
    with tempfile.TemporaryDirectory() as d:
        wavfile.write(f"{d}/in.wav", SR, seg)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{d}/in.wav", "-af", CHAIN, "-ar", str(SR), "-c:a", "pcm_f32le", f"{d}/out.wav"], check=True)
        y = wavfile.read(f"{d}/out.wav")[1].astype(np.float32)
    return y, lead, b - a


def pauses(y, lead, dur):
    w = int(0.01 * SR); n = len(y) // w
    db = 20 * np.log10(np.sqrt((y[: n * w].reshape(n, w) ** 2).mean(1)) + 1e-6)
    thr = np.percentile(db, 90) - 28
    out, run = [], None
    for i, v in enumerate(db):
        t = i * 0.01 - lead
        if v < thr and 0.1 < t < dur - 0.1:
            run = run or t
        else:
            if run is not None and t - run >= 0.07: out.append([round(run, 2), round(t, 2)])
            run = None
    return out


def main():
    starts = TL["voiceStart"]
    voice = np.zeros(int(TOTAL * SR) + SR, np.float32)
    info = []
    for take, st in zip(TL["takes"], starts):
        y, lead, dur = process(dec(f"{TAKES}{take}.mp3"))
        i = int((st - lead) * SR)
        voice[i: i + len(y)] += y
        info.append({"start": st, "dur": round(dur, 2), "pauses": pauses(y, lead, dur)})
    json.dump(info, open(ROOT + "src/productions/pikment001.voice.json", "w"), indent=1)
    print(json.dumps(info))
    wavfile.write("/tmp/claude-0/pik/voice_001.wav", SR, voice)

    # ---- SFX (real Mixkit recordings), aligned to the events in the timeline ----
    def load(k):
        out = f"{SFX}s{k}_48k.wav"
        subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", f"{SFX}s{k}.mp3", "-ac", "1", "-ar", str(SR), "-c:a", "pcm_f32le", out])
        return wavfile.read(out)[1].astype(np.float32)
    snd = {k: load(k) for k in [1490, 1492, 2356, 2357, 2577, 2573, 2903, 951]}

    def peak_t(x):
        w = int(0.01 * SR); n = len(x) // w
        return float(np.argmax(np.sqrt((x[: n * w].reshape(n, w) ** 2).mean(1))) * 0.01)
    track = np.zeros(int(TOTAL * SR) + SR * 4, np.float32)

    def put(k, at, gain, align=False):
        x = snd[k] * gain
        if align: at -= peak_t(snd[k])
        i = int(max(at, 0) * SR)
        track[i: i + len(x)] += x[: len(track) - i]

    T = TL
    put(1492, T["hook"]["words"][0] - 0.1, 0.20, True)            # first word in
    put(2356, T["hook"]["words"][1], 0.22)                        # "daha əlçatan" accent
    put(1490, T["hook"]["underline"][0] + 0.2, 0.26, True)        # underline sweep
    put(2903, T["laptop"]["morph"][1], 0.22, True)                # match-cut lands: laptop
    for i, t in enumerate(T["cards"]): put(2356 if i % 2 == 0 else 2357, t, 0.30)
    for t in T["cards"][:3]: put(2577, t + 0.18, 0.16)
    put(1490, T["sweep1"][0] + 0.3, 0.26, True)                   # sweep to domain
    put(2356, T["domain"][0] + 0.15, 0.30)
    put(1492, T["phoneIn"] - 0.2, 0.24, True)                     # phone rises
    for i, t in enumerate(T["appPops"]): put(2357 if i % 2 else 2356, t, 0.26)
    put(1490, T["together"] - 0.1, 0.22, True)
    put(2573, T["appLabel"], 0.20)
    put(2903, T["soon"] + 0.03, 0.40, True)                       # TEZLİKLƏ impact
    put(1490, T["logo"] - 0.2, 0.28, True)
    put(951, T["logo"] + 0.9, 0.24)                               # logo sparkle
    pk = np.max(np.abs(track))
    if pk > 0.95: track /= pk / 0.95
    wavfile.write("/tmp/claude-0/pik/sfx_001.wav", SR, track)

    # ---- music: stretch to 120 BPM, align first beat to t=0, duck under voice ----
    ratio = 120.0 / SRC_BPM
    first = FIRST_BEAT / ratio
    fo = round(TOTAL - 3.5, 2)
    fc = (
        f"[0]aresample=48000,loudnorm=I=-14:TP=-1.5:LRA=7,asplit=2[v1][v2];"
        f"[1]aresample=48000,atempo={ratio:.5f},atrim=start={first:.4f},asetpts=PTS-STARTPTS,atrim=0:{TOTAL},"
        f"equalizer=f=2500:t=q:w=0.9:g=-3.5,equalizer=f=250:t=q:w=1:g=-1.5,afade=t=in:d=0.6,afade=t=out:st={fo}:d=3.5,loudnorm=I=-20:TP=-3[m];"
        f"[m][v2]sidechaincompress=threshold=0.04:ratio=3.5:attack=25:release=420:makeup=1[md];"
        f"[2]aresample=48000,atrim=0:{TOTAL}[s];"
        f"[v1][md][s]amix=inputs=3:normalize=0:duration=longest,loudnorm=I=-14.5:TP=-1.5:LRA=9,atrim=0:{TOTAL},aresample=48000[o]"
    )
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", "/tmp/claude-0/pik/voice_001.wav", "-i", MUSIC, "-i", "/tmp/claude-0/pik/sfx_001.wav", "-filter_complex", fc, "-map", "[o]", OUT])
    print("wrote", OUT)


if __name__ == "__main__":
    main()
