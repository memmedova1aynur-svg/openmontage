#!/usr/bin/env bash
# Premix the 48 s soundtrack: Gemini TTS narration (assets/audio/gemini/vo_s*.wav)
# placed at each scene's cue, music time-stretched to 48 s, ducked under the voice
# (sidechain), faded out. HyperFrames only supports a static data-volume, so all
# level automation happens here.
set -euo pipefail
cd "$(dirname "$0")/.."

VO=assets/audio/gemini
OUT=hyperframes/assets/soundtrack.wav
DUR=48
# narration cue (seconds) per scene: s1..s8
CUES=(0.5 6.4 12.4 17.4 23.4 31.4 38.4 43.6)

inputs=(); delays=""; mixin=""
for i in $(seq 1 8); do
  inputs+=(-i "$VO/vo_s$i.wav")
  ms=$(python3 -c "print(int(${CUES[$((i-1))]}*1000))")
  delays+="[$((i-1)):a]aresample=48000,aformat=channel_layouts=mono,adelay=${ms}[v$i];"
  mixin+="[v$i]"
done

music_len=$(ffprobe -v error -show_entries format=duration -of csv=p=0 assets/music/bgm.mp3)
tempo=$(python3 -c "print(round($music_len/($DUR+0.3), 4))")

ffmpeg -y -hide_banner -loglevel error "${inputs[@]}" -i assets/music/bgm.mp3 -filter_complex "
${delays}
${mixin}amix=inputs=8:normalize=0,apad=whole_dur=${DUR},loudnorm=I=-15:TP=-1.5:LRA=7,aformat=channel_layouts=stereo,asplit[vo][key];
[8:a]aresample=48000,atempo=${tempo},volume=0.42,afade=t=in:d=0.8,afade=t=out:st=$((DUR-2)):d=1.9,apad=whole_dur=${DUR}[mus];
[mus][key]sidechaincompress=threshold=0.03:ratio=8:attack=25:release=420:makeup=1[duck];
[duck][vo]amix=inputs=2:normalize=0,alimiter=limit=0.89,atrim=0:${DUR}[out]" \
  -map "[out]" -ar 48000 -ac 2 "$OUT"

echo "wrote $OUT ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT") s)"
