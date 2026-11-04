"""Premium səs effektləri (tonal, küysüz) — <MONTAJ_DATA_DIR>/sfx/p_*.wav. Yoxdursa yaradır."""
import os, wave
from pathlib import Path
import numpy as np
SR = 48000
LIB = Path(os.environ.get("MONTAJ_DATA_DIR", "/root/montaj-data")) / "sfx"


def _save(n, x):
    x = x / np.max(np.abs(x)) * 0.89
    d = (np.stack([x, x], 1) * 32767).astype(np.int16)
    with wave.open(str(LIB / f"{n}.wav"), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(d.tobytes())


def _lp(x, c):
    a = np.exp(-2 * np.pi * c / SR); y = np.zeros_like(x); p = 0.0
    for i, v in enumerate(x): p = (1 - a) * v + a * p; y[i] = p
    return y


def ensure():
    LIB.mkdir(parents=True, exist_ok=True)
    if all((LIB / f"p_{k}.wav").exists() for k in ("sub", "bloom", "swell", "rise", "glint", "tap")): return
    t_ = lambda d: np.arange(int(SR * d)) / SR
    env = lambda t, a, dec: np.minimum(1, t / a) * np.exp(-t / dec)
    t = t_(0.7); f = 55 + 70 * np.exp(-t / 0.06); ph = 2 * np.pi * np.cumsum(f) / SR
    _save("p_sub", np.sin(ph) * env(t, 0.004, 0.18) + 0.25 * np.sin(2 * ph) * env(t, 0.004, 0.08))
    t = t_(1.6); x = sum(a * np.sin(2 * np.pi * f * t) + 0.3 * a * np.sin(4 * np.pi * f * t) for f, a in ((261.6, 1), (329.6, .8), (392, .7), (523.3, .5)))
    _save("p_bloom", _lp(x * env(t, 0.12, 0.55), 2500))
    t = t_(0.42); u = t / t[-1]; f = 380 + 520 * u ** 1.6; ph = 2 * np.pi * np.cumsum(f) / SR
    _save("p_swell", _lp((np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.2 * np.sin(3.01 * ph)) * np.sin(np.pi * u) ** 2, 3000))
    t = t_(0.9); u = t / t[-1]; f = 220 + 440 * u ** 2; ph = 2 * np.pi * np.cumsum(f) / SR
    _save("p_rise", _lp((np.sin(ph) + 0.5 * np.sin(1.5 * ph)) * u ** 2 * (1 - np.exp(-(1 - u) * 40)), 2600))
    t = t_(0.6)
    _save("p_glint", _lp(np.sin(2 * np.pi * 1318.5 * t) * env(t, 0.003, 0.16) + 0.5 * np.sin(2 * np.pi * 1975.5 * t) * env(t, 0.003, 0.09)
                         + 0.25 * np.sin(2 * np.pi * 2637 * t) * env(t, 0.002, 0.05), 5000))
    t = t_(0.12)
    _save("p_tap", _lp(np.sin(2 * np.pi * 880 * t) * env(t, 0.001, 0.018) + 0.4 * np.sin(2 * np.pi * 1760 * t) * env(t, 0.001, 0.01), 4000))


if __name__ == "__main__":
    ensure(); print("premium sfx:", LIB)
