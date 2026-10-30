#!/usr/bin/env bash
# Create projects/<id>/remotion from the expert-reels template and transcode
# the source footage into public/base.mp4 (H.264, -16 LUFS). The source decides the output size:
# a 4K vertical source keeps 2160x3840 (render scale 2), anything smaller stays 1080x1920
# (scale 1) - footage is never upscaled. The scale goes to public/render.json for render.sh.
#
# Usage: templates/expert-reels/scripts/setup_workspace.sh <project-id> <source-video>
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
TPL="$ROOT/templates/expert-reels"
WS="$ROOT/projects/$1/remotion"
SRC="$2"

if [ ! -d "$ROOT/remotion-composer/node_modules" ]; then
  (cd "$ROOT/remotion-composer" && npm install --no-audit --no-fund)
fi

mkdir -p "$WS/public"
ln -sfn "$ROOT/remotion-composer/node_modules" "$WS/node_modules"
# src is copied, not linked: webpack resolves symlinks to their real path, which
# would make ../public/edit.json point back into the template.
rm -rf "$WS/src" && cp -r "$TPL/src" "$WS/src"
ln -sfn "$TPL/public/fonts" "$WS/public/fonts"
cat > "$WS/tsconfig.json" <<'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "skipLibCheck": true
  },
  "include": ["src"]
}
EOF

# Phone footage is often 10-bit HDR HEVC; tonemap only when the source is HLG/PQ.
TRC="$(ffprobe -v error -select_streams v:0 -show_entries stream=color_transfer -of csv=p=0 "$SRC")"
# ffmpeg applies the phone's rotation metadata itself, so W/H below are the displayed size.
read -r W H < <(ffprobe -v error -select_streams v:0 -show_entries stream=width,height:stream_side_data=rotation \
  -of csv=p=0 "$SRC" | tr '\n' ',' | awk -F, '{w=$1;h=$2; if ($3 ~ /90/) {t=w;w=h;h=t}; print w, h}')
if [ "$W" -gt "$H" ]; then
  echo "NOTE: horizontal source (${W}x${H}); this template renders 9:16 Reels. Horizontal lessons need the 16:9 lesson layout." >&2
fi
if [ "$W" -ge 2160 ] && [ "$H" -ge 3840 ]; then SCALE=2; else SCALE=1; fi
OUTW=$((1080 * SCALE)); OUTH=$((1920 * SCALE))
echo "{\"scale\": $SCALE, \"source\": \"${W}x${H}\"}" > "$WS/public/render.json"
VF="scale=$OUTW:$OUTH:flags=lanczos,format=yuv420p"
if [ "$TRC" = "arib-std-b67" ] || [ "$TRC" = "smpte2084" ]; then
  VF="zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,$VF"
fi
ffmpeg -v error -y -i "$SRC" -vf "$VF" -af "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" \
  -c:v libx264 -preset fast -crf 17 -g 30 -r 30 -c:a aac -b:a 192k "$WS/public/base.mp4"
echo "workspace ready: $WS (source ${W}x${H} -> ${OUTW}x${OUTH})"
