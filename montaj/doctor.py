"""Sessiya başında BİR əmr: montaj üçün hər şey hazırdırmı? Çatışanı (mümkünsə) özü qurur, bir qısa nəticə verir.

  python -m montaj.doctor          → yoxla, nəticəni çap et (çıxış kodu 0 = hazırdır)
  python -m montaj.doctor --fix    → çatışan Python/npm/apt hissələrini `scripts/cloud-setup.sh` ilə qur, yenidən yoxla

Məqsəd: istifadəçi hər yeni sessiyada "X kitabxanası yoxdur" mesajı görməsin; token və vaxt itkisi olmasın.
İsteğe bağlı olanlar (açarlar, Drive paylaşımı) ayrıca "məsləhət" kimi yazılır, işi dayandırmır.
"""

from __future__ import annotations

import argparse
import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _py(mod: str) -> bool:
    try:
        importlib.import_module(mod); return True
    except Exception:  # noqa: BLE001
        return False


def _net(host: str, t: int = 5) -> bool:
    try:
        r = subprocess.run(["curl", "-s", "-m", str(t), "-o", "/dev/null", "-w", "%{http_code}", f"https://{host}/"], capture_output=True, text=True)
        return r.stdout.strip() not in ("", "000")
    except Exception:  # noqa: BLE001
        return False


def check() -> tuple[list[str], list[str]]:
    """(məcburi çatışmazlıqlar, məsləhətlər)"""
    need: list[str] = []; tips: list[str] = []
    for b in ("ffmpeg", "ffprobe", "node"):
        if not shutil.which(b): need.append(f"{b} yoxdur")
    for mod, name in (("faster_whisper", "faster-whisper"), ("mediapipe", "mediapipe"), ("PIL", "Pillow"), ("numpy", "numpy"), ("cv2", "opencv")):
        if not _py(mod): need.append(f"Python paketi: {name}")
    if not (ROOT / "remotion-composer" / "node_modules").exists(): tips.append("remotion-composer/node_modules yoxdur (yalnız Remotion üçün lazımdır)")
    if shutil.which("node") and subprocess.run(["node", "-e", "require('playwright')"], capture_output=True).returncode != 0:
        tips.append("node playwright tapılmadı (qrafik/animasiya qatı üçün; bulud mühitində hazır olur)")
    cache = Path.home() / ".cache" / "huggingface"
    if not cache.exists() or not any(cache.rglob("*turbo*")): tips.append("Whisper modeli keşdə yoxdur (ilk transkripsiyada endiriləcək, ~1 dəq)")
    from montaj import library
    cat = library.load(); k = {x: sum(1 for i in cat["items"] if i["kind"] == x) for x in library.KINDS}
    if k["broll"] < 10 or k["music"] < 3: need.append("kitabxana kataloqu boşdur → `python -m montaj.library seed`")
    if not any(i.get("source") == "drive" for i in cat["items"]): tips.append("Drive kitabxanasında öz fayllarınız yoxdur (qovluq: OpenMontage Kitabxana; 'Linki olan hər kəs — Baxan' + `python -m montaj.library sync`)")
    if not _net("assets.mixkit.co"): tips.append("Mixkit-ə çıxış yoxdur (stok B-roll/musiqi endirilə bilməz; mühit şəbəkə siyahısını yoxlayın)")
    if not (ROOT / ".venv-watch" / "bin" / "watch-skill").exists(): tips.append("watch-skill yoxdur (referans video linki analizi) → `bash scripts/cloud-setup.sh`")
    if not os.environ.get("PIXABAY_API_KEY"): tips.append("PIXABAY_API_KEY yoxdur (isteğe bağlı: B-roll seçimi genişlənir)")
    if not os.environ.get("FREESOUND_API_KEY"): tips.append("FREESOUND_API_KEY yoxdur (isteğe bağlı: CC0 musiqi seçimi genişlənir; Mixkit işləyir)")
    return need, tips


def main() -> int:
    ap = argparse.ArgumentParser(prog="python -m montaj.doctor"); ap.add_argument("--fix", action="store_true"); a = ap.parse_args()
    need, tips = check()
    if need and a.fix:
        print("quraşdırılır (scripts/cloud-setup.sh)…", flush=True)
        subprocess.run(["bash", str(ROOT / "scripts" / "cloud-setup.sh")], cwd=ROOT)
        if any("kataloq" in n for n in need):
            from montaj import library; library.seed()
        need, tips = check()
    print("HAZIRDIR" if not need else "ÇATIŞMAZLIQ: " + "; ".join(need))
    for t in tips: print("  məsləhət:", t)
    return 0 if not need else 1


if __name__ == "__main__":
    sys.exit(main())
