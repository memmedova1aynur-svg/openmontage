#!/usr/bin/env bash
# Give one stretch of the voice a megaphone / loudspeaker colour (band-limited, a little drive and slap
# echo) and leave the rest untouched. Used for a "quoted" opening line.
#
# Usage: templates/expert-reels/scripts/megaphone.sh <video> <start_s> <end_s>   (edits the file in place)
set -euo pipefail
IN="$1"; A="$2"; B="$3"
TMP="${IN%.mp4}.mega.mp4"
ffmpeg -v error -y -i "$IN" -filter_complex "\
[0:a]asplit=3[x][y][z];\
[x]atrim=0:$A,asetpts=PTS-STARTPTS[pre];\
[y]atrim=$A:$B,asetpts=PTS-STARTPTS,highpass=f=420,lowpass=f=3200,volume=2.2,asoftclip=type=tanh,aecho=0.8:0.5:38:0.28,volume=0.9[mega];\
[z]atrim=$B,asetpts=PTS-STARTPTS[post];\
[pre][mega][post]concat=n=3:v=0:a=1[a]" \
  -map 0:v -c:v copy -map "[a]" -c:a aac -b:a 192k "$TMP"
mv "$TMP" "$IN"
echo "megaphone $A-$B s applied to $IN"
