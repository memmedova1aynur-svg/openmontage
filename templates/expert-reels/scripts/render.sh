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
RAW="$P/assets/video/${NAME}_raw.mp4"
npx remotion render src/index.tsx Reel "$RAW" --codec=h264 --crf=17 --concurrency=4 "${BROWSER[@]}" --log=error

# Two-pass 3.6 Mbps keeps a ~60 s Reel near 26 MB, under Claude's 30 MB upload limit.
LOG="$(mktemp -d)/x264"
ffmpeg -v error -y -i "$RAW" -c:v libx264 -preset slow -b:v 3600k -maxrate 5000k -bufsize 8000k -pass 1 -passlogfile "$LOG" -an -f mp4 /dev/null
ffmpeg -v error -y -i "$RAW" -c:v libx264 -preset slow -b:v 3600k -maxrate 5000k -bufsize 8000k -pass 2 -passlogfile "$LOG" \
  -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart "$P/renders/$NAME.mp4"
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$P/renders/$NAME.mp4"
