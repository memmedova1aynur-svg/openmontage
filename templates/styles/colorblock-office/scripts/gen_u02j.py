"""U02 v7 · «Təbiətdən ilham al» — ƏSL MODA JURNALI (19.11 agentlik rəyi v6-ya: «səhifələr çox tez fırlanır, 3-4 kifayətdir; rəng korreksiyası et,
daha canlı; ağ yerlərə yazılar yaz, moda jurnalına bənzəsin; səhifə ortadan çevrilməsin — üz bölünmüş kimi görünür»).
4 jurnal səhifəsi + arxa üz qabığı, cəmi 4 səhifə çevrilməsi (sol kənar = onurğa, bütöv səhifə çevrilir, üz bölünmür):
  1 ÜZ QABIĞI (0–8.5)  · tam kadr foto, TƏBİƏT başlığı, ardıcıl çıxan cover-line-lar, barkod, keçən lobster
  2 MƏQALƏ (8.5–19.9)  · ağ kağız səhifə, böyük foto, başlıq + iki sütun mətn ({MÜŞTƏRİ}in öz sözləri), kolaj: lentlə yapışdırılmış paltar eskizi
  3 KOLAJ (19.9–32.6)  · kağız faktura, əyik foto (çəhrayı studiya fonu), parça nümunələri danışığa uyğun çıxır, sitat, əl yazısı
  4 SEMİNAR (32.6–37.7)· tədbir səhifəsi, düymə · ARXA ÜZ (37.7–) color-block + kolaj
Baza: base_cc.mp4 (jurnal rəng korreksiyası, grade_vf.txt) → base_cb.mp4 (3-cü səhifədə studiya fonu). python3 gen_u02j.py <esas>"""
import json, os, sys, shutil, subprocess, random
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from u02_art import *
# 21.11 agentlik: bu videoda tünd yaşıl üstün olsun (əvvəlki videolardakı çəhrayı / mavi / neon yaşıl yox)
# 21.11: {MÜŞTƏRİ}in öz rəng lövhəsi (referans/{musteri}_moodboard): zeytun yaşılı + tünd bənövşəyi + püstə
ULT, PNK, NEO, LAV = '#5F6A14', '#582147', '#C9DB73', '#B9D3BE'
RED = '#6B2553'
# variant: A = 3-cü səhifə krem, altyazıda aktiv söz yaşıl (agentlikun seçdiyi) · B = 3-cü səhifə tünd yaşıl, aktiv söz xardal
GV = os.environ.get('U02_VAR', 'A')
P3BG = 'background:url(assets/paper.jpg) center/cover' if GV == 'A' else f'background:url(assets/paper.jpg) center/cover,{ULT};background-blend-mode:multiply'
P3INK, P3T2, P3H2, P3H3 = (INK, RED, RED, ULT) if GV == 'A' else (CRM, NEO, NEO, '#B9D3BE')
CAPBG, CAPFG, PROGC = (ULT, '#fff', ULT) if GV == 'A' else (NEO, INK, NEO)
D = sys.argv[1]; HF = D + '/hf'; A = HF + '/assets'; os.makedirs(A + '/sfx', exist_ok=True); patterns(A)
TLJ = json.load(open(D + '/timeline.json')); DUR = TLJ['dur']; TEND = TLJ['speech_end'] + 0.05; SB = TLJ['seg_starts']
PB = [0, SB[3], SB[5], SB[8]]          # səhifə başlanğıcları (seqment sərhədlərində — cümlə ortasında çevrilmir)
NP = len(PB); FL = 0.8                 # çevrilmə müddəti
W = json.load(open(D + '/words_raw.json'))
FIX = {3: 'ildir', 5: 'qayıda', 9: 'boşqab', 13: 'bil', 14: 'Mişlen', 17: 'menyusudur.', 19: 'deyilmi?', 22: '1937-ci', 25: 'Schiaparelli', 27: 'Dalínin', 32: 'boşqab', 33: 'əvəzinə', 42: 'əskik',
       58: 'il', 59: 'dəb', 60: 'olan', 62: 'bəbir', 66: 'hal-hazırda', 69: 'Bəs', 70: 'sən', 71: 'qarderobunu', 79: 'görürsən?', 88: 'dizayna'}
for i, x in FIX.items(): W[i][2] = x
GROUPS = [[0, 1], [2, 3], [4, 5, 6], [7], [8, 9], [10, 11], [12, 13, 14], [15, 16], [17], [18, 19], [20, 21], [22, 24], [25, 26], [27, 28], [29, 30], [31, 32, 33], [34, 35, 36], [37],
          [38, 39, 40], [41, 42, 43], [44, 45], [46, 47], [48, 49, 50], [51, 52, 53], [54, 55, 56], [57, 58, 59, 60], [62, 63], [64, 65], [66, 68], [69, 70], [71, 72], [73, 74],
          [75, 76], [77, 78], [79], [80, 81, 82], [83, 84], [85, 86, 87], [88, 89], [90, 91]]
t = lambda i: W[i][0]
cap_html, cap_js = '', ''
for k, g in enumerate(GROUPS):
    s0 = t(g[0]) - 0.06; nx = GROUPS[k + 1] if k + 1 < len(GROUPS) else None
    e0 = (t(nx[0]) - 0.06) if nx and t(nx[0]) - W[g[-1]][1] < 0.7 else W[g[-1]][1] + 0.35
    e0 = min(e0, TEND - 0.2)
    cap_html += f'<div class="cap clip" id="k{k}" data-start="{s0:.3f}" data-duration="{e0 - s0:.3f}" data-track-index="8">' + ''.join(f'<span class="w" id="w{k}_{j}">{W[i][2].rstrip(",")}</span>' for j, i in enumerate(g)) + '</div>'
    cap_js += f'tl.fromTo("#k{k}",{{opacity:0,y:12}},{{opacity:1,y:0,duration:0.14,ease:"power2.out"}},{s0:.3f});'
    for j, i in enumerate(g):
        cap_js += f'tl.set("#w{k}_{j}",{{className:"w on"}},{t(i):.3f});'
        cap_js += f'tl.set("#w{k}_{j}",{{className:"w"}},{min(t(g[j + 1]) if j + 1 < len(g) else e0, t(i) + 1.1):.3f});'
T = dict(caf=t(7), mis=t(14), y37=t(22), sch=t(25), xer=t(31), etek=t(36), cef=t(39), tab=t(44), uza=t(48), beb=t(62), tr=t(68), qar=t(71), hey=t(74), bit=t(78), link=t(80), qos=t(84))

# ---------- kolaj materialları
def paper(path, base=(239, 231, 216), seed=3):
    rng = np.random.default_rng(seed); h, w = 1920, 1080
    n = rng.normal(0, 1, (h // 4, w // 4)); n = np.array(Image.fromarray(((n - n.min()) / (n.max() - n.min()) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(2))) / 255.0
    arr = np.stack([np.clip(c + (n - .5) * 12 + rng.normal(0, 5, (h, w)), 0, 255) for c in base], -1)
    im = Image.fromarray(arr.astype(np.uint8)); px = im.load(); rnd = random.Random(seed)
    for _ in range(240):
        x, y, L_, a = rnd.randint(0, w), rnd.randint(0, h), rnd.randint(8, 30), rnd.random() * 6.28
        for s in range(L_):
            xx, yy = int(x + s * np.cos(a)), int(y + s * np.sin(a))
            if 0 <= xx < w and 0 <= yy < h: r, g, b = px[xx, yy]; px[xx, yy] = (r - 16, g - 16, b - 14)
    im.save(path, quality=92)
paper(A + '/paper.jpg'); paper(A + '/paper2.jpg', base=(249, 247, 242), seed=8)
def torn(seed, n=30, amp=2.4):
    r = random.Random(seed); pts = [f'{i * 100 / n:.1f}% {r.uniform(0, amp):.2f}%' for i in range(n + 1)]
    pts += [f'{i * 100 / n:.1f}% {100 - r.uniform(0, amp):.2f}%' for i in range(n, -1, -1)]
    return 'polygon(' + ','.join(pts) + ')'
def pinked(n=12, d=4):
    p = []
    for i in range(n): p += [f'{i * 100 / n:.2f}% 0%', f'{(i + .5) * 100 / n:.2f}% {d}%']
    p.append('100% 0%')
    for i in range(n): p += [f'100% {i * 100 / n:.2f}%', f'{100 - d}% {(i + .5) * 100 / n:.2f}%']
    p.append('100% 100%')
    for i in range(n, 0, -1): p += [f'{i * 100 / n:.2f}% 100%', f'{(i - .5) * 100 / n:.2f}% {100 - d}%']
    p.append('0% 100%')
    for i in range(n, 0, -1): p += [f'0% {i * 100 / n:.2f}%', f'{d}% {(i - .5) * 100 / n:.2f}%']
    return 'polygon(' + ','.join(p) + ')'
PK = pinked()
tape = lambda x, y, w, rot, cls='': f'<i class="tape {cls}" style="left:{x}px;top:{y}px;width:{w}px;transform:rotate({rot}deg)"></i>'
hand = lambda x, y, txt, c, s=64, rot=-3, cls='': f'<div class="hand {cls}" style="left:{x}px;top:{y}px;color:{c};font-size:{s}px;transform:rotate({rot}deg)">{txt}</div>'
swatch = lambda x, y, w, h, img, sz, rot, cls='': f'<div class="swt {cls}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;transform:rotate({rot}deg)"><div style="position:absolute;inset:0;clip-path:{PK};background:url(assets/{img}) center/{sz}px"></div></div>'
def LOBL(w, c, sw=3):
    return (f'<svg viewBox="0 0 200 120" width="{w}" style="overflow:visible"><g fill="none" stroke="{c}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">'
            '<ellipse cx="100" cy="60" rx="34" ry="18"/><path d="M134 60 q14 -2 22 6 q8 8 22 4 M66 56 q-20 -10 -34 -30 q-6 -10 -18 -8 q10 4 8 14 M66 64 q-20 10 -34 30 q-6 10 -18 8 q10 -4 8 -14"/>'
            '<path d="M84 76 l-6 18 M96 78 l-2 20 M108 78 l2 20 M120 76 l6 18 M70 48 q-10 -30 -40 -40 M74 46 q0 -30 -20 -46"/></g></svg>')
def LEAF(w, c, sw=3):   # 21.11: son kadrda xərçəng əvəzinə tək yarpaq (cizgi)
    return (f'<svg viewBox="0 0 200 200" width="{w}" style="overflow:visible"><g transform="rotate(24 100 100)" fill="none" stroke="{c}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M100 178 C34 146 34 62 100 14 C166 62 166 146 100 178 Z"/><path d="M100 196 L100 34"/>'
            '<path d="M100 150 L72 128 M100 150 L128 128 M100 118 L66 92 M100 118 L134 92 M100 86 L76 66 M100 86 L124 66"/></g></svg>')
def DRL(w, c, lc, lob=True):
    return (f'<svg viewBox="0 0 100 160" width="{w}" style="overflow:visible"><g fill="none" stroke="{c}" stroke-width="1.6" stroke-linejoin="round" class="drp">'
            '<path d="M38 8 q12 8 24 0 l4 26 h-32 z"/><path d="M34 34 q-22 60 -30 120 q46 8 92 0 q-8 -60 -30 -120 z"/></g>'
            + (f'<g transform="translate(36 92) scale(.2)">{LOBL(200, lc, 6)}</g>'
               f'<g fill="none" stroke="#3DBB5A" stroke-width="1.4" stroke-linecap="round"><path d="M24 128 q4 -8 10 -6 M28 134 q-6 -6 -2 -12 M70 130 q4 -8 10 -4 M74 136 q-6 -4 -2 -10"/></g>' if lob else '') + '</svg>')
rb = random.Random(9); bars = ''; x = 0
while x < 220:
    w_ = rb.choice([2, 2, 3, 4, 6]); bars += f'<rect x="{x}" y="0" width="{w_}" height="90" fill="#111"/>'; x += w_ + rb.choice([2, 3, 4])
BARCODE = f'<div class="bc"><svg width="230" height="90">{bars}</svg><span>9 771234 567002</span></div>'

# ---------- səhifələr
PAPER2 = 'background:url(assets/paper2.jpg) center/cover'; PAPER = 'background:url(assets/paper.jpg) center/cover'
def frame(win, rot, pad=22):
    a, r, b_, lf = win; x0, y0, x1, y1 = lf - pad, a - pad, 1080 - r + pad, 1920 - b_ + pad
    return f'<div class="pf" style="left:{x0}px;top:{y0}px;width:{x1 - x0}px;height:{y1 - y0}px;transform:rotate({rot}deg);transform-origin:{(lf + 1080 - r) / 2 - x0}px {(a + 1920 - b_) / 2 - y0}px"></div>'
BODY1 = ('<span class="dc">E</span>lə bil Mişlen ulduzlu restoranın menyusudur: cəfəri, ağ boşqab və xərçəng. Elə deyilmi? Amma bu, 1937-ci ildə '
         'Schiaparelli ilə Dalínin yaratdığı bir paltardır. <span class="mk" id="mk1">Xərçəngi boşqab əvəzinə ağ paltarın ətəyinə yerləşdirirlər</span> '
         'və <span class="mk g" id="mk2">cəfərini də heç əskik etmirlər.</span>')
P = [
 dict(win=(0, 0, 0, 0), vx=0, vy=0, rot=0, cap=(1190, 60, 960), back='', html=f'''
  <div class="blk" style="left:0;top:0;width:1080px;height:520px;background:linear-gradient(180deg,rgba(16,12,28,.5),rgba(16,12,28,0))"></div>
  <div class="blk" style="left:0;top:1300px;width:1080px;height:620px;background:linear-gradient(0deg,rgba(16,12,28,.72),rgba(16,12,28,0))"></div>
  <span class="mo rv" style="left:56px;top:46px;color:#fff">{BREND} · MODA &amp; DİZAYN</span><span class="mo rv" style="right:56px;top:46px;color:#fff">№02</span>
  <div class="mast rv" style="top:78px;color:#fff">TƏBİƏT</div>
  <div class="cl lt" id="cl1" style="right:56px;top:330px;text-align:right"><b>cəfəri,</b><br><i>ağ boşqab</i><br>və xərçəng</div>
  <div class="cl lt" id="cl2" style="left:56px;top:330px"><b style="color:{NEO}">★★★</b><br><i>Mişlen</i><br>menyusu?</div>
  <span class="mo rv" style="left:56px;top:1440px;color:{NEO}">1937 → 2026</span>
  <div class="ser rv" style="left:56px;top:1480px;color:#fff;font-size:96px;text-shadow:0 4px 24px rgba(0,0,0,.35)"><i>89 il</i></div>
  <div class="ser rv" style="left:56px;top:1580px;color:#fff;font:700 70px/1.05 PlayB;text-shadow:0 4px 24px rgba(0,0,0,.35)">dənizə qayıtmayan<br>xərçəng</div>
  <div class="rv" style="position:absolute;right:56px;top:1700px">{BARCODE}</div>'''),
 dict(win=(56, 56, 760, 56), vx=30, vy=-348, sc=1.12, rot=0, cap=(1050, 90, 640), back=f'<div class="blk" style="inset:0;{PAPER2}"></div>', html=f'''
  <div class="torn lt" id="sk" style="left:745px;top:860px;width:300px;height:400px;transform:rotate(5deg);clip-path:{torn(11)};background:{ULT}"></div>
  <div class="lt" id="skd" style="position:absolute;left:793px;top:872px;width:204px;height:376px;transform:rotate(5deg)"><img src="assets/paltar.png" style="width:100%;height:100%;object-fit:contain;filter:drop-shadow(0 10px 16px rgba(0,0,0,.4))"></div>
  <div class="torn lt" id="lbc" style="left:806px;top:1622px;width:218px;height:250px;transform:rotate(-5deg);clip-path:{torn(5)}"></div>
  <div class="lt" id="lb2" style="position:absolute;left:816px;top:1630px;width:198px;height:234px;transform:rotate(-5deg);background:url(assets/xerceng.jpg) 50% 44%/136% auto no-repeat;mix-blend-mode:multiply"></div>
  <div class="lt" id="skt">{tape(820, 840, 140, -6)}</div>
  {hand(470, 1166, 'xərçəng ✓ →', RED, 52, -3, 'lt" id="h1')}{hand(880, 1338, 'cəfəri ✓', ULT, 50, -3, 'lt" id="h2')}
  <span class="mo" style="left:56px;top:1200px;color:{RED}">ARXİV · 1937 · PARİS</span>
  <div class="ser" style="left:56px;top:1240px;color:{INK};font:700 92px/1 PlayB">Schiaparelli × Dalí</div>
  <div class="ser" style="left:58px;top:1350px;color:{INK};font-size:44px">ağ axşam paltarı, ətəyində xərçəng</div>
  <div class="rule" style="left:56px;top:1425px;width:968px;background:{INK}"></div>
  <div class="body2">{BODY1}</div>
  <span class="mo" style="left:56px;top:1868px;color:{INK};font-size:20px">TƏBİƏT — №02</span><span class="mo" style="right:56px;top:1868px;color:{INK};font-size:20px">24</span>'''),
 dict(win=(300, 50, 540, 330), vx=145, vy=-50, rot=2.5, cap=(1420, 330, 700), back=f'<div class="blk" style="inset:0;{P3BG}"></div>', html=f'''
  <div class="ser" style="left:46px;top:30px;color:{P3INK};font-size:118px"><i>Təbiətdən</i></div>
  <div class="ser" style="left:610px;top:140px;color:{P3T2};font:700 96px/1 PlayB">ilham al</div>
  {tape(380, 268, 170, -10)}{tape(890, 292, 150, 14)}
  <span class="mo" style="left:46px;top:300px;color:{P3INK}">TREND / 2026</span>
  {swatch(40, 360, 250, 250, 'bebir.jpg', 230, -6, 'lt" id="sw1')}<i class="pin lt" id="pn1" style="left:150px;top:350px"></i>
  {hand(46, 625, 'bəbir printi', P3INK, 62, -4, 'lt" id="hb')}<span class="mo lt" id="hb2" style="left:52px;top:705px;color:#fff;background:{PNK};padding:8px 12px">bu ilin trendi</span>
  {swatch(60, 800, 200, 200, 'zebra.svg', 120, 7, 'lt" id="sw2')}{hand(60, 1010, 'hansı heyvan?', P3H2, 54, -3, 'lt" id="hh')}
  <img class="swt lt" id="sw3" src="assets/st_puste.png" style="left:40px;top:1060px;width:250px;transform:rotate(-6deg)"><img class="swt lt" id="lf1" src="assets/st_monstera.png" style="left:-120px;top:1560px;width:360px;transform:rotate(-14deg)"><img class="swt lt" id="lf2" src="assets/st_yarpaq.png" style="left:880px;top:1150px;width:250px;transform:rotate(-28deg)">{hand(60, 1290, 'hansı bitki?', P3H3, 54, -2, 'lt" id="hp')}
  <div class="qt lt" id="qt" style="color:{P3INK}"><span>“</span>Uzağa heç də getmək lazım deyil.</div>
  {hand(600, 1810, 'qarderobunu aç ↗', P3H2, 60, -4, 'lt" id="hq')}
  <span class="mo" style="left:46px;top:1868px;color:{P3INK};font-size:20px">37</span>'''),
 dict(win=(90, 90, 700, 90), vx=0, vy=-336, sc=1.12, rot=0, cap=(1040, 120, 840), back=f'<div class="blk" style="inset:0;{PAPER2}"></div>', html=f'''
  {tape(40, 60, 170, -30)}{tape(880, 60, 170, 30)}
  <span class="mo" style="left:90px;top:1262px;color:{RED}">SEMİNAR · {SPİKER_ADI}</span>
  <div class="ser" style="left:90px;top:1310px;color:{INK};font-size:112px"><i>Təbiətdən</i></div>
  <div class="ser" style="left:90px;top:1420px;color:{INK};font:700 112px/1 PlayB">ilham al</div>
  <span class="mo" style="left:90px;top:1560px;color:{INK};font-size:30px">11 DEKABR · ÖDƏNİŞSİZ · {BREND}</span>
  <div class="btnx" style="left:90px;top:1640px">QEYDİYYAT — LİNKDƏ ↗</div>
  <span class="mo" style="right:90px;top:1868px;color:{INK};font-size:20px">52</span>'''),
]
for p in P:
    if p['back']: p['back'] += frame(p['win'], p['rot'], 22)
wc = lambda p: ((p['win'][3] + 1080 - p['win'][1]) / 2, (p['win'][0] + 1920 - p['win'][2]) / 2)
TR = PB[1:] + [TEND]
for k, t1 in enumerate(TR, 1):
    if k < NP: subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t1 - 0.14:.3f}', '-i', D + '/base_cb.mp4', '-frames:v', '1', '-q:v', '2', f'{A}/st{k}.jpg'], check=True)

css = f'''
@font-face {{ font-family:"Arc"; src:url("assets/Archivo.ttf"); font-weight:100 900; font-stretch:62% 125%; }}
@font-face {{ font-family:"Mono"; src:url("assets/SpaceMono-Bold.ttf"); }} @font-face {{ font-family:"PlayI"; src:url("assets/PlayI.ttf"); }}
@font-face {{ font-family:"PlayB"; src:url("assets/PlayB.ttf"); }} @font-face {{ font-family:"PlayR"; src:url("assets/PlayR.ttf"); }} @font-face {{ font-family:"Cav"; src:url("assets/Caveat.ttf"); }}
* {{ margin:0; padding:0; box-sizing:border-box; }} html, body {{ width:1080px; height:1920px; overflow:hidden; background:{INK}; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:{INK}; }}
#stage {{ position:absolute; inset:0; perspective:5200px; perspective-origin:0 960px; }}
#page {{ position:absolute; inset:0; z-index:5; background:{CRM}; transform-origin:0 50%; overflow:hidden; }}
#vwin {{ position:absolute; inset:0; z-index:1; overflow:hidden; }} #vbox {{ position:absolute; left:0; top:0; width:1080px; height:1920px; transform-origin:540px 820px; }}
#vbox video {{ position:absolute; left:0; top:0; width:1080px; height:1920px; }}
.bkl {{ position:absolute; inset:0; z-index:0; visibility:hidden; }} .sc {{ position:absolute; inset:0; z-index:4; visibility:hidden; }} .blk {{ position:absolute; }}
.cp {{ position:absolute; inset:0; z-index:2; visibility:hidden; background:{CRM}; overflow:hidden; isolation:isolate; transform-origin:0 50%; }} .cp .sc, .cp .bkl, .cp .lt {{ visibility:inherit; }}
.cp .mk {{ background-size:100% 42%; }} .cp #u_qt {{ display:none; }}
.cp .gsh {{ position:absolute; inset:0; z-index:60; pointer-events:none; opacity:0; background:linear-gradient(90deg,rgba(16,12,28,0) 0%,rgba(255,255,255,.10) 50%,rgba(16,12,28,.42) 100%); }}
.uwin {{ position:absolute; inset:0; z-index:1; overflow:hidden; }} .uwin img {{ position:absolute; left:0; top:0; width:1080px; height:1920px; }}
#ush {{ position:absolute; inset:0; z-index:9; visibility:hidden; pointer-events:none; opacity:0; background:linear-gradient(90deg,rgba(16,12,28,.6),rgba(16,12,28,.2) 35%,rgba(16,12,28,0) 70%); }}
#psh {{ position:absolute; inset:0; z-index:60; pointer-events:none; opacity:0; background:linear-gradient(90deg,rgba(16,12,28,0) 0%,rgba(255,255,255,.10) 50%,rgba(16,12,28,.42) 100%); }}
#pedge {{ position:absolute; top:0; right:0; width:14px; height:1920px; z-index:61; opacity:0; background:linear-gradient(90deg,rgba(255,255,255,0),rgba(255,255,255,.9)); }}
.mast {{ position:absolute; left:0; right:0; text-align:center; font:700 230px/1 "PlayB"; letter-spacing:.03em; text-shadow:0 6px 34px rgba(0,0,0,.25); }}
.ser {{ position:absolute; font:600 80px/1.05 "PlayI"; white-space:nowrap; }} .ser i {{ font-family:"PlayI"; font-style:normal; }}
.mo {{ position:absolute; font:24px/1.25 "Mono"; letter-spacing:.12em; white-space:nowrap; }} .rule {{ position:absolute; height:3px; }}
.cl {{ position:absolute; color:#fff; font:700 54px/1.02 "PlayB"; text-shadow:0 3px 18px rgba(0,0,0,.45); }} .cl i {{ font:600 54px/1.02 "PlayI"; font-style:normal; }}
.bc {{ background:#fff; padding:10px 12px 6px; }} .bc span {{ display:block; font:16px "Mono"; color:#111; text-align:center; letter-spacing:.2em; }}
.body2 {{ position:absolute; left:56px; top:1450px; width:968px; height:400px; column-count:2; column-gap:44px; font:30px/1.42 "PlayR"; color:#222; text-align:left; }}
.body2 .dc {{ float:left; font:700 112px/0.85 "PlayB"; color:{RED}; margin:8px 10px 0 0; }}
.mk {{ background-image:linear-gradient({NEO},{NEO}); background-repeat:no-repeat; background-position:0 88%; background-size:0% 42%; }} .mk.g {{ background-image:linear-gradient(#D9B8CC,#D9B8CC); }}
.qt {{ position:absolute; left:330px; top:1560px; width:700px; font:600 62px/1.15 "PlayI"; color:{INK}; }} .qt span {{ position:absolute; left:-70px; top:-30px; font:700 170px/1 "PlayB"; color:{PNK}; }}
.btnx {{ position:absolute; padding:34px 56px 30px; border-radius:80px; background:{ULT}; color:#fff; font:800 56px/1 "Arc"; font-stretch:104%; white-space:nowrap; box-shadow:0 14px 26px rgba(60,70,10,.3); }}
.pf {{ position:absolute; background:#fff; box-shadow:0 22px 40px rgba(40,30,20,.30), 0 2px 4px rgba(40,30,20,.18); }}
.tape {{ position:absolute; height:52px; z-index:3; background:rgba(250,236,190,.8); box-shadow:0 2px 4px rgba(0,0,0,.12); clip-path:polygon(0 8%,4% 0,8% 10%,12% 0,100% 0,96% 12%,100% 24%,96% 40%,100% 58%,96% 76%,100% 100%,0 100%,4% 84%,0 66%,4% 48%,0 30%); }}
.hand {{ position:absolute; font-family:"Cav"; line-height:1; white-space:nowrap; }}
.torn {{ position:absolute; background:#fff; box-shadow:0 14px 24px rgba(40,30,20,.28); }}
.swt {{ position:absolute; filter:drop-shadow(0 12px 14px rgba(40,30,20,.35)); }}
.pin {{ position:absolute; width:40px; height:40px; border-radius:50%; background:{PNK}; box-shadow:2px 6px 8px rgba(0,0,0,.4); z-index:3; }}
#capbox {{ position:absolute; z-index:9; }}
.cap {{ position:absolute; left:0; top:0; width:100%; display:flex; flex-wrap:wrap; justify-content:center; gap:10px 10px; font:800 54px/1 "Arc"; font-stretch:102%; }}
.cap .w {{ padding:11px 15px 7px; background:{CRM}; color:{INK}; box-shadow:0 6px 16px rgba(16,12,28,.22); }}
.cap .w.on {{ background:{CAPBG}; color:{CAPFG}; }}
#rlob {{ position:absolute; left:0; top:1500px; z-index:6; opacity:0; pointer-events:none; }}
#end {{ position:absolute; inset:0; z-index:2; {PAPER2}; visibility:hidden; }} #end .x {{ position:absolute; }}
#prog {{ position:absolute; left:0; top:1910px; width:1080px; height:10px; z-index:80; background:rgba(16,12,28,.15); }} #prog b {{ display:block; height:100%; width:100%; background:{PROGC}; transform-origin:0 50%; transform:scaleX(0); }}
'''
def win_style(p):
    a, r, b_, lf = p['win']; cx, cy = wc(p)
    return f'clip-path:inset({a}px {r}px {b_}px {lf}px);transform:rotate({p["rot"]}deg);transform-origin:{cx}px {cy}px'
uid = lambda s: s.replace(' id="', ' id="u_')
ENDH = f'''
  <div class="x" style="left:0;top:0;width:620px;height:900px;background:{ULT}"></div>
  <div class="x" style="left:620px;top:0;width:460px;height:520px;background:{PNK}"></div>
  <div class="x" style="left:620px;top:520px;width:460px;height:380px;background:{NEO}"></div>
  <div class="x" style="left:110px;top:150px">{DRL(400, '#fff', '#fff', lob=False)}</div>
  <div class="x" style="left:720px;top:110px">{LEAF(290, '#fff', 4)}</div>
  <div class="x mo" style="left:670px;top:575px;color:{INK};font-size:30px">SAAT</div><div class="x ser" style="left:664px;top:615px;color:{INK};font:700 104px/1 PlayB">15:00</div>
  <img class="x swt" src="assets/st_puste.png" style="position:absolute;left:800px;top:730px;width:270px;transform:rotate(9deg)">
  <div class="x ser" style="left:70px;top:990px;color:{INK};font-size:150px"><i>Təbiətdən</i></div>
  <div class="x ser" style="left:70px;top:1150px;color:{INK};font:700 150px/1 PlayB">ilham al</div>
  <div class="x rule" style="left:74px;top:1350px;width:932px;background:{INK}"></div>
  <div class="x mo" style="left:74px;top:1390px;color:{INK};font-size:34px">{SPİKER_ADI} · SEMİNAR</div>
  <div class="x ser" style="left:70px;top:1470px;color:{ULT};font:700 120px/1 PlayB">11 dekabr</div>
  <div class="x mo" style="left:74px;top:1640px;color:#fff;background:{PNK};padding:14px 20px;font-size:34px">ÖDƏNİŞSİZ · QEYDİYYAT LİNKDƏ ↗</div>
  {hand(640, 1740, 'görüşənədək!', RED, 80, -5)}'''
backs = ''.join(f'<div class="bkl" id="bk{k}">{p["back"]}</div>' for k, p in enumerate(P))
scenes = ''.join(f'<div class="sc" id="sc{k}">{p["html"]}</div>' for k, p in enumerate(P))
copies = ''.join(f'<div class="cp" id="cp{k}"><div class="bkl">{uid(P[k-1]["back"])}</div><div class="uwin" style="{win_style(P[k-1])}"><img src="assets/st{k}.jpg" style="transform-origin:540px 820px;transform:translate({P[k-1]["vx"]}px,{P[k-1]["vy"]}px) scale({P[k-1].get("sc",1)*1.04:.4f})"></div><div class="sc">{uid(P[k-1]["html"])}</div><div class="gsh"></div></div>' for k in range(1, NP))
body = f'''
<div id="stage">
{copies}
<div id="end" class="clip" data-start="{TEND - FL - 0.02:.3f}" data-duration="{DUR - TEND + FL + 0.02:.3f}" data-track-index="25">{ENDH}</div>
<div id="ush"></div>
<div id="page">
 {backs}
 <div id="vwin"><div id="vbox"><video id="v0" class="clip" src="assets/base.mp4" data-start="0" data-duration="{DUR:.3f}" data-has-audio="true" data-track-index="0"></video></div></div>
 {scenes}
 <div id="rlob"><div style="position:absolute;left:100px;top:160px;width:380px;height:30px;border-radius:50%;background:radial-gradient(ellipse at center,rgba(0,0,0,.35),rgba(0,0,0,0) 70%)"></div><div id="rlobi" style="transform-origin:50% 90%">{lobster_walk(400, "lw")}</div></div>
 <div id="capbox">{cap_html}</div>
 <div id="psh"></div><div id="pedge"></div>
</div>
</div>
<div id="prog"><b></b></div>
'''
js = [f'tl.to("#prog b",{{scaleX:1,duration:{DUR:.3f},ease:"none"}},0);tl.set("#ush",{{opacity:0}},0);']
GH = 0.10
def flip(k, t1):
    """21.11: köhnə səhifənin dondurulmuş nüsxəsi (ghost) sol kənar ətrafında çevrilib gedir; altında YENİ səhifə artıq canlıdır ({MÜŞTƏRİ} danışır).
    Son keçiddə (son kadr) əvvəlki kimi canlı səhifə çevrilir."""
    if k < NP:
        g = f'#cp{k}'; t1 = t1 - GH      # kadr kəsimi səhifə sərhədindən 1–2 kadr əvvəl düşür: ghost bir az tez örtür
        return (f'tl.set("{g}",{{visibility:"visible",rotationY:0,zIndex:10}},{t1:.3f});'
                f'tl.to("{g}",{{rotationY:-92,duration:{FL},ease:"power2.inOut"}},{t1:.3f});'
                f'tl.fromTo("{g} .gsh",{{opacity:0}},{{opacity:1,duration:{FL},ease:"power1.in",immediateRender:false}},{t1:.3f});'
                f'tl.set("#ush",{{visibility:"visible"}},{t1:.3f});tl.fromTo("#ush",{{opacity:0.85}},{{opacity:0,duration:{FL},ease:"power1.in",immediateRender:false}},{t1:.3f});'
                f'tl.set("{g}",{{visibility:"hidden",zIndex:2}},{t1 + FL + 0.02:.3f});tl.set("#ush",{{opacity:0,visibility:"hidden"}},{t1 + FL + 0.02:.3f});')
    t0 = t1 - FL
    return (f'tl.set("#end",{{visibility:"visible"}},{t0:.3f});'
            f'tl.fromTo("#page",{{rotationY:0}},{{rotationY:-92,duration:{FL},ease:"power2.inOut"}},{t0:.3f});'
            f'tl.fromTo("#psh",{{opacity:0}},{{opacity:1,duration:{FL},ease:"power1.in"}},{t0:.3f});'
            f'tl.fromTo("#pedge",{{opacity:0}},{{opacity:1,duration:{FL * 0.6},ease:"power1.in"}},{t0:.3f});'
            f'tl.set("#page",{{visibility:"hidden"}},{t1:.3f});')
for k, p in enumerate(P):
    t0 = PB[k]; t1 = PB[k + 1] if k + 1 < NP else TEND
    a, r, b_, lf = p['win']; cy, cx, cw = p['cap']; wx, wy = wc(p)
    js.append(f'tl.set("#vwin",{{clipPath:"inset({a}px {r}px {b_}px {lf}px)",rotation:{p["rot"]},transformOrigin:"{wx}px {wy}px"}},{t0:.3f});'
              f'tl.set("#vbox",{{x:{p["vx"]},y:{p["vy"]},scale:{p.get("sc",1)}}},{t0:.3f});'
              f'tl.to("#vbox",{{scale:{p.get("sc",1)*1.04:.4f},duration:{t1 - t0:.3f},ease:"sine.inOut"}},{t0:.3f});'
              f'tl.set("#capbox",{{top:{cy},left:{cx},width:{cw}}},{t0:.3f});'
              f'tl.set(["#sc{k}","#bk{k}"],{{visibility:"visible"}},{t0:.3f});tl.set(["#sc{k}","#bk{k}"],{{visibility:"hidden"}},{t1 + 0.01:.3f});'
              f'tl.set("#sc{k} .lt",{{opacity:0}},{t0:.3f});')
    js.append(flip(k + 1, t1))
pop = lambda sel, at, y=30: f'tl.fromTo("{sel}",{{opacity:0,y:{y}}},{{opacity:1,y:0,duration:0.45,ease:"power3.out"}},{at:.3f});'
drop = lambda sel, at, r=-14: f'tl.fromTo("{sel}",{{opacity:0,scale:1.25,rotation:"+={r}"}},{{opacity:1,scale:1,rotation:"-={r}",duration:0.4,ease:"back.out(1.6)"}},{at:.3f});'
js.append(f'''
tl.fromTo("#sc0 .rv",{{opacity:0,y:40}},{{opacity:1,y:0,duration:0.5,ease:"power3.out",stagger:0.08}},0.15);
tl.fromTo("#sc0 .mast",{{letterSpacing:"0.25em"}},{{letterSpacing:"0.03em",duration:1.3,ease:"power3.out"}},0.15);
{pop('#cl1', T['caf'] - 0.1)} {pop('#cl2', T['mis'] - 0.15)}
{lobster_walk_js("lw", 0.05, 2.5)}
tl.set("#rlob",{{opacity:1,x:1120}},0); tl.to("#rlob",{{x:620,duration:0.9,ease:"power1.out"}},0.05); tl.to("#rlob",{{x:560,duration:0.35,ease:"sine.inOut"}},1.0);
tl.to("#rlob",{{x:-760,duration:1.1,ease:"power2.in"}},1.4); tl.to("#rlobi",{{y:-6,rotation:-1.3,duration:0.09,yoyo:true,repeat:11,ease:"sine.inOut"}},0.05);
tl.to("#rlobi",{{y:-7,rotation:-1.5,duration:0.08,yoyo:true,repeat:13,ease:"sine.inOut"}},1.4); tl.set("#rlob",{{opacity:0}},2.5);
{drop('#sk', T['y37'] - 0.1)} {drop('#skt', T['y37'] + 0.15, 6)}
tl.fromTo("#skd",{{opacity:0}},{{opacity:1,duration:0.1}},{T['y37'] + 0.1:.3f});
tl.fromTo("#skd",{{scale:1.12}},{{scale:1,duration:0.5,ease:"back.out(1.5)"}},{T['y37'] + 0.1:.3f});
tl.to("#mk1",{{backgroundSize:"100% 42%",duration:1.6,ease:"none"}},{T['xer']:.3f}); {drop('#lbc', T['xer'] - 0.1, 8)} tl.fromTo("#lb2",{{opacity:0,scale:1.15}},{{opacity:1,scale:1,duration:0.4,ease:"back.out(1.6)"}},{T['xer'] - 0.05:.3f}); {pop('#h1', T['etek'] - 0.1, 10)}
tl.to("#mk2",{{backgroundSize:"100% 42%",duration:1.0,ease:"none"}},{T['cef']:.3f}); {pop('#h2', T['cef'], 10)}
{drop('#sw1', T['beb'] - 0.25)} {drop('#pn1', T['beb'] - 0.05, 0)} {pop('#hb', T['beb'] + 0.2, 10)} {pop('#hb2', T['tr'] - 0.2, 10)}
{pop('#qt', T['uza'] - 0.1)}
tl.to("#qt",{{opacity:0,duration:0.3}},{T['qar'] - 0.6:.3f}); {pop('#hq', T['qar'] - 0.1, 10)}
{drop('#sw2', T['hey'] - 0.2, 10)} {pop('#hh', T['hey'] + 0.1, 10)} {drop('#sw3', T['bit'] - 0.2, -10)} {drop('#lf1', T['tab'] + 0.05, -16)} {drop('#lf2', T['tab'] + 0.3, 14)} {pop('#hp', T['bit'] + 0.1, 10)}
tl.to("#sc3 .btnx",{{scale:0.94,duration:0.1,yoyo:true,repeat:1}},{T['qos']:.3f}); tl.to("#sc3 .btnx",{{backgroundColor:"{PNK}",duration:0.15}},{T['qos'] + 0.1:.3f});
tl.set("#end",{{visibility:"visible"}},{TEND - FL:.3f});
{cap_js}''')
SFX = [(0.0, 'sea_waves.wav', .42), (0.1, 'p_tap.wav', .06), (0.45, 'p_tap.wav', .06), (1.5, 'p_tap.wav', .06), (1.85, 'p_tap.wav', .06), (0.2, 'pro_paper.wav', .16), (T['tab'] - 0.15, 'forest_birds_6s.wav', .62)]
for t1 in TR:
    f0 = t1 - FL if t1 == TEND else t1 - 0.10
    SFX += [(f0, 'pro_paper.wav', .3), (f0 + 0.3, 'pro_air.wav', .12)]
SFX += [(T['caf'] - 0.1, 'softclick.wav', .1), (T['mis'] - 0.15, 'softclick.wav', .1), (T['y37'] - 0.1, 'snip.wav', .12), (T['xer'], 'pro_tick.wav', .08),
        (T['beb'] - 0.25, 'snip.wav', .12), (T['hey'] - 0.2, 'snip.wav', .1), (T['bit'] - 0.2, 'snip.wav', .1), (T['qos'], 'softclick.wav', .25), (TEND + 0.4, 'chime.wav', .2)]
sfx_html = ''
for i, (tt, f, v) in enumerate(SFX):
    shutil.copy(f'/root/montaj-data/sfx/{f}', f'{A}/sfx/{f}')
    sfx_html += f'<audio id="sfx{i}" class="clip" src="assets/sfx/{f}" data-start="{max(0, tt):.3f}" data-duration="{3.8 if f.startswith("sea") else 1.0}" data-volume="{v}" data-track-index="{40 + i}"></audio>'
json.dump([[round(max(0, tt), 3), f, v] for tt, f, v in SFX], open(D + '/sfx.json', 'w'))
json.dump([[round((t1 - FL if t1 == TEND else t1 - 0.10) - 0.02, 2), round((t1 if t1 == TEND else t1 + FL) + 0.04, 2)] for t1 in TR], open(D + '/flips.json', 'w'))   # QC: keçid pəncərələri
shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'referans', 'xerceng_illustrasiya.jpg'), A + '/xerceng.jpg'); shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'referans', 'paltar_xerceng_kesim.png'), A + '/paltar.png'); shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'referans', 'bebir_xez.jpg'), A + '/bebir.jpg'); shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'referans', 'puste.jpg'), A + '/puste.jpg'); [shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'referans', 'stiker', a), A + '/st_' + b) for a, b in (('puste.png', 'puste.png'), ('monstera.png', 'monstera.png'), ('yarpaq1.png', 'yarpaq.png'))]; shutil.copy(D + '/base_cb.mp4', A + '/base.mp4'); shutil.copy('/root/montaj-data/music_mixkit/curiosity.mp3', A + '/music.mp3')
F = '/root/.fonts/ayra/'
shutil.copy('/root/.fonts/{musteri}/Archivo.ttf', A); shutil.copy('/root/.fonts/{musteri}/SpaceMono-Bold.ttf', A); shutil.copy(F + 'Caveat-500.ttf', A + '/Caveat.ttf')
shutil.copy(F + 'PlayfairDisplay-italic-600.ttf', A + '/PlayI.ttf'); shutil.copy(F + 'PlayfairDisplay-700.ttf', A + '/PlayB.ttf'); shutil.copy(F + 'PlayfairDisplay-400.ttf', A + '/PlayR.ttf')
mus = f'<audio id="mus" class="clip" src="assets/music.mp3" data-start="0" data-duration="{DUR:.3f}" data-volume="0.11" data-fade-in="0.5" data-fade-out="1.5" data-track-index="30"></audio>'
JS = '\n'.join(js)
def page(extra='', audio=mus + sfx_html):
    return f'''<!DOCTYPE html><html lang="az"><head><meta charset="UTF-8"><meta name="viewport" content="width=1080, height=1920">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script><style>{css}{extra}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{DUR:.3f}" data-width="1080" data-height="1920">{body}{audio}</div>
<script>window.__timelines = window.__timelines || {{}}; const tl = gsap.timeline({{ paused: true }});
{JS}
window.__timelines["main"] = tl; tl.seek(0);</script></body></html>'''
open(HF + '/index.html', 'w', encoding='utf-8').write(page())
CL = HF + '_clean'
for d_, nm in ((HF, 'hf'), (CL, 'hf_clean')):
    os.makedirs(d_, exist_ok=True); json.dump({'name': nm, 'private': True, 'type': 'module'}, open(d_ + '/package.json', 'w')); json.dump({'id': nm, 'name': nm}, open(d_ + '/meta.json', 'w'))
if not os.path.exists(CL + '/assets'): os.symlink(os.path.abspath(A), CL + '/assets')
# təmiz (QC): eyni pəncərə həndəsəsi, qrafika yoxdur
open(CL + '/index.html', 'w', encoding='utf-8').write(page('#stage > *:not(#page) { visibility:hidden !important; } #page > *:not(#vwin) { display:none !important; } #page { visibility:visible !important; } #prog { display:none; }', ''))
print('U02j OK', DUR, 'səhifələr', PB, 'çevrilmə', [round(x, 2) for x in TR])
