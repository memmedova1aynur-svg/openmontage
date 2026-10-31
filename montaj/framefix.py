"""Avtomatik kadraj düzəlişi: əyriliyin (üfüqün) düzəldilməsi və obyektin (üzün) ortalanması.

* Əyrilik: fondakı düz xətlər (rəf, masa, divar kənarı) üzrə — Canny + Hough, ±8°-dən kiçik bucaqlı uzun xətlərin
  çəkili medianı. 0.4°–6° arası düzəldilir; az xətt varsa toxunulmur (uydurulmur).
* Ortalama: MediaPipe üz aşkarlanması; mənbə çıxışla eyni formatdadırsa (məs. 9:16 → 9:16), ortalamaq üçün
  kiçik yaxınlaşma lazımdır — ümumi yaxınlaşma MAX_ZOOM-la məhdudlaşır (görüntü yumşalmasın), qismən ortalama olur.
* Kamera bir klip boyu sabit sayılır (əl kamerasının hərəkəti izlənmir — bunu istifadəçiyə demək lazımdır).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np

from montaj import reframe

MAX_ZOOM = 1.12      # ümumi yaxınlaşma həddi (fırlatma + ortalama)
TILT_MIN, TILT_MAX = 0.4, 6.0


def detect_tilt(src: Path, start: float, end: float, samples: int = 6) -> dict[str, Any]:
    """Kadrın əyrilik bucağı (dərəcə; müsbət = saat əqrəbi istiqamətində əyilib). Etibarsızdırsa angle=None."""
    import cv2

    step = max(0.3, (end - start) / max(samples, 8))
    angles, weights = [], []
    for _t, rgb in reframe.sample_frames(src, start, end, step, width=720):
        g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        g = cv2.GaussianBlur(g, (3, 3), 0)
        edges = cv2.Canny(g, 40, 120)
        h, w = g.shape
        lines = cv2.HoughLinesP(edges, 1, np.pi / 1440, threshold=40, minLineLength=int(w * 0.10), maxLineGap=6)
        for x1, y1, x2, y2 in (lines.reshape(-1, 4) if lines is not None else []):
            dx, dy = float(x2 - x1), float(y2 - y1)
            if dx < 0:
                dx, dy = -dx, -dy
            a = math.degrees(math.atan2(dy, dx))  # şəkil koordinatı (y aşağı): müsbət = sağa doğru aşağı
            if abs(a) < 8:
                angles.append(a)
                weights.append(math.hypot(dx, dy))
    if len(angles) < 8:
        return {"angle": None, "lines": len(angles), "why": "fonda kifayət qədər düz xətt yoxdur"}
    order = np.argsort(angles)
    a_s, w_s = np.array(angles)[order], np.array(weights)[order]
    cum = np.cumsum(w_s)
    med = float(a_s[np.searchsorted(cum, cum[-1] / 2)])
    spread = float(np.average(np.abs(a_s - med), weights=w_s))
    if spread > 2.5:
        return {"angle": None, "lines": len(angles), "why": "xətlərin bucağı çox səpələnib (perspektiv) — toxunulmur"}
    return {"angle": round(med, 2), "lines": len(angles), "spread": round(spread, 2)}


def rotation_zoom(rot_deg: float, w: float, h: float) -> float:
    r = math.radians(abs(rot_deg))
    return math.cos(r) + max(w / h, h / w) * math.sin(r)


def center_window(face_cx: float, face_top: float, max_scale: float) -> tuple[float, float, float]:
    """Eyni formatlı mənbədə pəncərə (s, cx, cy): üz üfüqi ortaya, baş üstü boşluq ~12–18%.
    s — pəncərə ölçüsü (1 = bütün kadr), max_scale-dən çox yaxınlaşma yoxdur."""
    need = abs(face_cx - 0.5)
    s_min = 1 / max_scale
    s = 1.0
    if need > 0.03:
        s = max(s_min, 1 - 2 * need)  # tam ortalamaq üçün lazım olan, həddə qədər
    cx = min(max(face_cx, s / 2), 1 - s / 2)
    cy = 0.5
    if s < 1:  # baş üstündə çox boşluq varsa pəncərəni bir az aşağı sal
        want_top = 0.15 * s
        cy = min(max(face_top - want_top + s / 2, s / 2), 1 - s / 2)
    return round(s, 4), round(cx, 4), round(cy, 4)


def suggest_fix(src: Path, m: dict[str, Any], src_in: float, src_out: float, out_w: int, out_h: int) -> dict[str, Any]:
    """Klip üçün kadraj təklifi (render-in `frame` formatında) və qısa izah."""
    sw, sh = float(m["width"]), float(m["height"])
    same = abs(sw / sh - out_w / out_h) < 0.02
    tilt = detect_tilt(src, src_in, src_out)
    rot = 0.0
    notes = []
    if tilt["angle"] is not None and TILT_MIN <= abs(tilt["angle"]) <= TILT_MAX:
        rot = -tilt["angle"]
        notes.append(f"əyrilik {tilt['angle']:+.1f}° düzəldildi")
    elif tilt["angle"] is not None and abs(tilt["angle"]) > TILT_MAX:
        notes.append(f"əyrilik {tilt['angle']:+.1f}° çox böyükdür — avtomatik düzəldilmədi")
    elif tilt["angle"] is None:
        notes.append(f"əyrilik ölçülmədi: {tilt['why']}")
    zr = rotation_zoom(rot, sw, sh) if rot else 1.0
    samples = reframe.detect_faces(src, src_in, src_out, step=max(0.5, (src_out - src_in) / 8))
    faces = [f for x in samples for f in x["faces"][:1]]
    if not same:
        aspect = next((k for k, v in reframe.ASPECTS.items() if abs(v - out_w / out_h) < 0.02), "9:16")
        fr = reframe.suggest(m, src_in, src_out, aspect, out_h, samples)
        fr["rotate"] = round(rot, 2)
        fr["autoFix"] = True
        return {"frame": fr, "notes": notes + fr.get("warnings", []), "tilt": tilt}
    if not faces:
        notes.append("üz tapılmadı — ortalama edilmədi")
        s, cx, cy = 1.0, 0.5, 0.5
    else:
        fcx = float(np.median([f["x"] + f["w"] / 2 for f in faces]))
        ftop = float(np.median([f["y"] for f in faces]))
        s, cx, cy = center_window(fcx, ftop, MAX_ZOOM / zr)
        if s < 1:
            left = abs(cx - fcx)
            notes.append(f"obyekt ortalandı (yaxınlaşma {1 / s * zr:.2f}x)" + (" — qismən, keyfiyyəti qorumaq üçün" if left > 0.02 else ""))
        else:
            notes.append("obyekt artıq ortadadır")
    fr = {"aspect": "source", "mode": "auto" if s < 1 else "none", "s": s, "baseW": 1, "baseH": 1,
          "keys": [{"t": src_in, "cx": cx, "cy": cy}], "rotate": round(rot, 2), "warnings": [], "autoFix": True}
    return {"frame": fr, "notes": notes, "tilt": tilt}
