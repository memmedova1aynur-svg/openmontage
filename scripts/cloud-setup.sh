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
# Heç bir addım bütün quraşdırmanı dayandırmır: səhvlər toplanır və sonda siyahı verilir (çıxış kodu 0).
# Səbəb: bulud mühitində setup uğursuz olanda sessiya ümumiyyətlə başlamır.
set -uo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$REPO_DIR" || exit 0
FAILED=()
step() {  # step "<ad>" <əmr...>
  local name="$1"; shift
  echo "[setup] $name"
  if ! "$@"; then
    echo "[setup] XƏBƏRDARLIQ: alınmadı — $name" >&2
    FAILED+=("$name")
  fi
}
SUDO=""; if [ "$(id -u)" != "0" ] && sudo -n true 2>/dev/null; then SUDO="sudo"; fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    step "ffmpeg (apt)" bash -c "$SUDO apt-get update -qq && $SUDO apt-get install -y -qq ffmpeg fonts-dejavu-core"
  else
    FAILED+=("ffmpeg yoxdur və apt-get tapılmadı")
  fi
fi

step "Python asılılıqları (requirements.txt)" python3 -m pip install -q -r requirements.txt
step "Python dev asılılıqları" python3 -m pip install -q -r requirements-dev.txt
step "Montaj asılılıqları (faster-whisper, mediapipe, Pillow, fonttools…)" python3 -m pip install -q -r montaj/requirements.txt

if ! ldconfig -p 2>/dev/null | grep -q libEGL.so.1 && command -v apt-get >/dev/null 2>&1; then
  step "libegl1/libgles2 (avtomatik kadraj üçün)" bash -c "($SUDO apt-get update -qq >/dev/null 2>&1 || true); $SUDO apt-get install -y -qq libegl1 libgles2 >/dev/null 2>&1"
fi

# Arxa səs təmizləmə: əvvəl torch CPU (yoxsa deepfilternet PyPI-dən böyük CUDA torch çəkər)
if ! python3 -c "import torch" >/dev/null 2>&1; then
  step "torch CPU (arxa səs təmizləmə)" python3 -m pip install -q --index-url https://download.pytorch.org/whl/cpu torch torchaudio
fi
if python3 -c "import torch" >/dev/null 2>&1 && ! python3 -c "import importlib.util,sys; sys.exit(importlib.util.find_spec('df') is None)" >/dev/null 2>&1; then
  step "deepfilternet" python3 -m pip install -q deepfilternet
fi
if [ ! -f "$HOME/.cache/DeepFilterNet/DeepFilterNet3/config.ini" ]; then
  mkdir -p "$HOME/.cache/DeepFilterNet"
  # github.com/raw bəzi şəbəkə siyasətlərində bloklanır — raw.githubusercontent.com işləyir
  step "DeepFilterNet3 modeli" bash -c "curl -sSL -m 180 -o /tmp/DeepFilterNet3.zip https://raw.githubusercontent.com/Rikorose/DeepFilterNet/main/models/DeepFilterNet3.zip && python3 -m zipfile -e /tmp/DeepFilterNet3.zip '$HOME/.cache/DeepFilterNet/'"
fi

if [ "${MONTAJ_PREFETCH_WHISPER:-1}" = "1" ]; then
  step "Whisper modeli (${MONTAJ_WHISPER_MODEL:-large-v3-turbo}) — ilk transkripsiyada da endirilə bilər" python3 -c '
import os
from faster_whisper import WhisperModel
WhisperModel(os.environ.get("MONTAJ_WHISPER_MODEL", "large-v3-turbo"), device="cpu", compute_type="int8")
'
fi

if command -v npm >/dev/null 2>&1 && [ -f remotion-composer/package-lock.json ]; then
  step "remotion-composer npm paketləri (montaj üçün məcburi deyil)" bash -c "cd remotion-composer && npm ci --no-audit --no-fund --loglevel=error"
fi

if [ ${#FAILED[@]} -eq 0 ]; then
  echo "[setup] Hazırdır."
else
  echo "[setup] Hazırdır, amma bu addımlar alınmadı (sessiyada yenidən: bash scripts/cloud-setup.sh):" >&2
  for x in "${FAILED[@]}"; do echo "  - $x" >&2; done
fi
exit 0
