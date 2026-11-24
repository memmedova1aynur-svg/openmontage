"""U02 v5 · «Moda jurnalı + color blocking» (19.11 agentlik seçdi) — baza: bəzi səhnələrdə {MÜŞTƏRİ} düz rəngli studiya fonunda (insan maskası),
digərlərində real küçə kadrı. Nəticə: esas/base_cb.mp4 (orijinal base.mp4 toxunulmur). python3 cb_u02.py <esas>"""
import sys, os, json, subprocess, numpy as np, cv2
E_ = os.path.abspath(sys.argv[1]); TL = json.load(open(E_ + '/timeline.json')); B = TL['seg_starts']; DUR = TL['dur']
hx = lambda h: np.array([int(h[i:i + 2], 16) for i in (5, 3, 1)], np.float32)   # BGR
ULT, LAV, CRM, PNK = '#2515C9', '#D6B9F8', '#F6F1E8', '#FF249B'
# səhnə → studiya fonu (None = real kadr). 0 giriş · 1 menyu · 2 Mişlen · 3 1937 · 4 ətək · 5 təbiət · 6 bəbir · 7 qarderob · 8 link
BG = [None] * 9   # 21.11 agentlik: arxa fon dəyişdirilmir, hər yerdə real kadr   # 19.11 v7: yalnız 3-cü jurnal səhifəsi (kolaj) studiya fonunda; 2-ci rakursda bitki maskaya düşür
W, H = 1080, 1920
seg_of = lambda t: max(i for i, s in enumerate(B) if s <= t + 1e-6)
rng = np.random.default_rng(7); GR = rng.normal(0, 5, (H, W, 1)).astype(np.float32)   # çap dənəsi (sabit)
rd = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', E_ + ('/base_cc.mp4' if os.path.exists(E_ + '/base_cc.mp4') else '/base.mp4'), '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
rm = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', E_ + '/bg/matte.mp4', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], stdout=subprocess.PIPE)
wr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', '30', '-i', '-', '-i', E_ + '/base.mp4',
                       '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '15', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-shortest', E_ + '/base_cb.mp4'], stdin=subprocess.PIPE)
n = 0
while True:
    f = rd.stdout.read(W * H * 3); m = rm.stdout.read(720 * 1280)
    if len(f) < W * H * 3: break
    fr = np.frombuffer(f, np.uint8).reshape(H, W, 3)
    c = BG[seg_of(n / 30)]
    if c is None or len(m) < 720 * 1280:
        wr.stdin.write(fr.tobytes())
    else:
        a = cv2.resize(np.frombuffer(m, np.uint8).reshape(1280, 720), (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32) / 255
        a = np.clip((a - 0.12) / 0.8, 0, 1)                       # kənar halosunu daralt
        a = cv2.GaussianBlur(a, (0, 0), 1.6)[..., None]
        col = hx(c)[None, None, :]
        x = fr.astype(np.float32)
        # kənarda rəng sızması: yarımşəffaf zonada insan pikselini fon rənginə bir az yaxınlaşdır (yumşaq keçid)
        edge = (a * (1 - a)) * 4
        x = x * (1 - 0.25 * edge) + col * 0.25 * edge
        out = x * a + (col + GR) * (1 - a)
        wr.stdin.write(np.clip(out, 0, 255).astype(np.uint8).tobytes())
    n += 1
wr.stdin.close(); wr.wait(); print('base_cb OK', n, 'kadr')
