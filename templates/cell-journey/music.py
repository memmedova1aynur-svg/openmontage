"""Compose a 25 s warm, moving cue from earshot's CC0-derived instrument notes.
100 BPM, C - G - Am - F, one chord per bar (2.4 s); arrangement follows the picture:
  0-3.9 drop: celesta sparkles | 3.9-9.1 vessel: pad + kalimba arpeggio
  9.1-14.1 shield: + harp, brush, hat | 14.1-20 neurons: + kick/snare, 8th arps, glock sparkles
  20-25 heart: resolve to C, bells, ring out.
"""
import subprocess, sys, wave
from pathlib import Path
import numpy as np

import os, shutil
E = os.environ.get("EARSHOT_BIN") or shutil.which("earshot") or str(Path(__file__).resolve().parents[2] / ".venv-earshot/bin/earshot")
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "music.wav")
CACHE = Path("notes"); CACHE.mkdir(exist_ok=True)
SR, DUR = 48000, 25.0
BEAT = 0.6; BAR = 4 * BEAT
mix = np.zeros((int(SR * (DUR + 4)), 2))

def load(sound, pitch=None, seed=1):
    key = f"{sound.replace('/', '_')}_{pitch or 'x'}_{seed}.wav"
    p = CACHE / key
    if not p.exists():
        cmd = [E, "make", "x", "--sound", sound, "-o", str(p), "--seed", str(seed)]
        if pitch: cmd += ["--pitch", pitch]
        subprocess.run(cmd, check=True, capture_output=True)
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(p), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)

def put(t, sound, pitch=None, db=0.0, pan=0.0, seed=1, cut=None):
    a = load(sound, pitch, seed).copy()
    if cut:  # shorten with a 60 ms fade
        n = int(cut * SR); a = a[:n]; f = min(len(a), int(.06 * SR)); a[-f:] *= np.linspace(1, 0, f)[:, None]
    g = 10 ** (db / 20); a *= g
    a[:, 0] *= np.sqrt(1 - max(0, pan)); a[:, 1] *= np.sqrt(1 + min(0, pan))
    i = int(t * SR); j = min(len(mix), i + len(a)); mix[i:j] += a[: j - i]

CHORDS = [("C", ["C4", "E4", "G4", "C5"], "C3"), ("G", ["B3", "D4", "G4", "B4"], "G2"),
          ("Am", ["A3", "C4", "E4", "A4"], "A2"), ("F", ["A3", "C4", "F4", "A4"], "F2")]
nbars = int(np.ceil(DUR / BAR))
for b in range(nbars):
    t0 = b * BAR; name, tones, bass = CHORDS[b % 4]
    final = t0 >= 19.2  # bars 8.. resolve: hold C
    if final: name, tones, bass = CHORDS[0]
    # intro sparkles (drop)
    if t0 < 3.9:
        for k, n in enumerate([tones[3], tones[2], tones[3]]):
            put(t0 + .3 + k * BEAT * 1.33, "note/celesta", n.replace("4", "5").replace("3", "5"), db=-14, pan=(k - 1) * .4, seed=b * 7 + k)
    # pad from the vessel on
    if t0 + BAR > 3.9:
        put(max(t0, 3.9), "pad/warm", tones[0], db=-17, seed=b)
        put(max(t0, 3.9), "pad/warm", tones[2], db=-19, seed=b + 50)
    # kalimba arpeggio: quarters in vessel/shield, eighths in neurons
    if t0 + BAR > 3.9:
        step = BEAT / 2 if 14.1 <= t0 < 19.2 else BEAT
        pat = [0, 1, 2, 3, 2, 1, 2, 3] if step < BEAT else [0, 2, 1, 3]
        for k in range(int(BAR / step)):
            tt = t0 + k * step
            if tt < 3.9 or tt > 24.2 or (final and k > 3): continue
            put(tt, "note/kalimba", tones[pat[k % len(pat)]], db=-12 + (2 if k % 2 == 0 else 0), pan=.25 if k % 2 else -.25, seed=k + b * 10)
    # bass on the one (+ the three in the build)
    if t0 >= 3.9 or t0 + BAR > 4.5:
        put(max(t0, 3.9), "note/round_bass", bass, db=-13, seed=b)
        if 9.1 <= t0 < 19.2: put(t0 + 3 * BEAT, "note/round_bass", bass, db=-15, seed=b + 1)
    # harp from the shield on
    if t0 >= 8.4 and not final:
        put(t0 + BEAT * .5, "note/harp", tones[3], db=-17, pan=-.3, seed=b)
    # drums
    for k in range(8):
        tt = t0 + k * BEAT / 2
        if 9.1 <= tt < 19.2:
            put(tt, "hat/closed", db=-24 if k % 2 else -21, pan=.3, seed=k + b)
        if 14.1 <= tt < 19.2:
            if k in (0, 4): put(tt, "kick/soft", db=-11, seed=k)
            if k in (2, 6): put(tt, "snare/brush", db=-17, seed=k + b)
    # neuron sparkles
    if 14.1 <= t0 < 19.2:
        put(t0 + BEAT * 1.5, "note/glockenspiel", tones[3].replace("4", "6").replace("3", "6"), db=-20, pan=.4, seed=b)
# heart: resolution
put(19.2, "crash/bright", db=-26, seed=3)
put(19.2, "note/hand_bell", "C5", db=-14, seed=2)
put(21.6, "note/celesta", "E6", db=-18, pan=-.3, seed=4)
put(22.2, "note/celesta", "G6", db=-19, pan=.3, seed=5)
put(22.9, "note/hand_bell", "G4", db=-16, seed=6)
put(22.9, "kick/soft", db=-14, seed=9); put(23.25, "kick/soft", db=-17, seed=10)  # heartbeat with the picture
put(24.1, "kick/soft", db=-15, seed=11)

y = mix[: int(SR * DUR)]
fade = int(1.2 * SR); y[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 1.5
fi = int(.08 * SR); y[:fi] *= np.linspace(0, 1, fi)[:, None]
y = np.tanh(y * 1.1) / 1.1  # gentle soft-clip safety
pk = np.max(np.abs(y)); y = y / pk * .7 if pk > 0 else y
with wave.open(str(OUT), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((y * 32767).astype("<i2").tobytes())
print("wrote", OUT, f"{len(y)/SR:.1f}s")
