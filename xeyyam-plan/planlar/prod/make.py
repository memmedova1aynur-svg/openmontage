"""Xəyyam seriyası: bir videonun tam montajı.  İstifadə: python3 make.py cfg/NN.json
cfg: n, name, keep[[a,b]], fix{}, base{s,cx,cy}, plan{...talk.py açarları...},
     el: {questions:[[src_t, dur, txt]], cards:[[src_a, src_b, txt]], items:[[src_t, txt]], headline: "..."} — vaxtlar MƏNBƏ saniyəsi ilə,
     fx: [{theme, a, b (mənbə san), l0, l1, burst, hold, opts}]"""
import json, glob, os, sys, subprocess, re, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); PRO = '/home/user/openmontage/templates/expert-reels/pro'
C = json.load(open(sys.argv[1])); n = C['n']; os.chdir(HERE)
A = json.load(open(glob.glob(os.path.expanduser(f'~/montaj-data/projects/xeyyam-yeni-{n}/analysis/*.json'))[0]))
SRC = glob.glob(os.path.expanduser(f'~/montaj-data/projects/xeyyam-yeni-{n}/media/originals/*'))[0]
_sd = subprocess.run(['ffmpeg', '-nostdin', '-i', SRC, '-af', f"highpass=f=100,silencedetect=noise={C.get('noise', -42)}dB:d=0.4", '-vn', '-f', 'null', '-'], capture_output=True, text=True).stderr
_v = [float(x) for x in re.findall(r'silence_(?:start|end): ([0-9.]+)', _sd)]
sil0 = [(x, y) for x, y in zip(_v[0::2], _v[1::2]) if y - x >= 0.42]  # səs səviyyəsinə uyğun hədd (montaj detektoru zəif səsdə sözü udur)
# sözün sonu səssizliyin içinə düşürsə (zəif səs), kəsimi sözün sonundan sonraya çək — son heca kəsilməsin
sil = []
for x, y in sil0:
    tails = [w['e'] for w in A['words'] if x - 0.05 < w['e'] < y - 0.2 and w['s'] < x + 0.1]
    x2 = min(max([x] + [e + 0.10 - 0.18 for e in tails]), y - 0.45)
    if y - x2 >= 0.4: sil.append((max(x, x2), y))
W = []
for w in A['words']:
    s, e = w['s'], w['e']
    for x, y in sil:
        if x <= s < y: s = y - 0.10
    for x, y in sil:
        if s < x and (x < e <= y + 0.05 or e > y): e = x + 0.12
    W.append({"type": "word", "text": w['w'], "start": round(s, 3), "end": round(max(e, s + 0.08), 3)})
os.makedirs('work', exist_ok=True); json.dump({"words": W}, open(f'work/w{n}.json', 'w'), ensure_ascii=False)
segs = []
for a0, b0 in C['keep']:
    cur = a0
    for x, y in sil:
        if x > cur + 0.3 and y < b0 and x > a0: segs.append([cur, x + 0.18]); cur = y - 0.14
    segs.append([cur, b0])
segs = [s for s in segs if any(w['start'] >= s[0] - 0.02 and w['end'] <= s[1] + 0.02 for w in W)]
# uzun seqmentləri cümlə/vergül sərhədində böl (punch-in)
MAXS = C.get('max_shot', 5.5); out = []
for a, b in segs:
    pts = [a]
    while b - pts[-1] > MAXS:
        cand = [w for w in W if pts[-1] + 2.2 < w['end'] < b - 1.5 and re.search(r'[.,?!]$', w['text'])]
        if not cand: cand = [w for w in W if pts[-1] + 2.5 < w['end'] < b - 1.5]
        if not cand: break
        tgt = pts[-1] + min(MAXS * 0.75, (b - pts[-1]) / 2)
        w = min(cand, key=lambda w: abs(w['end'] - tgt)); nx = next((v for v in W if v['start'] >= w['end'] - 0.01 and v is not w), None)
        pts.append(round((w['end'] + nx['start']) / 2 if nx else w['end'], 2))
    pts.append(b); out += [[x, y] for x, y in zip(pts, pts[1:])]
if C.get('end_at'): out[-1][1] = C['end_at']  # son sakit söz üçün əl ilə uzatma
Z = C.get('zooms', [1.0, 1.16]); segs = [[round(a, 2), round(b, 2), Z[i % len(Z)]] for i, (a, b) in enumerate(out)]
def fin(t):  # mənbə vaxtı → hazır videonun vaxtı
    off = 0.0
    for a, b, _ in segs:
        if t < a: return round(off, 2)
        if t <= b: return round(off + t - a, 2)
        off += b - a
    return round(off, 2)
T = sum(b - a for a, b, _ in segs); el = C.get('el', {})
P = {"src": SRC, "words": f"w{n}.json", "segs": segs, "fix": C.get('fix', {}), "cap_first": True, "accent": "#6CC57E", "style": "dinamik",
     "base": C.get('base'), "out": f"../out/{n}_{C['name']}.mp4", **C.get('plan', {})}
if not P['base']: P.pop('base')
if 'questions' in el: P['questions'] = [[fin(t), d, x] for t, d, x in el['questions']]
if 'cards' in el: P['cards'] = [[fin(a), fin(b), x] for a, b, x in el['cards']]
if 'items' in el: P['items'] = [[fin(t), x] for t, x in el['items']]
if 'headline' in el: P['headline'] = el['headline']
json.dump(P, open(f'work/p{n}.json', 'w'), ensure_ascii=False, indent=1)
print(f"{len(segs)} seqment, {T:.1f} s"); 
if len(sys.argv) > 2 and sys.argv[2] == 'plan':
    for a, b, z in segs: print(f"  {fin(a):6.2f}  src {a:6.2f}-{b:6.2f} z{z}  " + ' '.join(w['text'] for w in W if w['start'] >= a - 0.02 and w['end'] <= b + 0.02)[:110])
    sys.exit()
r = subprocess.run(['python3', 'talk.py', f'{HERE}/work/p{n}.json'], cwd=PRO, capture_output=True, text=True)
m = re.search(r'OK (\S+\.mp4)', r.stdout)
if not m: print(r.stdout[-1500:], r.stderr[-1500:]); sys.exit(1)
base_mp4 = m.group(1); final = f"{HERE}/done/{n}_{C['name']}.mp4"; os.makedirs('done', exist_ok=True)
fx = C.get('fx', [])
if fx:
    wins = [{"l0": 0, "l1": 1, **f, "a": fin(f['a']), "b": (T + 0.3 if f.get('hold') else fin(f['b']))} for f in fx]
    shutil.rmtree(f'work/fx{n}', ignore_errors=True)
    subprocess.run(['node', 'fx_render.js', 'fx.html', f'work/fx{n}', json.dumps(wins)], check=True, capture_output=True)
    cmd = ['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-i', base_mp4]; fc = []; last = '0:v'
    for k, w in enumerate(wins):
        cmd += ['-itsoffset', str(w['a']), '-framerate', '30', '-i', f'work/fx{n}/w{k}/%04d.png']
        en = f"gte(t,{w['a']})" if w.get('hold') else f"between(t,{w['a']},{w['b']})"
        fc.append(f"[{last}][{k + 1}:v]overlay=enable='{en}':eof_action={'repeat' if w.get('hold') else 'pass'}[v{k}]"); last = f'v{k}'
    cmd += ['-filter_complex', ';'.join(fc), '-map', f'[{last}]', '-map', '0:a', '-c:a', 'copy', '-c:v', 'libx264', '-crf', '15', '-preset', 'medium',
            '-pix_fmt', 'yuv420p', '-r', '30', '-movflags', '+faststart', '-t', f'{T:.2f}', final]
    subprocess.run(cmd, check=True)
else: shutil.copy(base_mp4, final)
# yoxlama: kadr vərəqi + QC + yenidən transkripsiya
import numpy as np
d = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', final], capture_output=True, text=True).stdout)
sel = '+'.join(f'eq(n,{int(d * 30 * k / 8) + 12})' for k in range(8))
subprocess.run(['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-i', final, '-vf', f"select='{sel}',scale=250:444,tile=8x1", '-frames:v', '1', '-vsync', '0', f'work/qc{n}.png'])
sys.path.insert(0, '/home/user/openmontage'); os.chdir('/home/user/openmontage')
from tools.analysis.delivery_qc import DeliveryQC
q = DeliveryQC().execute({"input_path": final, "loudness_profile": "social", "format": "short_form", "expected": {"width": 1080, "height": 1920, "fps": 30}}); q = getattr(q, 'data', q)
print('QC:', q.get('verdict'), q.get('loudness', {}).get('integrated_lufs'), 'LUFS, pik', q.get('loudness', {}).get('true_peak_dbtp'), [f['level'] + ':' + f['check'] for f in q.get('findings', [])])
from faster_whisper import WhisperModel
pcm = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', final, '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], capture_output=True).stdout, np.float32)
sg, _ = WhisperModel('large-v3-turbo', compute_type='int8').transcribe(pcm, language='az')
print('YENİDƏN TRANSKRİPT:', ' '.join(s.text.strip() for s in sg)); print('HAZIR', final, f'{d:.1f} s')
