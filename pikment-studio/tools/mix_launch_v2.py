#!/usr/bin/env python3
"""Pikment 001 v2 audio: ONE continuous ElevenLabs take, cut at sentence boundaries and re-spaced on the
120 BPM grid; word timings (from Whisper on the take) are re-timed to the layout and written for the composition.
Music: ElevenLabs Music (120 BPM, 27 s), delayed 12 ms so beats sit exactly on the 0.5 s grid.
Run from repo root:  python3 pikment-studio/tools/mix_launch_v2.py
"""
import json, subprocess, tempfile
import numpy as np
from scipy.io import wavfile

SR = 48000
P = "remotion-composer/"
TL = json.load(open(P + "src/productions/pikment001v2.timeline.json"))
RAW = json.load(open(P + "src/productions/pikment001v2.words.raw.json"))
WORK = "/tmp/claude-0/pik/v2/"
VOICE, MUSIC = WORK + "voiceA.mp3", WORK + "music.mp3"
SFX = "/tmp/claude-0/pik/sfx2/"
OUT = P + "public/pikment_launch/audio_v2.wav"
TOTAL = TL["total"]
BEAT_SHIFT = 0.012
TEXT = ["Pikment", "artıq", "daha", "əlçatan", "olacaq", "Təlimlər", "xidmətlər", "mentorluq", "və", "peşəkar", "inkişaf", "imkanları", "bir", "ünvanda",
        "Pikment", "nöqtə", "az", "İndi", "isə", "pedaqoqlar", "üçün", "yeni", "rəqəmsal", "imkanlar", "Pikment", "mobil", "tətbiqi", "Tezliklə", "Pikment", "Hər", "kəsin", "öz", "rəngi", "var"]
SENT_OF = [0]*5 + [1]*9 + [2]*3 + [3]*7 + [4]*3 + [5] + [6]*6

CHAIN = ("highpass=f=75,lowpass=f=15000,equalizer=f=110:t=q:w=1:g=1.5,equalizer=f=3200:t=q:w=1.1:g=2.2,equalizer=f=9500:t=q:w=1:g=1.0,"
         "deesser=i=0.35:m=0.5:f=0.5,acompressor=threshold=-21dB:ratio=3:attack=6:release=110:makeup=3,aecho=0.9:0.88:22|41:0.10|0.06")


def dec(p):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout, np.float32).copy()


def main():
    x = dec(VOICE)
    cuts = TL["cuts"] + [len(x) / SR]
    voice = np.zeros(int(TOTAL * SR) + SR, np.float32)
    words = []
    for s in range(7):
        a, b = cuts[s], cuts[s + 1]
        seg = x[int(a * SR): int(b * SR)].copy()
        idx = [i for i, k in enumerate(SENT_OF) if k == s]
        first_w = RAW[idx[0]][1] - a  # where the first word starts inside the segment
        lead = max(first_w - 0.02, 0)  # trim silence before it
        seg = seg[int(lead * SR):]
        voiced = seg[: int((RAW[idx[-1]][2] - a - lead) * SR)]
        seg *= (10 ** (-21 / 20)) / (np.sqrt((voiced ** 2).mean()) + 1e-9)
        fi, fo = int(0.01 * SR), int(0.05 * SR)
        seg[:fi] *= np.linspace(0, 1, fi); seg[-fo:] *= np.linspace(1, 0, fo)
        with tempfile.TemporaryDirectory() as d:
            wavfile.write(f"{d}/i.wav", SR, seg)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{d}/i.wav", "-af", CHAIN, "-ar", str(SR), "-c:a", "pcm_f32le", f"{d}/o.wav"], check=True)
            y = wavfile.read(f"{d}/o.wav")[1].astype(np.float32)
        st = TL["voiceStart"][s] - 0.02  # speech onset lands on the beat (0.02 s of pre-roll kept)
        i0 = int(st * SR)
        voice[i0: i0 + len(y)] += y
        for i in idx:
            w0 = TL["voiceStart"][s] + (RAW[i][1] - a - first_w)
            w1 = TL["voiceStart"][s] + (RAW[i][2] - a - first_w)
            words.append({"w": TEXT[i], "t0": round(w0, 3), "t1": round(w1, 3), "s": s})
    json.dump(words, open(P + "src/productions/pikment001v2.words.json", "w"), ensure_ascii=False, indent=0)
    wavfile.write(WORK + "voice_v2.wav", SR, voice)
    W = [w["t0"] for w in words]
    print("word starts", W)

    # ---- SFX (real Mixkit recordings), tasteful and event-locked ----
    def load(k):
        o = f"{SFX}s{k}_48k.wav"
        subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", f"{SFX}s{k}.mp3", "-ac", "1", "-ar", str(SR), "-c:a", "pcm_f32le", o])
        return wavfile.read(o)[1].astype(np.float32)
    snd = {k: load(k) for k in [1490, 1492, 2356, 2357, 2577, 2573, 2903, 951]}

    def peak_t(v):
        w = int(0.01 * SR); n = len(v) // w
        return float(np.argmax(np.sqrt((v[: n * w].reshape(n, w) ** 2).mean(1))) * 0.01)
    track = np.zeros(int(TOTAL * SR) + SR * 4, np.float32)

    def put(k, at, g, align=False, rev=False):
        v = snd[k][::-1].copy() if rev else snd[k]
        v = v * g
        if align: at -= (len(v) / SR - peak_t(snd[k][::-1].copy())) if rev else peak_t(snd[k])
        i = int(max(at, 0) * SR)
        track[i: i + len(v)] += v[: len(track) - i]

    put(1492, W[0] - 0.12, 0.16, True)
    put(2356, W[3], 0.16)
    put(1490, TL["morph"][0] + 0.1, 0.22, True)
    put(2903, TL["morph"][1], 0.20, True)
    for i in (5, 6, 7, 9): put(2356 if i % 2 else 2357, W[i], 0.22); put(2577, W[i] + 0.1, 0.10)
    put(1490, TL["push"][0] + 0.2, 0.22, True)
    put(2356, W[14], 0.24); put(2357, W[16], 0.22)
    put(1492, TL["phoneIn"][0] + 0.2, 0.20, True)
    for i, t in enumerate(TL["pops"]): put(2357 if i % 2 else 2356, t, 0.20)
    put(1490, TL["together"][0] - 0.05, 0.18, True)
    put(1490, W[27] - 0.05, 0.24, True, rev=True)     # riser into the impact
    put(2903, W[27] + 0.02, 0.42, True)               # TEZLİKLƏ impact
    put(1490, TL["iris"][0] + 0.1, 0.24, True)
    put(1492, TL["curtain"][0] + 0.15, 0.20, True)
    put(951, W[32], 0.20)
    pk = np.max(np.abs(track))
    if pk > 0.95: track /= pk / 0.95
    wavfile.write(WORK + "sfx_v2.wav", SR, track)

    fo = round(TOTAL - 0.9, 2)
    fc = (
        f"[0]aresample=48000,loudnorm=I=-14:TP=-1.5:LRA=7,asplit=2[v1][v2];"
        f"[1]aresample=48000,adelay={int(BEAT_SHIFT*1000)}|{int(BEAT_SHIFT*1000)},apad,atrim=0:{TOTAL},equalizer=f=2500:t=q:w=0.9:g=-3,equalizer=f=400:t=q:w=1:g=-1.5,"
        f"afade=t=in:d=0.4,afade=t=out:st={fo}:d=0.9,loudnorm=I=-19:TP=-3[m];"
        f"[m][v2]sidechaincompress=threshold=0.04:ratio=4:attack=20:release=380:makeup=1[md];"
        f"[2]aresample=48000,atrim=0:{TOTAL}[s];"
        f"[v1][md][s]amix=inputs=3:normalize=0:duration=longest,loudnorm=I=-14.5:TP=-1.5:LRA=9,atrim=0:{TOTAL},aresample=48000[o]"
    )
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", WORK + "voice_v2.wav", "-i", MUSIC, "-i", WORK + "sfx_v2.wav", "-filter_complex", fc, "-map", "[o]", OUT])
    print("wrote", OUT)


if __name__ == "__main__":
    main()
