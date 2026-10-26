"""Synthesise the SFX kit for 'Göy niyə mavidir' offline (no SFX provider key needed).

whoosh  — band-passed noise sweep with a fast swell (transitions, punch-ins)
pop     — short pitched blip with a soft click (text / element entrances)
tick    — tiny high click (list items, molecules)
riser   — rising noise + tone, 1.6 s (into reveals)
hit     — low sub thump with a noise transient (payoff lines)
shimmer — airy high chime (light / spectrum moments)
amb_space, amb_mars_wind, amb_air — low ambience beds per world

Usage: python make_sfx.py   -> ../assets/sfx/*.wav (48 kHz mono)
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 48000
OUT = Path(__file__).resolve().parent.parent / "assets" / "sfx"
rng = np.random.default_rng(7)


def t_axis(sec):
    return np.arange(int(SR * sec)) / SR


def onepole_lp(x, fc):
    """Time-varying one-pole low-pass; fc may be an array (Hz)."""
    fc = np.broadcast_to(np.asarray(fc, float), x.shape)
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    return y


def bandpass(x, lo, hi):
    return onepole_lp(x, hi) - onepole_lp(x, lo)


def env_ad(n, attack, decay_pow=2.0):
    a = int(n * attack)
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a) ** 2
    e[a:] = np.linspace(1, 0, n - a) ** decay_pow
    return e


def norm(x, peak_db=-3.0):
    return x / (np.abs(x).max() + 1e-9) * 10 ** (peak_db / 20)


def fade(x, ms_in=3, ms_out=20):
    i, o = int(SR * ms_in / 1000), int(SR * ms_out / 1000)
    x = x.copy()
    x[:i] *= np.linspace(0, 1, i)
    x[-o:] *= np.linspace(1, 0, o)
    return x


def whoosh(sec=0.7):
    t = t_axis(sec)
    n = rng.standard_normal(len(t))
    u = t / sec
    centre = 300 + 3200 * np.sin(np.pi * u) ** 1.5
    x = bandpass(n, centre * 0.5, centre * 1.6)
    return norm(x * env_ad(len(t), 0.55, 1.6), -4)


def pop(freq=620, sec=0.12):
    t = t_axis(sec)
    f = freq * (1 + 0.6 * np.exp(-t * 60))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38)
    click = rng.standard_normal(len(t)) * np.exp(-t * 900) * 0.3
    return norm(tone + click, -6)


def tick(sec=0.05):
    t = t_axis(sec)
    x = np.sin(2 * np.pi * 2600 * t) * np.exp(-t * 160) + rng.standard_normal(len(t)) * np.exp(-t * 1500) * 0.4
    return norm(x, -9)


def riser(sec=1.6):
    t = t_axis(sec)
    u = t / sec
    n = bandpass(rng.standard_normal(len(t)), 400 + 2500 * u, 1500 + 8000 * u)
    f = 180 * 2 ** (2.2 * u)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35
    x = (n + tone) * u ** 2.2
    x[-int(SR * 0.03):] *= np.linspace(1, 0, int(SR * 0.03))
    return norm(x, -5)


def hit(sec=1.4):
    t = t_axis(sec)
    f = 55 + 70 * np.exp(-t * 18)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    trans = onepole_lp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 40) * 0.8
    return norm(np.tanh(1.6 * (sub + trans)), -3)


def shimmer(sec=1.6):
    t = t_axis(sec)
    x = sum(np.sin(2 * np.pi * f * t + p) / (k + 1) for k, (f, p) in
            enumerate([(1760, 0), (2637, 1), (3520, 2), (5274, 0.5)]))
    x = x * env_ad(len(t), 0.04, 2.5) * (1 + 0.3 * np.sin(2 * np.pi * 7 * t))
    return norm(x, -10)


def ambience(sec, lo, hi, wobble=0.15, seed=0):
    r = np.random.default_rng(seed)
    t = t_axis(sec)
    n = bandpass(r.standard_normal(len(t)), lo, hi)
    lfo = 1 + wobble * np.sin(2 * np.pi * 0.13 * t) + wobble * 0.6 * np.sin(2 * np.pi * 0.31 * t + 1)
    return norm(n * lfo, -18)


def write(name, x):
    OUT.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(fade(x), -1, 1) * 32767).astype(np.int16)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("wrote", OUT / f"{name}.wav")


if __name__ == "__main__":
    write("whoosh", whoosh())
    write("whoosh_short", whoosh(0.4))
    write("pop", pop())
    write("pop_low", pop(380))
    write("tick", tick())
    write("riser", riser())
    write("hit", hit())
    write("shimmer", shimmer())
    write("amb_space", ambience(6.5, 40, 300, 0.2, 1))
    write("amb_mars_wind", ambience(6.5, 150, 1400, 0.45, 2))
    write("amb_air", ambience(6.5, 200, 2500, 0.25, 3))
