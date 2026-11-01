"""Kadrdakı üzlər və ağız hərəkəti zaman seriyası (əlavə model yoxdur): kim danışır, kadrarxası sual, növbələr.

seminar.active_speaker bir aralıq üçün tək cavab verir; burada bütün media üçün bir dəfə seriya qurulur və
istənilən cümləyə tətbiq olunur (M10 — kadrarxası sual, növ 11 — iki nəfərin növbəsi).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


def mouth_tracks(src: Path, start: float, end: float, fps: float = 5.0) -> dict[str, Any]:
    """{"times": [t], "tracks": [{"cx","cy","w","h","n","motion": [m per frame | None]}]} — üzlər x-mövqeyinə görə izlənir,
    hərəkət ağız nahiyəsinin (üzün aşağı üçdə biri) kadrlar arası fərqidir."""
    from montaj import reframe

    step = 1.0 / fps
    frames = list(reframe.sample_frames(src, start, end, step, width=480))
    dets = {round(d["t"], 3): d["faces"] for d in reframe.detect_faces(src, start, end, step=step)}
    times = [round(t, 3) for t, _ in frames]
    tracks: list[dict[str, Any]] = []
    for t in times:
        for f in dets.get(t, []):
            cx = f["x"] + f["w"] / 2
            tr = next((x for x in tracks if abs(x["cx"] - cx) < max(0.08, f["w"] * 0.6)), None)
            if tr is None:
                tr = {"cx": cx, "cy": f["y"] + f["h"] / 2, "w": f["w"], "h": f["h"], "n": 0, "boxes": {}}
                tracks.append(tr)
            tr["n"] += 1
            tr["cx"] += (cx - tr["cx"]) / tr["n"]
            tr["w"] += (f["w"] - tr["w"]) / tr["n"]
            tr["h"] += (f["h"] - tr["h"]) / tr["n"]
            tr["boxes"][t] = f
    tracks = [x for x in tracks if x["n"] >= max(2, len(times) * 0.2)]
    tracks.sort(key=lambda x: x["cx"])
    for tr in tracks:
        prev, mo = None, []
        for t, (_, rgb) in zip(times, frames):
            f = tr["boxes"].get(t) or {"x": tr["cx"] - tr["w"] / 2, "y": tr["cy"] - tr["h"] / 2, "w": tr["w"], "h": tr["h"]}
            h, w = rgb.shape[:2]
            x0, x1 = int((f["x"] + f["w"] * 0.25) * w), int((f["x"] + f["w"] * 0.75) * w)
            y0, y1 = int((f["y"] + f["h"] * 0.62) * h), int((f["y"] + f["h"] * 0.95) * h)
            u0, u1 = int((f["y"] + f["h"] * 0.2) * h), int((f["y"] + f["h"] * 0.5) * h)
            crop = _fix(rgb[max(0, y0):max(y0 + 1, y1), max(0, x0):max(x0 + 1, x1)])
            up = _fix(rgb[max(0, u0):max(u0 + 1, u1), max(0, x0):max(x0 + 1, x1)])
            if prev is not None:
                # baş tərpənməsi danışıq sayılmasın: üzün yuxarı hissəsinin (göz) hərəkəti çıxılır
                mo.append(max(0.0, float(np.abs(crop - prev[0]).mean()) - 0.7 * float(np.abs(up - prev[1]).mean())))
            else:
                mo.append(None)
            prev = (crop, up)
        tr["motion"] = mo
        del tr["boxes"]
    return {"times": times, "tracks": tracks}


def _fix(a: np.ndarray, h: int = 12, w: int = 20) -> np.ndarray:
    """Sabit ölçülü boz nümunə (üz qutusu kadrdan kadra bir az dəyişsə də müqayisə olunsun)."""
    g = a.astype(float).mean(axis=2)
    ys = np.linspace(0, g.shape[0] - 1, h).astype(int)
    xs = np.linspace(0, g.shape[1] - 1, w).astype(int)
    return g[np.ix_(ys, xs)]


def motion_in(series: dict[str, Any], track: int, s: float, e: float) -> float | None:
    vals = [m for t, m in zip(series["times"], series["tracks"][track]["motion"]) if s <= t <= e and m is not None]
    return float(np.mean(vals)) if vals else None


def main_track(series: dict[str, Any]) -> int | None:
    tr = series["tracks"]
    if not tr:
        return None
    return max(range(len(tr)), key=lambda i: (tr[i]["n"], tr[i]["w"]))


def turns(series: dict[str, Any], sentences: list[dict[str, Any]], ratio: float = 1.3) -> list[int | None]:
    """Hər cümlə üçün danışanın üz indeksi (ən çox ağız hərəkəti; aydın deyilsə əvvəlki danışan)."""
    out: list[int | None] = []
    prev = None
    for s in sentences:
        ms = [motion_in(series, i, s["s"], s["e"]) or 0.0 for i in range(len(series["tracks"]))]
        if not ms:
            out.append(None)
            continue
        order = sorted(range(len(ms)), key=lambda i: -ms[i])
        if len(ms) == 1 or ms[order[0]] > ratio * ms[order[1]]:
            prev = order[0]
        out.append(prev)
    return out
