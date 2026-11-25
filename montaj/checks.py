"""Render-dən ƏVVƏL 4 avtomatik yoxlama (tam render xərci olmadan): kəsim sərhədləri, səs boğuqluğu, kadraj, rəng.

Hər yoxlama {"name", "status": "ok|warn|bad|fixed|skip", "msg", "items": [...]} qaytarır. `preflight.run` onları işlədir; "fixed" — avtomatik düzəldilən.
Səbəb (istifadəçi şikayətləri): sözlər yarıda qalır; arxa səs kəsiləndə danışanın səsi boğuq çıxır; kadr ortalanmır; rəng çaları.
Hədlər aşağıdakı sabitlərdədir və testlə qorunur.
"""

from __future__ import annotations

import colorsys
import subprocess
from pathlib import Path
from typing import Any

import numpy as np

CUT_INSIDE_TOL = 0.02       # söz sərhədindən bu qədər içəridə kəsim = söz yarımçıq
CUT_EDGE_MARGIN = 0.03      # kəsim söz sonundan/başından bu qədər yaxın = son heca / söz başı riski
HF_DROP_WARN, HF_DROP_BAD = -2.0, -3.5   # danışıqda 2–8 kHz/100–2000 Hz nisbətinin azalması (dB): boğuqluq
CENTER_TOL = 0.04           # üzün mərkəzdən sapması (kadr enin payı)
HEAD_TOP = (0.04, 0.40)     # baş üstü boşluq (kadr hündürlüyünün payı)
MIN_FACE_H = 0.09           # üz kadrın ən azı bu qədəri (uzaqdan çəkilmə)
SKIN_HUE = (0.015, 0.125)   # dəri tonu (HSV hue 0..1): <0.015 qırmızılıq, >0.125 sarılıq
SKIN_SAT = (0.10, 0.72)     # <0.10 solğunluq, >0.72 həddindən artıq doyma
LUMA_JUMP = 0.12            # klipler arası orta parlaqlıq fərqi
ADJUST_LIMITS = {"sharpen": (0.0, 0.30), "contrast": (0.94, 1.06), "saturation": (1.0, 1.0), "vibrance": (0.0, 0.06), "brightness": (-0.07, 0.07), "tint": (-0.03, 0.03)}


def _res(name: str, status: str, msg: str, items: list[str] | None = None) -> dict[str, Any]:
    return {"name": name, "status": status, "msg": msg, "items": items or []}


# ---------- 1. kəsim sərhədləri ----------
def cut_boundaries(project: dict[str, Any], analyses: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Real kəsim yerlərində (davamlı olmayan sərhədlər) heç bir söz yarımçıq deyil: söz vaxtları (Whisper) ilə."""
    from montaj.render import _continuous, render_plan

    pl = render_plan(project)
    vids = [v for v in pl["video"] if not v["clip"].get("broll")]
    bad: list[str] = []
    warn: list[str] = []

    def words(mid: str) -> list[dict[str, Any]]:
        return (analyses.get(mid) or {}).get("words") or []

    def check_out(clip: dict[str, Any], t_tl: float) -> None:
        t = float(clip["srcOut"])
        for w in words(clip.get("media")):
            if w["s"] + CUT_INSIDE_TOL < t < w["e"] - CUT_INSIDE_TOL:
                bad.append(f"{t_tl:.2f} s: “{w['w']}” sözü yarımçıq kəsilir (kəsim sözün ortasındadır)")
            elif w["e"] - CUT_INSIDE_TOL <= t < w["e"] + CUT_EDGE_MARGIN:
                warn.append(f"{t_tl:.2f} s: “{w['w']}” sözünün son hecası riskdədir (kəsim sözün sonundan {max(0, int((t - w['e']) * 1000))} ms sonradır)")

    def check_in(clip: dict[str, Any], t_tl: float) -> None:
        t = float(clip["srcIn"])
        for w in words(clip.get("media")):
            if w["s"] + CUT_INSIDE_TOL < t < w["e"] - CUT_INSIDE_TOL:
                bad.append(f"{t_tl:.2f} s: “{w['w']}” sözü başdan yarımçıq başlayır")
            elif w["s"] - CUT_EDGE_MARGIN < t <= w["s"] + CUT_INSIDE_TOL:
                warn.append(f"{t_tl:.2f} s: “{w['w']}” sözünün başı riskdədir (kəsim söz başından {max(0, int((w['s'] - t) * 1000))} ms əvvəldədir)")

    if not vids:
        return _res("kəsim sərhədləri", "skip", "video klip yoxdur")
    check_in(vids[0]["clip"], 0.0)
    cuts = 0
    for a, b in zip(vids, vids[1:]):
        if _continuous(a["clip"], b["clip"]):
            continue
        cuts += 1
        t_tl = a["start"] + a["dur"]
        check_out(a["clip"], t_tl)
        check_in(b["clip"], t_tl)
    check_out(vids[-1]["clip"], vids[-1]["start"] + vids[-1]["dur"])
    if bad:
        return _res("kəsim sərhədləri", "bad", f"{len(bad)} söz yarımçıq kəsilir ({cuts} kəsim yoxlandı) — `cut`/`edit` ilə sərhədi genişləndir", bad + warn)
    if warn:
        return _res("kəsim sərhədləri", "warn", f"{len(warn)} sərhəd riskli ({cuts} kəsim yoxlandı)", warn)
    return _res("kəsim sərhədləri", "ok", f"{cuts} kəsim, heç bir söz yarımçıq deyil")


# ---------- 2. səs boğuqluğu (voice-clean) ----------
def _read(path: Path, ss: float, t: float, sr: int = 16000) -> np.ndarray:
    out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{ss:.3f}", "-t", f"{t:.3f}", "-i", str(path), "-map", "0:a:0", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True)
    return np.frombuffer(out.stdout, dtype=np.float32)


def band_ratio_db(x: np.ndarray, frames: np.ndarray | None = None, sr: int = 16000) -> tuple[float, np.ndarray]:
    """Danışıq kadrlarında (ən güclü 30%) yüksək (2–7.5 kHz) / aşağı (100–2000 Hz) enerji nisbəti, dB. Qayıdır (nisbət, istifadə olunan kadr indeksləri)."""
    n = 1024
    if len(x) < n * 4:
        return 0.0, np.array([], dtype=int)
    hop = 512
    idx = np.arange(0, len(x) - n, hop)
    win = np.hanning(n)
    spec = np.abs(np.fft.rfft(np.stack([x[i:i + n] * win for i in idx]), axis=1)) ** 2
    f = np.fft.rfftfreq(n, 1 / sr)
    lo, hi = spec[:, (f >= 100) & (f < 2000)].sum(axis=1), spec[:, (f >= 2000) & (f < 7500)].sum(axis=1)
    if frames is None:
        tot = lo + hi
        frames = np.where(tot >= np.quantile(tot, 0.7))[0]
    return float(10 * np.log10((hi[frames].sum() + 1e-12) / (lo[frames].sum() + 1e-12))), frames


def voice_integrity(project: dict[str, Any], root: Path, max_seconds: float = 40.0) -> tuple[dict[str, Any], dict[str, Any]]:
    """Təmizlənmiş danışıq (voice-clean) orijinala nisbətən boğuqdurmu: 2–8 kHz/100–2000 Hz nisbətinin azalması. Qayıdır (nəticə, düzəldilmiş layihə)."""
    vc = project.get("voiceClean") or {}
    if not vc:
        return _res("danışıq səsi", "skip", "arxa səs təmizləmə tətbiq olunmayıb (orijinal səs işlənir)"), project
    media = {m["id"]: m for m in project["media"]}
    items, worst = [], 0.0
    fixed = dict(vc)
    for mid, rec in vc.items():
        m = media.get(mid)
        if not m or not rec.get("file") or not (root / rec["file"]).is_file():
            continue
        spans = [(float(c["srcIn"]), float(c["srcOut"])) for c in project["clips"] if c.get("media") == mid and c["track"] == "a1"]
        ss = min((a for a, _ in spans), default=0.0)
        dur = min(max_seconds, max((b for _, b in spans), default=ss + max_seconds) - ss)
        a, b = _read(root / m["file"], ss, dur), _read(root / rec["file"], ss, dur)
        n = min(len(a), len(b))
        r0, fr = band_ratio_db(a[:n])
        r1, _ = band_ratio_db(b[:n], fr)
        delta = r1 - r0
        worst = min(worst, delta)
        items.append(f"{m.get('name') or mid}: 2–8 kHz nisbəti {r0:.1f} → {r1:.1f} dB ({delta:+.1f} dB)")
        if delta < HF_DROP_BAD:
            fixed.pop(mid, None)
    if worst < HF_DROP_BAD:
        p2 = {**project, "voiceClean": fixed}
        return _res("danışıq səsi", "fixed", f"təmizlənmiş səs boğuq çıxırdı ({worst:+.1f} dB, hədd {HF_DROP_BAD}) — orijinal danışıq səsinə qayıdıldı (təmizləmə söndürüldü)", items), p2
    if worst < HF_DROP_WARN:
        return _res("danışıq səsi", "warn", f"təmizlənmiş səsdə yüksək tezlik azalıb ({worst:+.1f} dB) — `ses_evvel_sonra.m4a`-nı dinlə", items), project
    return _res("danışıq səsi", "ok", f"səs boğulmayıb (ən pis fərq {worst:+.1f} dB)", items), project


# ---------- 3. kadraj (rəqəmlə) və 4. rəng — hazır kadrlarda ----------
def _detect(frames: list[np.ndarray]) -> list[list[dict[str, float]]]:
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision

    from montaj import reframe

    model = reframe.face_model()
    if model is None:
        return [[] for _ in frames]
    det = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(base_options=BaseOptions(model_asset_path=str(model)), min_detection_confidence=0.5))
    out = []
    try:
        for rgb in frames:
            h, w = rgb.shape[:2]
            fs = []
            for d in det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))).detections:
                b = d.bounding_box
                fs.append({"x": b.origin_x / w, "y": b.origin_y / h, "w": b.width / w, "h": b.height / h})
            out.append(sorted(fs, key=lambda f: -f["w"] * f["h"]))
    finally:
        det.close()
    return out


def framing(faces: list[list[dict[str, float]]], labels: list[str]) -> dict[str, Any]:
    """Üz mərkəzdədir, baş üstü boşluq normaldır, üz çox kiçik deyil — hazır kadrlarda (üz tapılmayan kadrlar: B-roll/kart — keçilir)."""
    items, bad = [], []
    dxs = []
    seen = 0
    for fs, lab in zip(faces, labels):
        if not fs:
            continue
        seen += 1
        f = fs[0]
        cx, top, fh = f["x"] + f["w"] / 2, f["y"] - 0.3 * f["h"], f["h"]
        dxs.append(cx - 0.5)
        items.append(f"{lab}: üz mərkəzdən {100 * (cx - 0.5):+.1f}%, baş üstü {100 * max(0, top):.0f}%, üz hündürlüyü {100 * fh:.0f}%")
        if abs(cx - 0.5) > CENTER_TOL:
            bad.append(f"{lab}: üz mərkəzdən {100 * (cx - 0.5):+.1f}% kənardadır (hədd ±{100 * CENTER_TOL:.0f}%)")
        if top < HEAD_TOP[0]:
            bad.append(f"{lab}: baş kadrın yuxarısına çox yaxındır ({100 * top:.0f}%)")
        elif top > HEAD_TOP[1]:
            bad.append(f"{lab}: başın üstündə çox boşluq ({100 * top:.0f}%)")
        if fh < MIN_FACE_H:
            bad.append(f"{lab}: üz çox kiçikdir ({100 * fh:.0f}%) — kadraj daha yaxın olmalıdır")
    if not seen:
        return _res("kadraj", "skip", "yoxlanan kadrlarda üz tapılmadı (B-roll/kart)")
    r = _res("kadraj", "bad" if bad else "ok", (f"{len(bad)} kadraj problemi" if bad else f"üz mərkəzdədir, boşluqlar normaldır ({seen} kadr)"), bad or items)
    r["mean_dx"] = float(np.mean(dxs)) if dxs else 0.0
    return r


def skin_ok(rgb: np.ndarray, f: dict[str, float]) -> tuple[bool, str, tuple[float, float, float]]:
    h, w = rgb.shape[:2]
    x0, x1 = int((f["x"] + 0.22 * f["w"]) * w), int((f["x"] + 0.78 * f["w"]) * w)
    y0, y1 = int((f["y"] + 0.40 * f["h"]) * h), int((f["y"] + 0.70 * f["h"]) * h)
    patch = rgb[max(0, y0):max(y0 + 2, y1), max(0, x0):max(x0 + 2, x1)].reshape(-1, 3)
    r, g, b = (float(np.median(patch[:, i])) / 255 for i in range(3))
    hue, sat, val = colorsys.rgb_to_hsv(r, g, b)
    if hue < SKIN_HUE[0] and sat > 0.25:
        return False, f"dəri tonu qırmızıya meyllidir (hue {hue * 360:.0f}°)", (hue, sat, val)
    if hue > SKIN_HUE[1]:
        return False, f"dəri tonu sarıya meyllidir (hue {hue * 360:.0f}°)", (hue, sat, val)
    if sat < SKIN_SAT[0]:
        return False, f"dəri tonu solğundur (doyma {sat:.2f})", (hue, sat, val)
    if sat > SKIN_SAT[1]:
        return False, f"dəri tonu həddindən artıq doymuşdur ({sat:.2f})", (hue, sat, val)
    return True, "", (hue, sat, val)


def adjust_limits(project: dict[str, Any]) -> list[str]:
    """`look: auto` parametrləri təhlükəsiz hədlərdədir (saturation artımı, güclü kəskinlik, ağ balansı sürüşməsi yoxdur)."""
    out = []
    for c in project["clips"]:
        adj = c.get("adjust") or {}
        if not adj or c["track"] not in ("v1", "v2"):
            continue
        for k, (lo, hi) in ADJUST_LIMITS.items():
            if k in adj and not (lo - 1e-9 <= float(adj[k]) <= hi + 1e-9):
                out.append(f"klip {c['id']}: {k}={adj[k]} hədd xaricindədir [{lo}, {hi}]")
        t = adj.get("temperature")
        if t is not None and not (5800 <= float(t) <= 7200):
            out.append(f"klip {c['id']}: temperature={t} K hədd xaricindədir [5800, 7200]")
    return out


def color(frames: list[np.ndarray], faces: list[list[dict[str, float]]], media_ids: list[str | None], labels: list[str], project: dict[str, Any]) -> dict[str, Any]:
    """Dəri tonunda qırmızılıq/sarılıq/solğunluq, klipler arası işıq fərqi və look parametrlərinin hədləri."""
    items, bad = [], []
    for rgb, fs, lab in zip(frames, faces, labels):
        if fs:
            ok, why, hsv = skin_ok(rgb, fs[0])
            items.append(f"{lab}: dəri hue {hsv[0] * 360:.0f}°, doyma {hsv[1]:.2f}")
            if not ok:
                bad.append(f"{lab}: {why}")
    lum = {}
    for rgb, mid in zip(frames, media_ids):
        if mid:
            lum.setdefault(mid, []).append(float(rgb.mean()) / 255)
    if len(lum) > 1:
        ms = [float(np.mean(v)) for v in lum.values()]
        if max(ms) - min(ms) > LUMA_JUMP:
            bad.append(f"klipler arası işıq fərqi {100 * (max(ms) - min(ms)):.0f}% (hədd {100 * LUMA_JUMP:.0f}%) — `matchExposure` yoxla")
    bad += adjust_limits(project)
    if bad:
        return _res("rəng", "bad", f"{len(bad)} rəng problemi", bad)
    return _res("rəng", "ok", "dəri tonu təbiidir, look parametrləri hədlər daxilindədir", items)


def recenter(project: dict[str, Any], dx: float) -> dict[str, Any]:
    """Üzü mərkəzə gətirmək üçün kadraj açar kadrlarının cx-ini sürüşdürür (yalnız avtomatik kadrajlı klipləri; kənardan çıxmır)."""
    import copy

    q = copy.deepcopy(project)
    for c in q["clips"]:
        fr = c.get("frame") or {}
        if c["track"] == "v1" and fr.get("mode") in ("auto", "manual") and fr.get("keys"):
            w = float(fr.get("baseW", 1)) * float(fr.get("s", 1))
            for k in fr["keys"]:
                k["cx"] = round(min(max(float(k["cx"]) + dx * w, w / 2), 1 - w / 2), 4)
    return q
