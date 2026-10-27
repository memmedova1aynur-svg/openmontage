#!/usr/bin/env bash
# Remove background noise (cafe clatter, cutlery, music bleed) from an already-rendered edit
# without re-rendering the picture:
#   1. DeepFilterNet3 cleans the cut footage's voice track (assets/video/cut.mp4)
#   2. public/base.mp4 gets the clean voice (video stream copied)
#   3. Remotion renders the audio only (voice + SFX), then it replaces the audio of
#      renders/<name>.mp4 and renders/<name>_ig.mp4 (pictures copied, -16 LUFS kept)
#
# Needs the deep-filter binary (https://github.com/Rikorose/DeepFilterNet/releases,
# x86_64-unknown-linux-musl build) at $DEEP_FILTER or /home/user/dfbin/deep-filter.
#
# Usage: templates/expert-reels/scripts/denoise.sh <project-id> [render-name]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
P="$ROOT/projects/$1"
NAME="${2:-final}"
DF="${DEEP_FILTER:-/home/user/dfbin/deep-filter}"
WS="$P/remotion"
TMP="$P/artifacts/dn"
mkdir -p "$TMP"

ffmpeg -v error -y -i "$P/assets/video/cut.mp4" -vn -ac 1 -ar 48000 -c:a pcm_s16le "$TMP/voice.wav"
# -D keeps the voice in sync (compensates the model look-ahead); --pf = post-filter for residual noise
"$DF" -D --pf -o "$TMP/out" "$TMP/voice.wav" >/dev/null 2>&1

cp "$WS/public/base.mp4" "$TMP/base_noisy.mp4"
ffmpeg -v error -y -i "$TMP/base_noisy.mp4" -i "$TMP/out/voice.wav" -map 0:v -map 1:a -c:v copy \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" -ac 2 -c:a aac -b:a 192k "$WS/public/base.mp4"

BROWSER=()
for b in /opt/pw-browsers/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell; do
  [ -x "$b" ] && BROWSER=(--browser-executable="$b") && break
done
(cd "$WS" && npx remotion render src/index.tsx Reel "$TMP/mix.wav" --codec=wav "${BROWSER[@]}" --log=error)

for f in "$NAME.mp4" "${NAME}_ig.mp4"; do
  src="$P/renders/$f"
  [ -f "$src" ] || continue
  cp "$src" "$TMP/noisy_$f"
  if [ "$f" = "$NAME.mp4" ]; then AC=(-c:a aac -b:a 320k); else AC=(-af "loudnorm=I=-16:TP=-1.5:LRA=11" -ar 48000 -c:a aac -b:a 192k); fi
  ffmpeg -v error -y -i "$TMP/noisy_$f" -i "$TMP/mix.wav" -map 0:v -map 1:a -c:v copy "${AC[@]}" -shortest -movflags +faststart "$src"
  ffprobe -v error -show_entries format=duration,size -of csv=p=0 "$src"
done
