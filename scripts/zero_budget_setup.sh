#!/usr/bin/env bash
# Zero-budget OpenMontage setup: installs only free, local tools.
# Safe to re-run. No API keys, no paid services.
set -euo pipefail

pip install -q piper-tts faster-whisper

MODELS="${PIPER_MODELS_DIR:-$HOME/.piper/models}"
mkdir -p "$MODELS"
BASE=https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium
for f in en_US-lessac-medium.onnx en_US-lessac-medium.onnx.json; do
  [ -s "$MODELS/$f" ] || curl -sSL -o "$MODELS/$f" "$BASE/$f"
done

python - <<'PY'
from tools.tool_registry import registry
import json
registry.discover()
s = registry.provider_menu_summary()
print("runtimes:", s["composition_runtimes"])
for c in s["capabilities"]:
    if c["capability"] in ("tts", "analysis", "subtitle", "video_post", "music_search"):
        print(c["capability"], c["configured"], "/", c["total"])
PY
