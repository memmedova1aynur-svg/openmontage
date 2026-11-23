"""U02 «Təbiətdən ilham al» ({SPİKER_ADI}) — baza kəsim: 4 dubldan ən təmiz cümlələr (hamısı 1-ci məkan), color_auto, DFN 12.
python3 base_u02.py <esas_qovluğu>"""
import subprocess, sys, os, json
R = '/home/user/openmontage/instagram-clients/{musteri}/'; SRC = R + 'xam/U02_tebiet_uzun.mp4'
O = sys.argv[1]; os.makedirs(O, exist_ok=True)
# (başlanğıc, son, rakurs) — 19.11 agentlik: hər iki rakurs, güzgü çevrilmiş (hflip), rəng korreksiyası
SEG = [(93.45, 96.20, 1), (96.42, 98.58, 1), (117.98, 121.60, 1), (189.12, 194.50, 2), (194.80, 200.77, 2), (132.65, 136.23, 1), (141.03, 145.50, 1), (145.69, 150.34, 1), (260.25, 265.40, 2)]
PAD = 3.4
CA = {1: json.load(open(R + 'xam/ca_U02.json'))['vf'].replace('vibrance=intensity=0.11', 'eq=saturation=0.86'), 2: json.load(open(R + 'xam/ca_U02_L2.json'))['vf']}
ZS = [1.0, 1.07, 1.0, 1.0, 1.06, 1.0, 1.07, 1.0, 1.0]
ins, fc = [], []
for i, (a, b, loc) in enumerate(SEG):
    ins += ['-ss', f'{a}', '-t', f'{b - a:.3f}', '-i', SRC]
    z = ZS[i]
    zc = '' if z == 1 else f',crop={int(1080 / z)}:{int(1920 / z)}:{int((1080 - 1080 / z) / 2)}:{int((1920 - 1920 / z) * 0.30)},scale=1080:1920'
    fc.append(f'[{i}:v]{CA[loc]}{zc},hflip,fps=30,setsar=1,format=yuv420p,trim=duration={b - a:.3f},setpts=PTS-STARTPTS[v{i}]')
    fc.append(f'[{i}:a]aresample=48000,aformat=channel_layouts=mono,atrim=duration={b - a:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.015,afade=t=out:st={b - a - 0.03:.3f}:d=0.03[a{i}]')
n = len(SEG)
fc.append(''.join(f'[v{i}]' for i in range(n)) + f'concat=n={n}:v=1:a=0,tpad=stop_mode=clone:stop_duration={PAD}[v]')
fc.append(''.join(f'[a{i}]' for i in range(n)) + f'concat=n={n}:v=0:a=1[a]')
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y'] + ins + ['-filter_complex', ';'.join(fc), '-map', '[v]', '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', O + '/v.mp4', '-map', '[a]', O + '/raw.wav'], check=True)
sys.path.insert(0, '/home/user/openmontage/templates/expert-reels/pro')
from audio_pro import load, save, measure, dfn
x = load(O + '/raw.wav'); y = dfn(x, 12); y = y * 10 ** ((-14 - measure(y)['lufs']) / 20); save(O + '/voice0.wav', y)
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', O + '/voice0.wav', '-af', f'alimiter=limit=0.89:level=disabled,apad=pad_dur={PAD}', O + '/voice.wav'], check=True)
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', O + '/v.mp4', '-i', O + '/voice.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', O + '/base.mp4'], check=True)
for f in ('v.mp4', 'raw.wav', 'voice0.wav'): os.remove(O + '/' + f)
off = 0; B = []
for a, b, _ in SEG: B.append(round(off, 3)); off += b - a
json.dump({'loc': [l for _, _, l in SEG], 'seg_starts': B, 'speech_end': round(off, 3), 'dur': round(off + PAD, 3)}, open(O + '/timeline.json', 'w')); print('base ok', B, round(off, 2))
