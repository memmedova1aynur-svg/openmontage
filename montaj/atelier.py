"""Bəzək rejimi (atelier): hər hero video üçün SIFIRDAN yazılmış səhnə — hazır şablon yox.

Agent bu videoya xas HTML/CSS/JS səhnə yazır (müəyyən vaxtın funksiyası: `window.setTime(t)`), sistem onu deterministik kadr-kadr çəkib
MP4 edir və B-roll/animasiya kimi planda işlədir:
  plan: {"broll": [{"make": {"kind": "atelier", "props": {"html": "yol/səhnə.html"}}, "mode": "cover", "at": 18.2, "dur": 4.2}]}
Qayda: hazır `scenes` kataloqundan kopyalama yoxdur; hər səhnə həmin videonun mövzusuna, üslub dəstinə və danışıq cümlələrinə görə yazılır.
Müddət: ~0.1 s/kadr (30 fps → 4 s ≈ 12–20 s). Nəticə keşlənir (html məzmunu + ölçü + müddət).
Nümunə: montaj/atelier/example_hero.html. Yazma bələdçisi: skills/creative/atelier-scenes.md.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from montaj import fonts
from montaj.errors import UserError

MJS = Path(__file__).resolve().parent / "editor" / "atelier.mjs"


def render(html: str | Path, dur: float, W: int, H: int, theme: dict[str, Any] | None, out_dir: Path, fps: int = 30) -> Path:
    src = Path(html)
    if not src.is_file():
        raise UserError(f"Bəzək səhnəsi tapılmadı: {src}", "props.html — mövcud HTML faylının yolu olmalıdır.")
    key = hashlib.sha1(src.read_bytes() + f"{W}x{H}@{fps}:{dur:.3f}:{json.dumps(theme or {}, sort_keys=True)}".encode()).hexdigest()[:12]
    out = out_dir / f"atelier_{src.stem}_{key}.mp4"
    if out.is_file():
        return out
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="atelier_") as tmp:
        frames = Path(tmp) / "f"
        cfg = {"html": str(src), "outDir": str(frames), "W": W, "H": H, "fps": fps, "dur": dur, "theme": theme or {},
               "fonts": [{"family": fam, "weight": w, "path": str(p), "range": fonts.RANGES[sub]} for fam, w, sub, p in fonts.editor_font_files()] + fonts.extra_font_faces()}
        cf = Path(tmp) / "cfg.json"
        cf.write_text(json.dumps(cfg), encoding="utf-8")
        r = subprocess.run(["node", str(MJS), str(cf)], capture_output=True, text=True)
        if r.returncode != 0:
            raise UserError("Bəzək səhnəsi çəkilmədi.", (r.stderr or r.stdout).strip()[-300:] or "HTML-də window.setTime(t) olmalıdır.")
        part = out.with_suffix(".part.mp4")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(fps), "-i", str(frames / "f_%05d.png"), "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(part)], check=True)
        shutil.move(str(part), out)
    return out
