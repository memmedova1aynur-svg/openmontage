#!/bin/sh
# Telefon ölçüsündə önizləmə (390px en): sh phone_check.sh file.png|file.mp4 [saniyə]
in="$1"; t="${2:-0}"; o="${in%.*}_390.png"
case "$in" in *.mp4|*.mov) ffmpeg -v error -y -ss "$t" -i "$in" -frames:v 1 -vf scale=390:-1 "$o";; *) ffmpeg -v error -y -i "$in" -vf scale=390:-1 "$o";; esac
echo "$o"
