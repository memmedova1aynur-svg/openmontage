#!/usr/bin/env bash
# Dizayn alətlərini (yenidən) quraşdırır. Konteyner yenilənəndə bir dəfə işlət.
set -e
command -v inkscape >/dev/null || (apt-get update -q && apt-get install -y -q inkscape)
command -v convert >/dev/null || apt-get install -y -q imagemagick
python3 -c "import playwright" 2>/dev/null || pip install -q playwright
mkdir -p /root/design-tools && cd /root/design-tools
[ -f package.json ] || npm init -y >/dev/null
npm i -s sharp fabric konva gsap animejs lottie-web motion three
echo "hazır: inkscape, imagemagick, blender, ffmpeg, playwright(py) + /root/design-tools/node_modules"
