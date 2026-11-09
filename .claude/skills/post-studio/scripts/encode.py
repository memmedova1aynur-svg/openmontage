"""Kadrlar + SFX -> MP4 (-14 LUFS, faststart) və QA.
python3 encode.py --frames DIR --out video.mp4 --total 10 --sfx '[["pop",1.0,-20],["ding",5.6,-18]]'
SFX növləri avkit.synth: pop, swoosh, ding (ətraflı: templates/expert-reels/pro/avkit.py)."""
import argparse, json, sys, os, tempfile
sys.path.insert(0, '/home/user/openmontage/templates/expert-reels/pro')
import avkit as K, numpy as np
a = argparse.ArgumentParser(); a.add_argument('--frames', required=True); a.add_argument('--out', required=True)
a.add_argument('--total', type=float, required=True); a.add_argument('--sfx', default='[]'); a.add_argument('--fps', default='30')
x = a.parse_args(); mix = np.zeros((int(x.total * K.SR), 2))
for kind, t, db in json.loads(x.sfx): mix = K.add_sfx(mix, K.synth(kind), float(t), float(db))
d = tempfile.mkdtemp(); raw, fin = os.path.join(d, 'm.wav'), os.path.join(d, 'f.wav')
K.save(mix, raw); K.finalize(raw, fin)
K.run(['ffmpeg', '-v', 'error', '-y', '-framerate', x.fps, '-i', os.path.join(x.frames, '%05d.png'), '-i', fin, '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
       '-pix_fmt', 'yuv420p', '-maxrate', '4.5M', '-bufsize', '9M', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', x.out])
print(K.qa(x.out))
