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


# ---- "pro" dəsti: küy əsaslı, tonsuz (melodik "uyu" səsləri yoxdur) — Xəyyam üçün standart ----
def _bp(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0; return np.fft.irfft(X, len(x))


def _save2(n, l, r, peak=0.89):
    m = max(np.max(np.abs(l)), np.max(np.abs(r))); l, r = l / m * peak, r / m * peak
    d = (np.stack([l, r], 1) * 32767).astype(np.int16)
    with wave.open(str(LIB / f"{n}.wav"), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(d.tobytes())


def _sweep_noise(dur, f0, f1, seed, att=0.45):
    rng = np.random.default_rng(seed); n = int(SR * dur); t = np.arange(n) / SR; u = t / dur
    out = np.zeros(n); seg = 1024
    src = rng.normal(0, 1, n + seg)
    for i in range(0, n, seg // 2):  # zamanla dəyişən zolaq (whoosh)
        c = f0 * (f1 / f0) ** (i / n); blk = src[i:i + seg] * np.hanning(seg)
        y = _bp(blk, c * 0.55, c * 1.8); j = min(seg, n - i); out[i:i + j] += y[:j]
    env = np.sin(np.pi * np.clip(u / att, 0, 1) / 2) ** 2 * np.clip((1 - u) / (1 - att), 0, 1) ** 1.6
    return out * env, u


def ensure_pro():
    LIB.mkdir(parents=True, exist_ok=True)
    if all((LIB / f"pro_{k}.wav").exists() for k in ("whoosh", "air", "click", "thump", "paper")): return
    x, u = _sweep_noise(0.38, 500, 2600, 1); pan = 0.5 + 0.35 * (u - 0.5)
    _save2("pro_whoosh", x * (1 - pan) * 2, x * pan * 2, 0.7)
    x, u = _sweep_noise(0.7, 300, 1600, 2, 0.6); pan = 0.5 - 0.3 * (u - 0.5)
    _save2("pro_air", x * (1 - pan) * 2, x * pan * 2, 0.6)
    rng = np.random.default_rng(3); t = np.arange(int(SR * 0.25)) / SR
    c = _bp(rng.normal(0, 1, len(t)), 1800, 7000) * np.exp(-t / 0.004) + 0.5 * np.sin(2 * np.pi * 2100 * t) * np.exp(-t / 0.006)
    _save2("pro_click", c, c, 0.6)
    t = np.arange(int(SR * 0.32)) / SR
    th = np.sin(2 * np.pi * 62 * t) * np.exp(-t / 0.07) * np.minimum(1, t / 0.003) + 0.35 * _bp(rng.normal(0, 1, len(t)), 80, 900) * np.exp(-t / 0.02)
    _save2("pro_thump", th, th, 0.8)
    t = np.arange(int(SR * 0.3)) / SR; u = t / t[-1]
    pp = _bp(rng.normal(0, 1, len(t)), 2000, 9000) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 38 * t))) * np.sin(np.pi * u) ** 1.5
    _save2("pro_paper", pp, pp * 0.9, 0.5)
