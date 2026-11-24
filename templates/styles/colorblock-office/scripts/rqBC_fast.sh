#!/bin/bash
# B və C versiyalarını render et → gate qovluqlarına final/clean → QC
cd /home/user/openmontage; C=instagram-clients/{musteri}; E=$C/montaj/U01_moodboard_reklam/esas
for X in ${@:-B C}; do T0=$(date +%s)
  [ $X = B ] && V=U01B_moodboard_qurulur || V=U01C_pinterest_bento
  python3 $C/alətlər/gen_u01_$X.py $E >/dev/null || { echo "$X GEN XƏTA"; continue; }
  (cd $E/hf_$X && npx --yes hyperframes@0.9.65 render -q delivery --workers 3 -o ../render_$X.mp4 > ../render_$X.log 2>&1) || { echo "$X RENDER XƏTA"; tail -3 $E/render_$X.log; }
  (cd $E/hf_${X}_clean && npx --yes hyperframes@0.9.65 render -q draft --fps 4 --workers 3 -o ../clean_$X.mp4 > ../clean_$X.log 2>&1) || echo "$X CLEAN XƏTA"
  mkdir -p $C/montaj/$V; cp $E/render_$X.mp4 $C/montaj/$V/final.mp4; cp $E/clean_$X.mp4 $C/montaj/$V/clean.mp4
  python3 templates/expert-reels/pro/qc_render.py $C/montaj/$V/final.mp4 --clean $C/montaj/$V/clean.mp4 --out $C/montaj/$V/QC 2>&1 | grep "QC " | cut -c1-500 | sed "s/^/$X /"; echo "$X vaxt: $(( $(date +%s) - T0 )) s"
done
