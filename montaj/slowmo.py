"""Yavaşlatma (videoqrafiya: "50 FPS material 25 FPS timeline-da 2 dəfə yavaşlayır; proqramın əlavə kadr yaratması artefakt verir").

Yalnız REAL kadrlar: yüksək fps-li hissə (məs. 60 fps) çıxış fps-ində (30) bütün kadrları ilə göstərilir → 0.5x, hamar.
Kadr uydurulmur (interpolyasiya yoxdur). Material imkan vermirsə (30 fps-i 0.5x etmək) — kadrlar təkrarlanır, titrək görünür:
xəbərdarlıq verilir, istifadəçiyə dürüst deyilir.
Nəticə — törəmə media (media/derived/), səssiz; zaman xətti onu adi klip kimi işlədir (sürət sahəsi yoxdur).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def min_clean_speed(src_fps: float, out_fps: float) -> float:
    """Kadr təkrarı olmadan ən yavaş sürət (60 → 30: 0.5)."""
    return min(1.0, out_fps / max(1.0, src_fps))


def verdict(src_fps: float, out_fps: float, speed: float) -> str | None:
    """Material yavaşlatmaya imkan vermirsə izah (yoxsa None)."""
    eff = src_fps * speed
    if eff + 0.5 < out_fps * 0.8:
        return (f"material {src_fps:.0f} fps — {speed}x yavaşlatmada saniyədə {eff:.0f} real kadr qalır (çıxış {out_fps:.0f}); "
                f"kadrlar təkrarlanacaq, titrək görünə bilər. Hamar yavaşlatma üçün 60 fps çəkiliş lazımdır")
    return None


def make(src: Path, dst: Path, a: float, b: float, speed: float, out_fps: str) -> None:
    """[a, b] mənbə hissəsi → speed dəfə yavaş (səssiz, yüksək keyfiyyət)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".part.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", str(src), "-an",
                    "-vf", f"setpts=(PTS-STARTPTS)/{speed:.4f},fps={out_fps}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "14", "-pix_fmt", "yuv420p", str(tmp)], check=True)
    tmp.rename(dst)
