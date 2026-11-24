#!/bin/bash
# U01C tam zəncir: base → C render+QC → loqo sona → QC → mahnısız
set -e; cd /home/user/openmontage/instagram-clients/{musteri}; D=montaj/U01C_pinterest_bento; L=referans/Logo_{Brend}_StopMotion.mp4
cd /home/user/openmontage && bash instagram-clients/{musteri}/alətlər/rqBC_fast.sh C | cut -c1-300; cd instagram-clients/{musteri}
cp $D/final.mp4 $D/esas_final_nologo.mp4
mk(){ ffmpeg -loglevel error -y -i $1 -i $2 -i $L -filter_complex "[0:v]fps=30,format=yuv420p,setsar=1[v0];[2:v]fps=30,format=yuv420p,setsar=1,scale=1080:1920[v1];[1:a]aresample=48000,aformat=channel_layouts=stereo,apad[a0p];[a0p]atrim=0:$(ffprobe -v error -show_entries format=duration -of csv=p=0 $1)[a0];[2:a]aresample=48000,aformat=channel_layouts=stereo,volume=4dB[a1];[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][ac];[ac]aresample=192000,alimiter=limit=0.78:attack=1:release=40:level=disabled,aresample=48000[a]" -map "[v]" -map "[a]" -c:v libx264 -crf $4 -maxrate $5 -bufsize 28M -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart $3; }
mk $D/esas_final_nologo.mp4 $D/esas_final_nologo.mp4 $D/final.mp4 18 20M
# 21.11 qayda: musiqisiz yalnız istəniləndə — mk $D/esas_final_nologo.mp4 montaj/U01_moodboard_reklam/esas/base.mp4 paketler/capcut/{MUSTERI}_Moodboard_senet_reklam_C_musiqisiz.mp4 21 7M
cd /home/user/openmontage && python3 templates/expert-reels/pro/qc_render.py instagram-clients/{musteri}/$D/final.mp4 --clean instagram-clients/{musteri}/$D/clean.mp4 --out instagram-clients/{musteri}/$D/QC 2>&1 | grep "QC " | cut -c1-400; echo HAZIR
