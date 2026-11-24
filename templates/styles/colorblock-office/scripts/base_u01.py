"""U01 moodboard reklamı — baza kəsim: danışıq səsi fasiləsiz (IMG_3018 0.30→26.13), görüntüdə B-roll əvəzləmələri.
HLG→SDR (hable) + qapalı məkan rəngi (STİL). Çıxış: esas/base.mp4 (1080x1920@30, səs = DFN təmizlənmiş danışıq)."""
import subprocess, sys, os
X = '/tmp/claude-0/-home-user-openmontage/75c47652-31ab-5cc9-b432-aff8ff258064/scratchpad/{musteri}/'
XM = '/home/user/openmontage/instagram-clients/{musteri}/xam/'   # orijinal .mov-lar
O = sys.argv[1]; os.makedirs(O, exist_ok=True)
T0, TEND, PAD = 0.30, 26.13, 3.2
# 19.11 müştəri ({SPİKER}) rəyi: «yaxşı məhsul» deməzdən əvvəl göz çox yumulur → həmin hissə kəsilir (yeni plan 9.433-də başlayır, söz 9.66-da)
CUT = (9.433, 9.62)
EYE = 9.88   # yeni planda göz 9.88-də açılır → «yaxşı»nın ilk 0.26 s-i B-roll (laptop) ilə örtülür, səs davam edir          # danışıq başlanğıcı/sonu, son kart üçün əlavə
# (mənbə, mənbədə başlanğıc, timeline başlanğıcı (danışıq vaxtı), müddət)
# 5-ci sahə: üz mərkəzi (x, 0–1) — danışan seqmentlər 1.25× yaxın kəsilir (QC: başüstü boşluq çox idi); None = B-roll tam kadr
SEG = [('IMG_3018', 0.30, 0.30, 2.65, 0.57), ('IMG_9527', 10.0, 2.95, 2.65, None), ('IMG_3018', 5.60, 5.60, 3.83, 0.57),
       ('IMG_9527', 14.0, 9.43, EYE - CUT[1], None), ('IMG_3018', EYE, 9.43, 2.37 - (EYE - 9.43), 0.40), ('IMG_9528', 76.0, 11.80, 1.40, None), ('IMG_3018', 13.20, 13.20, 2.00, 0.40),
       ('IMG_9528', 20.0, 15.20, 5.10, None), ('IMG_3018', 20.30, 20.30, TEND - 20.30, 0.40)]
Z, Y0 = 1.12, 206   # 18.11 agentlik: «çox yaxından olmasın» (1.25 → 1.12; kadr aşağıya söykənir, başüstü ~0.25–0.33)
LOOK = 'zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,' \
       'eq=contrast=1.09:saturation=1.20:gamma=0.97,cas=0.75'
ins, fc = [], []
import json as _j
# 18.11 agentlik: «rəng korreksiyası, peşəkar görüntü» — hər mənbə üçün color_auto ölçülü düzəlişi (HLG→SDR + ağ balansı + dərinlik)
CA = {f: _j.load(open(X + f'ca_{f}.json'))['vf'] for f in ('IMG_3018', 'IMG_9527', 'IMG_9528')}
for i, (src, ss, _, d, cx) in enumerate(SEG):
    ins += ['-ss', f'{ss}', '-t', f'{d}', '-i', XM + src + '.mov']
    zc = '' if cx is None else f',crop={int(1080 / Z)}:{int(1920 / Z)}:{max(0, min(1080 - int(1080 / Z), int(cx * 1080 - 540 / Z)))}:{Y0},scale=1080:1920'
    fc.append(f'[{i}:v]{CA[src]},scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920{zc},fps=30,setsar=1,trim=duration={d},setpts=PTS-STARTPTS[v{i}]')
fc.append(''.join(f'[v{i}]' for i in range(len(SEG))) + f'concat=n={len(SEG)}:v=1:a=0,tpad=stop_mode=clone:stop_duration={PAD}[v]')
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y'] + ins + ['-filter_complex', ';'.join(fc), '-map', '[v]', '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-pix_fmt', 'yuv420p', O + '/v.mp4'], check=True)
# səs: DFN (STİL) → −14 LUFS
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', XM + 'IMG_3018.mov', '-filter_complex', f'[0:a]atrim={T0}:{CUT[0]},asetpts=PTS-STARTPTS,afade=t=out:st={CUT[0] - T0 - 0.02:.3f}:d=0.02[a0];[0:a]atrim={CUT[1]}:{TEND},asetpts=PTS-STARTPTS,afade=t=in:d=0.02[a1];[a0][a1]concat=n=2:v=0:a=1,aformat=channel_layouts=mono,aresample=48000[a]', '-map', '[a]', O + '/raw.wav'], check=True)
sys.path.insert(0, '/home/user/openmontage/templates/expert-reels/pro')
from audio_pro import load, save, measure, dfn
# DFN 12 dB (18.11 agentlik: «sözün sonu eşidilmir» — 30 dB söz sonlarını yeyirdi)
x = load(O + '/raw.wav'); m = measure(x); y = dfn(x, 12); y = y * 10 ** ((-14 - measure(y)['lufs']) / 20); save(O + '/voice0.wav', y)
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', O + '/voice0.wav', '-af', f'alimiter=limit=0.89:level=disabled,apad=pad_dur={PAD}', O + '/voice.wav'], check=True)
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', O + '/v.mp4', '-i', O + '/voice.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', O + '/base.mp4'], check=True)
for f in ('v.mp4', 'raw.wav', 'voice0.wav'): os.remove(O + '/' + f)
# 18.11 agentlik: «çox sıx kəsmisən» — mənbə (IMG_3018) özü sıx montajlıdır; yapışıq yerlərə nəfəs pauzası (kadr donur, səs sükut, söz sonu yumşaq sönür)
PAUSES = [(9.433, 0.16), (22.48, 0.12), (23.60, 0.15)]   # (mənbə vaxtı, pauza s) · 19.11: 7.02 pauzası çıxarıldı (müştəri: «yığmısan——amma» fasiləsi pis bilinir)
pre = lambda t: t - T0 - ((CUT[1] - CUT[0]) if t >= CUT[1] - 1e-3 else 0)
cuts = [pre(t) for t, _ in PAUSES]; edges = [0] + cuts + [None]; vf, af, ins = [], [], ['-i', O + '/base.mp4']
for k in range(len(edges) - 1):
    a, b = edges[k], edges[k + 1]; tr = f'trim=start={a}' + (f':end={b}' if b else ''); atr = f'atrim=start={a}' + (f':end={b}' if b else '')
    p = PAUSES[k][1] if b else 0
    vf.append(f'[0:v]{tr},setpts=PTS-STARTPTS' + (f',tpad=stop_mode=clone:stop_duration={p}' if p else '') + f'[v{k}]')
    af.append(f'[0:a]{atr},asetpts=PTS-STARTPTS' + (f',afade=t=in:d=0.015' if k else '') + (f',afade=t=out:st={b - a - 0.03:.3f}:d=0.03,apad=pad_dur={p}' if p else '') + f'[a{k}]')
n = len(edges) - 1
fc = ';'.join(vf + af) + ';' + ''.join(f'[v{k}][a{k}]' for k in range(n)) + f'concat=n={n}:v=1:a=1[v][a]'
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y'] + ins + ['-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k', O + '/base_p.mp4'], check=True)
os.replace(O + '/base_p.mp4', O + '/base.mp4'); print('pauzalar əlavə olundu', sum(p for _, p in PAUSES))
print('base ok', m['lufs'], '→ −14')
