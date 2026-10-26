#!/usr/bin/env bash
# Create projects/<id>/remotion from the expert-reels template and transcode
# the source footage into public/base.mp4 (H.264, 1080x1920, -16 LUFS).
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
VF="scale=1080:1920:flags=lanczos,format=yuv420p"
if [ "$TRC" = "arib-std-b67" ] || [ "$TRC" = "smpte2084" ]; then
  VF="zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,$VF"
fi
ffmpeg -v error -y -i "$SRC" -vf "$VF" -af "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" \
  -c:v libx264 -preset fast -crf 17 -g 30 -r 30 -c:a aac -b:a 192k "$WS/public/base.mp4"
echo "workspace ready: $WS"
