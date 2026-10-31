#!/usr/bin/env bash
# OpenMontage + Montaj paneli — Claude Code cloud mühiti üçün setup skripti.
#
# Bu fayl yalnız quraşdırma əmrlərindən ibarətdir. SKILL.md / YAML mətni
# setup script sahəsinə YAPIŞDIRILMAMALIDIR — skill-lər repodakı
# .claude/skills/ qovluğundan avtomatik yüklənir, quraşdırma tələb etmir.
#
# İstifadə: claude.ai → mühit menyusu → Edit → "Setup script" sahəsinə
#   bash scripts/cloud-setup.sh
# yazın (repo klonlandıqdan sonra işləyir) və ya bu faylın məzmununu yapışdırın.
#
# Lazım olan şəbəkə ünvanları (bu sessiyada real sorğularla yoxlanılıb):
#   pypi.org, files.pythonhosted.org   — Python paketləri
#   registry.npmjs.org                 — remotion-composer npm paketləri
#   huggingface.co (+ yönləndirmə CDN-i) — faster-whisper modeli (ilk transkripsiyada)
#   storage.googleapis.com             — MediaPipe üz modeli (kadraj)
#   api.anthropic.com                  — yalnız ANTHROPIC_API_KEY verilsə (paneldaxili AI)
#   drive.usercontent.google.com       — Drive linkindən fayl yükləmə
# Gizli açar tələb olunmur. Açarları bu fayla YAZMAYIN — mühitin
# "Environment variables" bölməsindən verin.
set -euo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$REPO_DIR"

echo "[setup] ffmpeg yoxlanılır"
if ! command -v ffmpeg >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    (sudo -n true 2>/dev/null && SUDO=sudo || SUDO="")
    ${SUDO:-} apt-get update -qq && ${SUDO:-} apt-get install -y -qq ffmpeg fonts-dejavu-core libegl1 libgles2
  else
    echo "[setup] XƏBƏRDARLIQ: ffmpeg yoxdur və apt-get tapılmadı" >&2
  fi
fi

echo "[setup] Python asılılıqları (requirements.txt + dev)"
python3 -m pip install -q -r requirements.txt
python3 -m pip install -q -r requirements-dev.txt || true

echo "[setup] Montaj paneli asılılıqları (faster-whisper, mediapipe, anthropic)"
python3 -m pip install -q -r montaj/requirements.txt || echo "[setup] bəzi montaj asılılıqları quraşdırılmadı" >&2
if ! ldconfig -p 2>/dev/null | grep -q libEGL.so.1 && command -v apt-get >/dev/null 2>&1; then
  (apt-get update -qq >/dev/null 2>&1 || true)
  apt-get install -y -qq libegl1 libgles2 >/dev/null 2>&1 || echo "[setup] libegl1 quraşdırılmadı — avtomatik kadraj işləməyəcək" >&2
fi

if [ "${MONTAJ_PREFETCH_WHISPER:-1}" = "1" ]; then
  echo "[setup] Whisper modeli əvvəlcədən endirilir (${MONTAJ_WHISPER_MODEL:-small})"
  python3 - <<'PY' || echo "[setup] Model endirilmədi — ilk transkripsiyada yenidən cəhd olunacaq" >&2
import os
from faster_whisper import WhisperModel
WhisperModel(os.environ.get("MONTAJ_WHISPER_MODEL", "small"), device="cpu", compute_type="int8")
print("[setup] model hazırdır")
PY
fi

if command -v npm >/dev/null 2>&1 && [ -f remotion-composer/package-lock.json ]; then
  echo "[setup] remotion-composer npm paketləri"
  (cd remotion-composer && npm ci --no-audit --no-fund --loglevel=error)
fi

echo "[setup] Hazırdır. Paneli işə salmaq: python3 -m montaj --host 0.0.0.0 --port 4760"
