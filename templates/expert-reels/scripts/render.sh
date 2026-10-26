#!/usr/bin/env bash
# Render projects/<id>/remotion and encode an Instagram-ready MP4 (< 30 MB).
#
# Usage: templates/expert-reels/scripts/render.sh <project-id> [output-name]
#        STILL=<frame> templates/expert-reels/scripts/render.sh <project-id>   # one preview frame
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
P="$ROOT/projects/$1"
WS="$P/remotion"
NAME="${2:-final}"
BROWSER=()
# Use a local Chromium when Remotion cannot download its own headless shell.
for b in /opt/pw-browsers/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell; do
  [ -x "$b" ] && BROWSER=(--browser-executable="$b") && break
done

cd "$WS"
if [ -n "${STILL:-}" ]; then
  mkdir -p "$P/renders/stills"
  npx remotion still src/index.tsx Reel "$P/renders/stills/frame_$STILL.png" --frame="$STILL" "${BROWSER[@]}" --log=error
  exit 0
fi

mkdir -p "$P/assets/video" "$P/renders"
# Master: rendered at 2x (2160x3840) so captions and graphics are drawn natively in 4K,
# JPEG frames at quality 95 (Remotion's default 80 softens detail), x264 CRF 14 slow.
# This file goes to Instagram as-is: no second lossy pass.
npx remotion render src/index.tsx Reel "$P/renders/$NAME.mp4" --scale=2 --codec=h264 --crf=14 \
  --x264-preset=slow --jpeg-quality=95 --audio-bitrate=320k --concurrency=4 "${BROWSER[@]}" --log=error
ffprobe -v error -show_entries stream=width,height:format=duration,size -of default=nw=1 "$P/renders/$NAME.mp4"

# Delivery copy: same 4K picture as HEVC (hvc1, plays natively on iPhone) sized to ~44 MB,
# because phones fail to download the 200-300 MB master from chat.
DUR="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$P/renders/$NAME.mp4")"
HB="$(python3 -c "print(int(44*8*1000/$DUR) - 200)")"
ffmpeg -v error -y -i "$P/renders/$NAME.mp4" -c:v libx265 -preset fast -tag:v hvc1 -pix_fmt yuv420p \
  -x265-params "crf=20:vbv-maxrate=$HB:vbv-bufsize=$((HB * 2)):log-level=error" \
  -c:a aac -b:a 192k -movflags +faststart "$P/renders/${NAME}_ig.mp4"
ffprobe -v error -show_entries format=size -of default=nw=1 "$P/renders/${NAME}_ig.mp4"

# Optional small 1080p copy for chat previews (Claude uploads are capped at 30 MB).
if [ -n "${PREVIEW:-}" ]; then
  DUR="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$P/renders/$NAME.mp4")"
  VB="$(python3 -c "print(min(3600, int(27*8*1000/$DUR) - 170))")k"
  ffmpeg -v error -y -i "$P/renders/$NAME.mp4" -vf scale=1080:1920:flags=lanczos -c:v libx264 -preset slow -b:v "$VB" \
    -maxrate 5000k -bufsize 8000k -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart "$P/renders/${NAME}_preview.mp4"
fi
