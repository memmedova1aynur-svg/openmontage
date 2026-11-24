"""3D ikonlar (Three.js, prosedur — pulsuz, açarsız): şəffaf fonlu kadr ardıcıllığı, `depthfx` `icon3d` effekti üçün.

Növlər: brain (beyin), books (kitablar), bulb (lampa — fikir), heart (ürək), star (ulduz), check (təsdiq).
Kadrlar keşlənir (növ + rəng + müddət + ölçü). İlk dəfə `three` npm-dən qurulur (data qovluğuna).
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

from montaj.config import REPO_ROOT, data_dir

KINDS = ("brain", "books", "bulb", "heart", "star", "check")
FPS = 30
SRC = REPO_ROOT / "montaj" / "icons3d_web"


def env_dir() -> Path:
    d = data_dir() / "icons3d" / "env"
    d.mkdir(parents=True, exist_ok=True)
    for f in ("index.html", "render.mjs"):
        if not (d / f).is_file() or (d / f).read_bytes() != (SRC / f).read_bytes():
            shutil.copyfile(SRC / f, d / f)
    if not (d / "node_modules" / "three").is_dir():
        (d / "package.json").write_text('{"name":"icons3d","private":true,"type":"module"}')
        subprocess.run(["npm", "install", "--silent", "--no-audit", "--no-fund", "three@0.160.0"], cwd=d, check=True)
    pw = d / "node_modules" / "playwright"
    if not pw.exists():  # mühitdə qurulu Playwright (başqa versiya qurulmur)
        r = subprocess.run(["node", "-e", "console.log(require.resolve('playwright/package.json'))"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            pw.symlink_to(Path(r.stdout.strip()).parent)
        else:
            subprocess.run(["npm", "install", "--silent", "--no-audit", "--no-fund", "playwright"], cwd=d, check=True)
    return d


def frames_dir(kind: str, color: str | None, dur: float, size: int) -> Path:
    if kind not in KINDS:
        raise ValueError(f"naməlum ikon: {kind} ({', '.join(KINDS)})")
    d = env_dir()
    sig = hashlib.sha1(f"{kind}|{color}|{dur:.3f}|{size}|".encode() + (SRC / "index.html").read_bytes()).hexdigest()[:12]
    out = data_dir() / "icons3d" / "cache" / f"{kind}_{sig}"
    n = max(1, round(dur * FPS))
    if not (out / f"f{n - 1:04d}.png").is_file():
        tmp = out.with_name(out.name + ".part")
        shutil.rmtree(tmp, ignore_errors=True)
        r = subprocess.run(["node", "render.mjs", str(tmp), kind, color or "-", f"{dur:.3f}", str(FPS), str(size)],
                           cwd=d, capture_output=True, text=True)
        if r.returncode != 0 or not (tmp / f"f{n - 1:04d}.png").is_file():
            raise RuntimeError(f"3D ikon render olunmadı: {(r.stderr or r.stdout).strip()[-300:]}")
        shutil.rmtree(out, ignore_errors=True)
        tmp.rename(out)
    return out


def frames(kind: str, color: str | None, dur: float, size: int) -> list[np.ndarray]:
    """RGBA uint8 kadrlar (30 fps)."""
    d = frames_dir(kind, color, dur, size)
    return [np.asarray(Image.open(f).convert("RGBA")) for f in sorted(d.glob("f*.png"))]
