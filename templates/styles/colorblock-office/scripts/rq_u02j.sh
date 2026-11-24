#!/bin/bash
# U02: HF qur → render → clean (4 fps) → QC → loqo sona → mahnısız
T0=$(date +%s); cd /home/user/openmontage; C=instagram-clients/{musteri}; D=$C/montaj/U02_tebietden_ilham; E=$D/esas; L=$C/referans/Logo_{Brend}_StopMotion.mp4
python3 $C/alətlər/gen_u02j.py $E >/dev/null || { echo GEN XƏTA; exit 1; }
(cd $E/hf && npx --yes hyperframes@0.9.65 render -q delivery --workers 3 -o ../render.mp4 > ../render.log 2>&1) || { echo RENDER XƏTA; tail -3 $E/render.log; }
rm -rf /tmp/hyperframes-extract-cache-0   # disk dolmasın
(cd $E/hf_clean && npx --yes hyperframes@0.9.65 render -q draft --fps 30 --workers 3 -o ../clean_render.mp4 > ../clean.log 2>&1) || echo CLEAN XƏTA
cp $E/clean_render.mp4 $D/clean.mp4; rm -rf /tmp/hyperframes-extract-cache-0
mk(){ ffmpeg -loglevel error -y -i $1 -i $2 -i $L -filter_complex "[0:v]fps=30,format=yuv420p,setsar=1[v0];[2:v]fps=30,format=yuv420p,setsar=1,scale=1080:1920[v1];[1:a]aresample=48000,aformat=channel_layouts=stereo,apad[a0p];[a0p]atrim=0:$(ffprobe -v error -show_entries format=duration -of csv=p=0 $1)[a0];[2:a]aresample=48000,aformat=channel_layouts=stereo,volume=4dB[a1];[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][ac];[ac]volume=-1.7dB,aresample=192000,alimiter=limit=0.78:attack=1:release=40:level=disabled,aresample=48000[a]" -map "[v]" -map "[a]" -c:v libx264 -crf $4 -maxrate $5 -bufsize 28M -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart $3; }
mk $E/render.mp4 $E/render.mp4 $D/final.mp4 18 20M
# 19.11: mahnısız = danışıq + səs effektləri (dəniz səsi daxil), yalnız musiqi çıxır
# (21.11 agentlik: musiqisiz yalnız istəniləndə) python3 $C/../aytan-celilova/alətlər/mix_nomusic.py $E $E/render.mp4 $E/nomus.mp4 >/dev/null
# (21.11 agentlik: musiqisiz yalnız istəniləndə) mkdir -p $C/paketler/capcut; mk $E/render.mp4 $E/nomus.mp4 $C/paketler/capcut/{MUSTERI}_Tebietden_ilham_reklam_musiqisiz.mp4 21 7M
FULL=$(python3 -c "import json;print(\",\".join(f\"{a}-{b}\" for a,b in json.load(open(\"$E/flips.json\"))))"); python3 templates/expert-reels/pro/qc_render.py $D/final.mp4 --clean $D/clean.mp4 --full "$FULL" --out $D/QC 2>&1 | grep "QC " | cut -c1-600; echo "vaxt: $(( $(date +%s) - T0 )) s"
