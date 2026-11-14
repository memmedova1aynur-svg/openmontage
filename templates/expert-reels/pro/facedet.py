"""Üz tapma (mediapipe BlazeFace, montaj-ın modeli). Bütün yeni QA/rəng alətləri bunu işlədir."""
import os
from pathlib import Path
import numpy as np
_DET = None
CANDS = [Path(os.environ.get("MONTAJ_DATA_DIR", "/root/montaj-data")) / "models/blaze_face_short_range.tflite",
         Path(__file__).resolve().parents[3] / ".montaj/models/blaze_face_short_range.tflite"]


def _det():
    global _DET
    if _DET is None:
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions, vision
        m = next((p for p in CANDS if p.is_file()), None)
        if m is None:
            from montaj.reframe import face_model
            m = face_model()
        _DET = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(base_options=BaseOptions(model_asset_path=str(m)), min_detection_confidence=0.5))
    return _DET


def faces(rgb):
    """rgb: HxWx3 uint8 və ya float 0..1 → [(x0,y0,x1,y1,score)] nisbi koordinatlarda, böyükdən kiçiyə."""
    import mediapipe as mp
    a = rgb if rgb.dtype == np.uint8 else (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    h, w = a.shape[:2]
    out = []
    for d in _det().detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(a))).detections:
        b = d.bounding_box
        out.append((b.origin_x / w, b.origin_y / h, (b.origin_x + b.width) / w, (b.origin_y + b.height) / h, float(d.categories[0].score) if d.categories else 0.0))
    return sorted(out, key=lambda f: -(f[2] - f[0]) * (f[3] - f[1]))
