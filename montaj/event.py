"""M09 — tədbir, seminar icmalı və kameraarxası montajı: görüntülər musiqi ritmi ilə (VIDEO_TYPES növ 5, 7).

* Musiqinin vuruşları (beat) yerli tapılır (numpy, əlavə kitabxana yoxdur): spektral axın → temp → vuruş şəbəkəsi.
* Kadrlar (shot) avtomatik bölünür və qiymətləndirilir: kəskinlik, işıq, titrəmə, üz; zəif kadr seçilmir.
* Quruluş: açılış (ümumi plan, məkan) → inkişaf (insanlar, fəaliyyət, xronoloji) → final (sonuncu anlar, uzun kadr).
  Kəsimlər vuruşlara düşür. Yavaşlatma: material ≥50 fps olanda final kadr 0.5x (real kadrlar, slowmo.py); 30 fps-də yoxdur.
* Seçim təklifdir: Claude variant şəklinə baxıb yoxlayır; real səs (alqış, gülüş) namizədləri `_review`-da.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np

SR = 22050
HOP = 512


# ---------------------------------------------------------------------------
# Musiqi vuruşları
# ---------------------------------------------------------------------------

def _decode(path: Path, sr: int = SR) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def onset_envelope(y: np.ndarray, n_fft: int = 2048, hop: int = HOP) -> np.ndarray:
    if len(y) < n_fft:
        return np.zeros(1)
    n = 1 + (len(y) - n_fft) // hop
    idx = np.arange(n_fft)[None, :] + hop * np.arange(n)[:, None]
    spec = np.abs(np.fft.rfft(y[idx] * np.hanning(n_fft)[None, :], axis=1))
    logs = np.log1p(1000 * spec)
    flux = np.maximum(0, np.diff(logs, axis=0)).sum(axis=1)
    flux = np.concatenate([[0], flux])
    flux -= np.convolve(flux, np.ones(16) / 16, mode="same")  # yerli orta çıxılır
    flux = np.maximum(flux, 0)
    return flux / (flux.max() or 1)


def beats(path: Path, bpm_range: tuple[float, float] = (70, 180)) -> dict[str, Any]:
    """{"tempo": bpm, "beats": [s...], "duration": s}. Temp avtokorrelyasiya ilə (120 ətrafına üstünlük), faza ən güclü düzülüşlə."""
    y = _decode(Path(path))
    dur = len(y) / SR
    env = onset_envelope(y)
    fps = SR / HOP
    if env.size < fps * 4 or env.max() == 0:
        return {"tempo": 0.0, "beats": [], "duration": round(dur, 3)}
    ac = np.correlate(env, env, mode="full")[env.size - 1:]
    lags = np.arange(len(ac))
    lo, hi = int(fps * 60 / bpm_range[1]), int(fps * 60 / bpm_range[0])
    cand = lags[lo:hi + 1]
    bpm = 60 * fps / np.maximum(cand, 1)
    weight = np.exp(-0.5 * (np.log2(bpm / 120) / 0.9) ** 2)
    period = int(cand[np.argmax(ac[lo:hi + 1] * weight)])
    # dəqiq period (kəsr): avtokorrelyasiya zirvəsinin parabola ilə incələşdirilməsi
    if 1 <= period < len(ac) - 1:
        a, b, c = ac[period - 1], ac[period], ac[period + 1]
        den = a - 2 * b + c
        per = period + (0.5 * (a - c) / den if den else 0)
    else:
        per = float(period)
    best, phase = -1.0, 0.0
    for off in np.linspace(0, per, int(per) * 2, endpoint=False):
        pos = np.arange(off, env.size, per).astype(int)
        sc = env[pos].sum()
        if sc > best:
            best, phase = sc, off
    out, t = [], phase
    w = max(1, int(per * 0.1))
    while t < env.size:
        i = int(round(t))
        a0, a1 = max(0, i - w), min(env.size, i + w + 1)
        j = a0 + int(np.argmax(env[a0:a1])) if env[a0:a1].max() > 0.3 else i  # aydın zərbə yaxındadırsa ona çək
        out.append(round(j / fps, 3))
        t += per
    out = [x + 1024 / SR for x in out]  # STFT pəncərəsinin mərkəzi
    out = [round(_refine(y, x), 3) for x in out if x < dur - 0.05]  # zərbənin dəqiq başlanğıcı (5 ms)
    return {"tempo": round(60 * fps / per, 1), "beats": out, "duration": round(dur, 3)}


def _refine(y: np.ndarray, t: float, win: float = 0.07) -> float:
    """±70 ms içində qısa (5 ms) enerjinin ən kəskin artdığı an — görüntü kəsimi zərbə ilə eyni kadrda olsun."""
    h = int(0.005 * SR)
    a, b = max(0, int((t - win) * SR)), min(len(y), int((t + win) * SR))
    seg = y[a:b]
    n = len(seg) // h
    if n < 4:
        return t
    e = np.log1p(1e4 * (seg[: n * h].reshape(n, h) ** 2).mean(axis=1))
    d = np.diff(e)
    i = int(np.argmax(d))
    return (a + (i + 1) * h) / SR if d[i] > 0.5 else t


# ---------------------------------------------------------------------------
# Kadrlar
# ---------------------------------------------------------------------------

def _gray(rgb: np.ndarray) -> np.ndarray:
    return rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114


def _sharp(g: np.ndarray) -> float:
    """Kəskinlik 0..1 (Crété-Roffet "blur effect" əksinə): şəkil yenidən bulandırılanda nə qədər detal itirir.
    Düz rəngli səthlər bulanıq sayılmır (laplasian dispersiyasından fərqli)."""
    out = 1.0
    for ax in (0, 1):
        k = 9
        pad = [(0, 0), (0, 0)]
        pad[ax] = (k // 2, k // 2)
        gp = np.pad(g, pad, mode="edge")
        cs = np.cumsum(gp, axis=ax)
        cs = np.concatenate([np.zeros_like(np.take(cs, [0], axis=ax)), cs], axis=ax)
        b = (np.take(cs, range(k, cs.shape[ax]), axis=ax) - np.take(cs, range(0, cs.shape[ax] - k), axis=ax)) / k
        df, db = np.abs(np.diff(g, axis=ax)), np.abs(np.diff(b, axis=ax))
        sf = df.sum()
        if sf <= 1e-6:
            continue
        sv = np.maximum(0, df - db).sum()
        out = min(out, sv / sf)  # 1 − blur
    return float(out)


def creation_order(m: dict[str, Any], src: Path) -> str:
    """Xronologiya: faylın çəkiliş vaxtı (metadata), yoxdursa adı."""
    try:
        tags = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format_tags=creation_time", "-of", "json", str(src)],
                                         capture_output=True, text=True, check=True).stdout).get("format", {}).get("tags", {})
        if tags.get("creation_time"):
            return tags["creation_time"] + "|" + m["name"]
    except Exception:
        pass
    return "~|" + m["name"]


def scan_shots(media: list[dict[str, Any]], root: Path, step: float = 0.5, faces: bool = True) -> list[dict[str, Any]]:
    """Bütün görüntü mediaları üzrə kadrlar (xronoloji): vaxt, kəskinlik, işıq, titrəmə, üz, səs; kadr daxili seriya (ən yaxşı pəncərə üçün)."""
    from montaj import reframe

    shots: list[dict[str, Any]] = []
    vids = [m for m in media if m.get("hasVideo") and not (m.get("source") or {}).get("type") in ("generated", "music", "sfx")]
    vids.sort(key=lambda m: creation_order(m, root / m["file"]))
    for order, m in enumerate(vids):
        src = root / m["file"]
        if m.get("isImage"):
            from PIL import Image

            g = _gray(np.asarray(Image.open(src).convert("RGB").resize((320, 320)), dtype=float))
            shots.append({"media": m["id"], "name": m["name"], "order": order, "s": 0.0, "e": 3.0, "image": True,
                          "sharp": _sharp(g), "bright": float(g.mean()), "shake": 0.0, "faces": 0, "face": 0.0, "loud": -90.0,
                          "series": [[0.0, _sharp(g), 0.0]]})
            continue
        dur = float(m.get("duration") or 0)
        frames = list(reframe.sample_frames(src, 0, dur, step, width=320))
        if not frames:
            continue
        ts, gs = [t for t, _ in frames], [_gray(f.astype(float)) for _, f in frames]
        sharp = [_sharp(g) for g in gs]
        diff = [0.0] + [float(np.abs(gs[i] - gs[i - 1]).mean()) for i in range(1, len(gs))]
        med = float(np.median(diff[1:])) if len(diff) > 2 else 0.0
        cuts = [0] + [i for i in range(1, len(diff)) if diff[i] > max(28.0, 3.5 * med)] + [len(gs)]
        loud = _loudness(src, dur) if m.get("hasAudio") else None
        for a, b in zip(cuts, cuts[1:]):
            s, e = ts[a], min(dur, ts[b - 1] + step)
            if e - s < 0.8:
                continue
            seg = range(a, b)
            mot = [diff[i] for i in seg if i > a]
            sh = {"media": m["id"], "name": m["name"], "order": order, "s": round(s, 2), "e": round(e, 2),
                  "sharp": float(np.median([sharp[i] for i in seg])), "bright": float(np.mean([gs[i].mean() for i in seg])),
                  "shake": float(np.median(mot)) if mot else 0.0, "faces": 0, "face": 0.0,
                  "loud": float(np.mean(loud[int(s):max(int(s) + 1, int(e))])) if loud is not None and len(loud) else -90.0,
                  "series": [[round(ts[i], 2), round(sharp[i], 3), round(diff[i] if i > a else 0.0, 2)] for i in seg]}
            if faces:
                det = reframe.detect_faces(src, s, e, step=max(1.0, (e - s) / 3))
                fs = [f for d in det for f in d["faces"]]
                sh["faces"] = round(len(fs) / max(1, len(det)), 1)
                sh["face"] = round(max((f["w"] * f["h"] for f in fs), default=0.0), 4)
            shots.append(sh)
    _score(shots)
    return shots


def _loudness(src: Path, dur: float) -> np.ndarray:
    y = _decode(src, 8000)
    n = int(len(y) // 8000)
    if n == 0:
        return np.zeros(0)
    r = np.sqrt((y[: n * 8000].reshape(n, 8000) ** 2).mean(axis=1) + 1e-12)
    return 20 * np.log10(r)


def _score(shots: list[dict[str, Any]]) -> None:
    if not shots:
        return
    for s in shots:
        why = []
        q = max(0.0, min(1.0, (s["sharp"] - 0.25) / 0.4))  # ≈0.65+ kəskin, ≤0.4 bulanıq
        if s["sharp"] < 0.4:
            why.append("bulanıq")
        b = s["bright"]
        expo = 1.0 if 60 <= b <= 200 else 0.5 if 35 <= b <= 225 else 0.0
        if expo < 1:
            why.append("qaranlıq" if b < 60 else "çox açıq")
        shake = s["shake"]
        stab = 1.0 if shake < 6 else 0.6 if shake < 14 else 0.2
        if stab < 0.6:
            why.append("titrəyir/sürətli hərəkət")
        s["score"] = round(1.4 * q + expo + stab + (0.3 if s["faces"] else 0.0), 3)
        s["weak"] = why
        s["wide"] = (not s["faces"]) or s["face"] < 0.02  # ümumi plan (məkan/zal) — açılış üçün


def best_window(shot: dict[str, Any], length: float, avoid: list[tuple[float, float]] | None = None) -> float | None:
    """Kadr daxilində `length` uzunluğunda ən kəskin və sakit pəncərənin başlanğıcı (kadr qısadırsa və ya
    artıq işlənmiş hissələrlə (avoid) üst-üstə düşməyən yer yoxdursa None)."""
    s, e = shot["s"], shot["e"]
    if shot.get("image"):
        return None if avoid else 0.0
    if e - s < length - 0.02:
        return None
    ser = shot["series"]
    best, at = -1e9, None
    starts = sorted({x[0] for x in ser} | {round(e - length, 3)})
    for t0 in starts:
        if t0 < s - 1e-6 or t0 + length > e + 1e-6:
            continue
        if any(t0 < b - 0.05 and t0 + length > a + 0.05 for a, b in avoid or []):
            continue
        win = [x for x in ser if t0 <= x[0] < t0 + length] or ser[:1]
        sc = 100 * float(np.mean([x[1] for x in win])) - float(np.mean([x[2] for x in win]))
        if sc > best:
            best, at = sc, t0
    return None if at is None else round(min(at, e - length), 3)


# ---------------------------------------------------------------------------
# Yığım (variantlar)
# ---------------------------------------------------------------------------

VARIANTS = {
    "A": {"title": "Xronoloji: açılış → inkişaf → final", "unit": 4, "target": 30.0},
    "B": {"title": "Ritmik: musiqi vuruşuna kəsim", "unit": 2, "target": 30.0},
    "C": {"title": "Qısa dəvət (15–20 s)", "unit": 2, "target": 17.0},
}


def _slots(bt: list[float], start_i: int, unit: int, target: float, music_end: float) -> list[tuple[float, float]]:
    """Vuruş şəbəkəsindən kadr yerləri (musiqi vaxtı ilə): açılış 1 uzun yer, final 1 uzun yer."""
    out, i = [], start_i
    t0 = bt[start_i]
    while i + unit < len(bt) and bt[i] - t0 < target - 1e-6:
        u = unit * 2 if not out else unit  # açılış kadrı iki dəfə uzun (məkanla tanışlıq)
        j = min(i + u, len(bt) - 1)
        out.append((bt[i], bt[j]))
        i = j
    if not out:
        return [(t0, min(music_end, t0 + target))]
    if len(out) >= 3:  # final: son iki yer birləşir (uzun son kadr)
        a, _ = out[-2]
        out[-2:] = [(a, out[-1][1])]
    return out


def assemble(shots: list[dict[str, Any]], bt: dict[str, Any], variant: str = "A", target: float | None = None) -> dict[str, Any]:
    """Kadrları vuruş yerlərinə düzür. Nəticə: {"cards", "music_from", "dur", "review"}; kartlar storyboard formatında."""
    v = VARIANTS[variant]
    unit = v["unit"] * (2 if bt["tempo"] > 140 else 1)
    target = target or v["target"]
    beats_ = bt["beats"]
    review: list[str] = []
    if len(beats_) < 4:
        raise ValueError("musiqidə vuruş tapılmadı (çox sakit/ritmsiz) — başqa musiqi seç")
    start_i = 1 if beats_[0] < 0.3 and len(beats_) > 5 else 0
    good = [s for s in shots if not s["weak"]] or sorted(shots, key=lambda s: -s["score"])[: max(3, len(shots) // 2)]
    if len(good) < len(shots):
        review.append(f"{len(shots) - len(good)} zəif kadr seçilmədi (bulanıq/qaranlıq/titrək)")
    slots = _slots(beats_, start_i, unit, target, bt["duration"])
    while len(slots) > max(4, 3 * len(good)) and unit < 16:  # material azdırsa kəsim seyrəlir (eyni kadr təkrarlanmasın)
        unit *= 2
        slots = _slots(beats_, start_i, unit, target, bt["duration"])
    music_from = slots[0][0]
    chrono = sorted(good, key=lambda s: (s["order"], s["s"]))
    n = len(slots)
    cards, uses, prev = [], {}, None

    def win(s_, length):
        return best_window(s_, length, uses.get(id(s_)))
    queue = list(enumerate(slots))
    while queue:
        k, (a, b) = queue.pop(0)
        length = round(b - a, 3)
        lo, hi = int(len(chrono) * k / n), max(int(len(chrono) * (k + 1) / n), int(len(chrono) * k / n) + 1)
        pool = chrono[lo:hi]
        if k == 0:
            pool = sorted(chrono[: max(1, len(chrono) // 3)], key=lambda s: (not s["wide"], -s["score"]))  # açılış: ümumi plan
        elif k == n - 1:
            pool = sorted(chrono[-max(1, len(chrono) // 3):], key=lambda s: -s["score"])  # final: sonuncu anlar
        cand = [s for s in pool if id(s) not in uses and win(s, length) is not None and s is not prev] or \
               [s for s in chrono if id(s) not in uses and win(s, length) is not None and s is not prev] or \
               [s for s in chrono if win(s, length) is not None and s is not prev]
        if not cand:
            inner = [x for x in beats_ if a + 0.2 < x < b - 0.2]
            if inner:  # uzun kadr yoxdur: yer vuruşda iki kadra bölünür (ritm qorunur)
                m_ = inner[len(inner) // 2]
                queue[:0] = [(k, (a, m_)), (k, (m_, b))]
                continue
            review.append(f"yer {k + 1} ({length:.1f} s) üçün uyğun kadr yoxdur — atlandı (musiqi qısalır)")
            continue
        sh = max(cand, key=lambda s: s["score"] + (0.4 if k == 0 and s["wide"] else 0) - 0.8 * len(uses.get(id(s), [])))
        t0 = win(sh, length)
        uses.setdefault(id(sh), []).append((t0, t0 + length))
        prev = sh
        cards.append({"id": f"e{k + 1}", "mediaId": sh["media"], "srcIn": round(t0, 3), "srcOut": round(t0 + length, 3),
                      "include": True, "words": [], "role": "açılış" if k == 0 else "final" if k == n - 1 else "inkişaf"})
    rep = sum(1 for v_ in uses.values() if len(v_) > 1)
    if rep:
        review.append(f"{rep} kadrın müxtəlif hissələri bir neçə dəfə işlənib (material azdır)")
    dur = round(sum(c["srcOut"] - c["srcIn"] for c in cards), 3)
    med = float(np.median([s["loud"] for s in good])) if good else -90.0
    loud = sorted([s for s in good if s["loud"] > max(-35.0, med + 6)], key=lambda s: -s["loud"])[:3]  # ümumi fondan yüksək
    if loud:
        review.append("real səs namizədləri (alqış/gülüş ola bilər — dinlə, istəsən liveSound.keep): "
                      + ", ".join(f"{s['name']} {s['s']:.1f}–{s['e']:.1f} s" for s in loud))
    return {"cards": cards, "music_from": round(music_from, 3), "dur": dur, "tempo": bt["tempo"], "review": list(dict.fromkeys(review))}
