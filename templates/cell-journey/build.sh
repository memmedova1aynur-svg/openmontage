#!/usr/bin/env bash
# Bir damcının səyahəti — 25 s, 1080x1920, 30 fps. Tam pulsuz: Three.js + earshot + ffmpeg.
# İstifadə: bash templates/cell-journey/build.sh stories/sura-ana-sudu.json [iş_qovluğu]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/../.." && pwd)"
STORY="$(cd "$HERE" && realpath "${1:?story.json yolu lazımdır}")"
WORK="${2:-$ROOT/projects/cell-journey-$(basename "$STORY" .json)}"
mkdir -p "$WORK"; cp "$HERE"/{index.html,render.mjs,music.py,cues.json,package.json} "$WORK"/; cp "$STORY" "$WORK/story.json"
cd "$WORK"
[ -d node_modules/three ] || npm install --silent --no-audit --no-fund
if [ ! -e node_modules/playwright ]; then   # use the preinstalled Playwright (do not install another one)
  PW="$(node -e "console.log(require.resolve('playwright').replace(/\/playwright\/.*/,''))" 2>/dev/null || true)"
  if [ -n "$PW" ]; then ln -sfn "$PW/playwright" node_modules/playwright; else npm install --silent --no-audit --no-fund playwright; fi
fi
EARSHOT_BIN="${EARSHOT_BIN:-$(bash "$ROOT/.claude/skills/earshot/scripts/install.sh")}"; export EARSHOT_BIN
echo "1/5 kadrlar (750)…";  rm -rf frames; node render.mjs frames 30 0 25 | tail -1
echo "2/5 musiqi…";         python3 music.py music.wav
echo "3/5 video…";          ffmpeg -loglevel error -y -framerate 30 -i frames/f%05d.jpg -i music.wav -c:v libx264 -preset slow -crf 16 \
                              -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart base.mp4
echo "4/5 səs effektləri…"; mkdir -p sfx
mk() { [ -f "sfx/$1" ] || "$EARSHOT_BIN" make "$2" ${3:+--sound "$3"} -o "sfx/$1" --seed "$4" >/dev/null; }
mk drip.wav x drip/drop 2; mk whoosh_soft.wav x whoosh/soft 3; mk whoosh_deep.wav x whoosh/deep 4
mk shield.wav "a soft success sound" "" 5; mk tink.wav x click/soft 6; mk twinkle.wav x like/twinkle 7; mk riser.wav x rise/air 8
python3 "$ROOT/.claude/skills/real-sfx/scripts/real_sfx.py" place base.mp4 cues.json -o mixed.mp4 --no-duck >/dev/null
echo "5/5 səs səviyyəsi (-14 LUFS)…"
J=$(ffmpeg -hide_banner -i mixed.mp4 -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g() { echo "$J" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
ffmpeg -loglevel error -y -i mixed.mp4 -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,alimiter=limit=0.79:level=false,aresample=48000" \
  -c:v copy -c:a aac -b:a 192k -movflags +faststart final_ig.mp4
echo "hazır: $WORK/final_ig.mp4"
