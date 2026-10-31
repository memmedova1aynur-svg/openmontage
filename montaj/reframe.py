"""Avtomatik kadraj təklifi (9:16 və s.) — üz aşkarlanması ilə.

Qaydalar:
  * Ölçü dəyişmir (yaxınlaşdırma yoxdur), yalnız kəsim pəncərəsinin yeri seçilir.
    İstisna: baş üstündə çox boşluq varsa VƏ mənbə çıxışdan böyükdürsə, keyfiyyət
    itkisi olmadan yüngül (≤1.25x) yaxınlaşma təklif olunur.
  * Bir neçə üz varsa hamısı kadra salınmağa çalışılır; sığmırsa xəbərdarlıq.
  * Kadraj yumşaq hərəkət edir: hamarlama + ölü zona.
  * Mənbədə olmayan hissə uydurulmur (pəncərə həmişə kadr daxilindədir).

Kadraj məlumatı klipdə saxlanılır:
  frame = {aspect, mode: auto|manual|none, s, keys: [{t, cx, cy}], rotate, warnings}
  cx, cy — pəncərə mərkəzi (0..1, mənbəyə nisbətən), s — pəncərə hündürlüyü / mənbə hündürlüyü.
"""

from __future__ import annotations

import subprocess
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np

from montaj import diag
from montaj.config import models_dir

FACE_MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/face_detector/"
                  "blaze_face_short_range/float16/latest/blaze_face_short_range.tflite")
ASPECTS = {"9:16": 9 / 16, "1:1": 1.0, "4:5": 4 / 5, "16:9": 16 / 9}


def face_model() -> Path | None:
    p = models_dir() / "blaze_face_short_range.tflite"
    if not p.is_file():
        try:
            urllib.request.urlretrieve(FACE_MODEL_URL, p)
        except Exception:  # noqa: BLE001
            diag.exception("üz modeli endirilmədi")
            return None
    return p


def sample_frames(src: Path, start: float, end: float, step: float = 0.5, width: int = 480):
    """(t, rgb ndarray) generatoru."""
    dur = max(0.1, end - start)
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", str(src),
         "-vf", f"fps=1/{step},scale={width}:-2", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True)
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
         "-of", "csv=p=0", str(src)], capture_output=True, text=True, check=True).stdout.strip().split(",")
    sw, sh = int(probe[0]), int(probe[1])
    h = int(round(width * sh / sw / 2) * 2)
    n = len(out.stdout) // (width * h * 3)
    arr = np.frombuffer(out.stdout[: n * width * h * 3], dtype=np.uint8).reshape(n, h, width, 3)
    for i in range(n):
        yield start + i * step, arr[i]


def detect_faces(src: Path, start: float, end: float, step: float = 0.5) -> list[dict[str, Any]]:
    model = face_model()
    if model is None:
        return []
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision

    det = vision.FaceDetector.create_from_options(
        vision.FaceDetectorOptions(base_options=BaseOptions(model_asset_path=str(model)), min_detection_confidence=0.5))
    res = []
    try:
        for t, rgb in sample_frames(src, start, end, step):
            h, w = rgb.shape[:2]
            img = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
            faces = []
            for d in det.detect(img).detections:
                b = d.bounding_box
                faces.append({"x": b.origin_x / w, "y": b.origin_y / h, "w": b.width / w, "h": b.height / h,
                              "score": float(d.categories[0].score) if d.categories else 0.0})
            res.append({"t": round(t, 3), "faces": faces})
    finally:
        det.close()
    return res


def _smooth(vals: list[float], k: int = 5) -> list[float]:
    if not vals:
        return vals
    pad = k // 2
    a = np.pad(np.array(vals, dtype=float), pad, mode="edge")
    return list(np.convolve(a, np.ones(k) / k, mode="valid"))


def suggest(m: dict[str, Any], src_in: float, src_out: float, aspect: str, out_h: int,
            samples: list[dict[str, Any]], kind_hint: str = "") -> dict[str, Any]:
    """Üz nümunələrindən kadraj təklifi."""
    sw, sh = float(m["width"]), float(m["height"])
    ar = ASPECTS.get(aspect, 9 / 16)
    warnings: list[str] = []
    src_ar = sw / sh
    if abs(src_ar - ar) < 0.02:
        return {"aspect": aspect, "mode": "none", "s": 1.0, "keys": [{"t": src_in, "cx": 0.5, "cy": 0.5}],
                "rotate": 0, "warnings": ["Mənbə artıq bu formatdadır — kəsim lazım deyil."]}
    # pəncərə: s=1 olanda mümkün olan ən böyük pəncərə
    if src_ar > ar:   # enli mənbə → hündürlük tam, en kəsilir
        base_w, base_h = ar * sh / sw, 1.0
    else:             # hündür mənbə → en tam, hündürlük kəsilir
        base_w, base_h = 1.0, (sw / ar) / sh
    s = 1.0
    with_faces = [x for x in samples if x["faces"]]
    if kind_hint in ("product", "event"):
        warnings.append("Məhsul/tədbir videosunda vacib obyektlər avtomatik tanınmır — kadrajı yoxlayıb əl ilə düzəldin.")
    if not with_faces:
        warnings.append("Üz tapılmadı — pəncərə mərkəzdədir. Lazım olsa əl ilə dəyişin.")
        keys = [{"t": src_in, "cx": 0.5, "cy": 0.5}]
        return {"aspect": aspect, "mode": "auto", "s": s, "baseW": base_w, "baseH": base_h,
                "keys": keys, "rotate": 0, "warnings": warnings}
    cxs, cys, ts = [], [], []
    tops, bottoms = [], []
    for x in samples:
        if x["faces"]:
            l = min(f["x"] for f in x["faces"])
            r = max(f["x"] + f["w"] for f in x["faces"])
            top = min(f["y"] for f in x["faces"])
            bot = max(f["y"] + f["h"] for f in x["faces"])
            if r - l > base_w * 0.9:
                warnings.append("Kadrda bir neçə nəfər var və hamısı 9:16 pəncərəyə sığmır — əl ilə seçin və ya 1:1/4:5 sınayın.")
            cxs.append((l + r) / 2)
            # baş + çənə + çiyin üçün yer: üzün yuxarısından bir az yuxarı, aşağıdan xeyli aşağı
            cys.append(top + (bot - top) * 0.9)
            tops.append(top)
            bottoms.append(bot)
        else:
            cxs.append(cxs[-1] if cxs else 0.5)
            cys.append(cys[-1] if cys else 0.5)
        ts.append(x["t"])
    # yüngül yaxınlaşma yalnız baş üstündə çox boşluq və mənbə ehtiyatı olanda
    headroom = float(np.median(tops)) if tops else 0.2
    max_zoom = min(1.25, (sh * base_h) / max(1, out_h))
    if base_h == 1.0 and headroom > 0.22 and max_zoom > 1.02:
        s = round(1 / max_zoom, 3)
        warnings.append(f"Baş üstündə artıq boşluq azaldılıb (yaxınlaşma {1/s:.2f}x, keyfiyyət itkisi olmadan).")
    win_w, win_h = base_w * s, base_h * s
    cxs = _smooth(cxs, 5)
    cys = _smooth(cys, 5)
    keys: list[dict[str, float]] = []
    last = None
    for t, cx, cy in zip(ts, cxs, cys):
        cx = min(max(cx, win_w / 2), 1 - win_w / 2)
        # üz mərkəzi pəncərənin yuxarı ~40%-də olsun
        cyw = min(max(cy - win_h * 0.1, win_h / 2), 1 - win_h / 2)
        if last is None or abs(cx - last["cx"]) > 0.04 * win_w * 2 or abs(cyw - last["cy"]) > 0.04:
            last = {"t": round(t, 3), "cx": round(cx, 4), "cy": round(cyw, 4)}
            keys.append(last)
    if bottoms and win_h < 1:
        lowest = float(np.max(bottoms))
        if keys and lowest > keys[0]["cy"] + win_h / 2:
            warnings.append("Çənə və ya əllər bəzi anlarda pəncərədən çıxa bilər — yoxlayın.")
    crop_px = sh * win_h
    if crop_px < out_h * 0.66:
        warnings.append(f"Kəsim çox kiçikdir ({int(crop_px)} px → {out_h} px): görüntü bulanıqlaşa bilər.")
    return {"aspect": aspect, "mode": "auto", "s": s, "baseW": base_w, "baseH": base_h,
            "keys": keys or [{"t": src_in, "cx": 0.5, "cy": 0.5}], "rotate": 0,
            "warnings": sorted(set(warnings))}


def output_size(first_video: dict[str, Any] | None, aspect: str) -> tuple[int, int]:
    """Çıxış ölçüsü: mənbənin imkanından böyük deyil, cüt ədədlər."""
    if not first_video or aspect == "source":
        w = int(first_video["width"]) if first_video else 1080
        h = int(first_video["height"]) if first_video else 1920
        return w // 2 * 2, h // 2 * 2
    ar = ASPECTS[aspect]
    sw, sh = float(first_video["width"]), float(first_video["height"])
    if sw / sh > ar:
        h = min(sh, 1920 if ar < 1 else 1080 / ar if ar > 1 else 1080)
    else:
        h = min(sw / ar, 1920 if ar < 1 else 1080)
    h = int(h) // 2 * 2
    w = int(round(h * ar)) // 2 * 2
    return w, h
