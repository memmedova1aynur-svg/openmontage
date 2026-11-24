"""U01 · C «PİNTEREST → BENTO» — yuxarıda sonsuz Pinterest skrolu + sayğac, «alınmır» anında STOP; sonra ekran 2×2 rəng blokuna
(bento) bölünür, hər söz bir xana; CTA neon düymə + kursor; son kadr bento-kolaj.  python3 gen_u01_C.py <esas_qovluğu>"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from u01_common import *
D = sys.argv[1]
t_cox, t_hec, t_bil = at('çoxlu'), at('heç'), at('bilmirsən')
t_ilh, t_tek, t_ren, t_tar = at('ilham'), at('tekstura'), at('rənglər'), at('tarazlıq')
t_lin, t_sem, t_qos = at('linkə'), at('seminarımıza'), at('qoşula')
T_FULL = bt(9.433)          # mənbədə kamera keçidi — burada video tam ekrana açılır
T_BENTO = t_ilh - 0.55

def top_of(t):
    if t < T_FULL: return 1520
    if t < B[5]: return 1420
    if t >= B[6] - 0.1: return 1215
    return 1420
cap_html, cap_js = captions(top_of)
cap_js += f'tl.to("#k10",{{opacity:0,duration:0.12}},{T_BENTO - 0.12:.3f});'   # «sizə lazımdır» bento başlayanda çəkilir (xanalar üzərinə düşməsin)

# masonry: 4 sütun, uzun lent (yuxarı skrol olunur)
fs = ['p1.jpg', 'p2.jpg', 'p3.jpg', 'k_ilham.jpg', 'k_tekstura.jpg', 'k_rengler.jpg', 'k_taraz.jpg']
pos = ['50% 50%', '20% 30%', '80% 70%', '50% 10%', '30% 90%']
tiles, cols = '', [0, -120, -60, -180]
for i in range(76):
    c = i % 4; hh = (220, 300, 260, 340)[(i * 7) % 4]
    tiles += f'<div class="tile" style="left:{20 + c * 262}px;top:{cols[c]}px;height:{hh}px;background-image:url(assets/{fs[(i * 3 + c) % 7]});background-position:{pos[i % 5]}"></div>'
    cols[c] += hh + 14
counts = ['12', '48', '97', '163', '240', '318', '402', '511', '640', '777', '869', '999+']
cnt_js = ''.join(f'tl.set("#cnt b",{{textContent:"{n}"}},{t_cox - 0.1 + i * (t_bil - t_cox + 0.1) / len(counts):.3f});' for i, n in enumerate(counts))

cells = [('c1', 24, 948, NEO, 'k_ilham.jpg', 'İLHAM<br>MƏNBƏYİ', INK, t_ilh), ('c2', 552, 948, LAV, 'k_tekstura.jpg', 'TEKSTURA', INK, t_tek),
         ('c3', 24, 1432, PNK, None, 'RƏNGLƏR', '#fff', t_ren), ('c4', 552, 1432, CRM, 'grid', 'TARAZLIQ', INK, t_tar)]
def inner(img):
    if img is None: return ''.join(f'<i class="sw" style="left:{24 + k * 116}px;background:{c}"></i>' for k, c in enumerate([ULT, NEO, LAV, CRM]))
    if img == 'grid': return '<i class="gr"></i>'
    return f'<i class="ci" style="background-image:url(assets/{img})"></i>'
cell_html = ''.join(f'<div class="cell clip" id="{i}" data-start="{T_BENTO:.3f}" data-duration="{DUR - T_BENTO:.3f}" data-track-index="{12 + k}" style="left:{x}px;top:{y}px;background:{bg}">{inner(img)}<b style="color:{fg}">{lb}</b></div>'
                    for k, (i, x, y, bg, img, lb, fg, t) in enumerate(cells))
cell_js = ''.join(f'tl.fromTo("#{i}",{{opacity:0,scale:0.5}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(1.8)"}},{t - 0.12:.3f});' for i, *_, t in cells)

import shutil as _sh; os.makedirs(D + '/hf_C/assets', exist_ok=True); _sh.copy('/root/.fonts/ayra/PlayfairDisplay-700.ttf', D + '/hf_C/assets/PlayB.ttf')   # 19.11 müştəri: ad kursiv yox, düz stilli serif
css = f'''
@font-face {{ font-family:"PlayB"; src:url("assets/PlayB.ttf"); }}
#bg {{ position:absolute; inset:0; background:#fff; }}
#feed {{ position:absolute; left:0; top:0; width:1080px; height:470px; overflow:hidden; z-index:2; background:#fff; }}
#mas {{ position:absolute; left:0; top:0; width:1080px; }}
.tile {{ position:absolute; width:248px; border-radius:20px; background-size:cover; }}
#search {{ position:absolute; left:60px; top:44px; width:960px; height:96px; border-radius:48px; background:#fff; border:5px solid {INK}; z-index:3; font:34px/86px "Mono"; padding-left:40px; color:{INK}; box-shadow:0 10px 24px rgba(0,0,0,.18); }}
#cnt {{ position:absolute; left:290px; top:200px; z-index:4; font:60px/1 "Mono"; color:#fff; background:{PNK}; padding:18px 28px; opacity:0; }}
#stop {{ position:absolute; left:0; top:0; width:1080px; height:470px; z-index:5; background:{ULT}; transform-origin:50% 0; }}
#stop b {{ position:absolute; left:60px; top:130px; font:900 240px/1 "Arc"; font-stretch:112%; color:{NEO}; }}
#stop span {{ position:absolute; left:66px; top:400px; font:40px/1 "Mono"; color:{INK}; background:{NEO}; padding:12px 20px; }}
#vbox {{ position:absolute; left:0; top:0; width:1080px; height:1920px; overflow:hidden; z-index:1; clip-path:inset(470px 0px 0px 0px round 0px); }}
#vbox video {{ position:absolute; left:0; top:0; width:1080px; height:1920px; }}
#dark {{ position:absolute; inset:0; background:{INK}; z-index:0; opacity:0; }}
.cell {{ position:absolute; width:504px; height:460px; border-radius:34px; overflow:hidden; z-index:6; opacity:0; }}
.cell b {{ position:absolute; left:28px; top:344px; font:900 54px/0.98 "Arc"; font-stretch:108%; }}
.ci {{ position:absolute; left:24px; top:24px; width:456px; height:296px; border-radius:22px; background-size:cover; background-position:center; }}
.sw {{ position:absolute; top:24px; width:100px; height:296px; border-radius:16px; }}
.gr {{ position:absolute; left:24px; top:24px; width:456px; height:296px; border-radius:22px; background-image:linear-gradient(90deg,{INK}40 3px,transparent 3px),linear-gradient({INK}40 3px,transparent 3px); background-size:76px 74px; }}
#btn {{ position:absolute; left:24px; top:1350px; width:1032px; height:250px; border-radius:34px; background:{NEO}; z-index:6; font:900 80px/250px "Arc"; font-stretch:104%; color:{INK}; text-align:center; opacity:0; }}
#lnk {{ z-index:7; opacity:0; }}
#cur {{ position:absolute; left:900px; top:1900px; z-index:9; }}
.ring {{ position:absolute; left:560px; top:1440px; width:40px; height:40px; border:8px solid {INK}; border-radius:50%; z-index:9; opacity:0; }}
#good {{ z-index:7; opacity:0; }}
.cap {{ position:absolute; left:64px; width:952px; z-index:8; display:flex; flex-wrap:wrap; gap:6px 22px; font:900 90px/1.02 "Arc"; font-stretch:108%; }}
.cap .w {{ padding:4px 14px 0; color:#fff; -webkit-text-stroke:6px {INK}; paint-order:stroke fill; }}
.cap .w.on {{ background:{NEO}; color:{INK}; -webkit-text-stroke:0; }}
.ec {{ position:absolute; border-radius:34px; overflow:hidden; z-index:10; opacity:0; background-size:cover; background-position:center; }}
'''
body = f'''
<div id="bg"></div><div id="dark"></div>
<div id="vbox"><video id="v0" class="clip" src="assets/base.mp4" data-start="0" data-duration="{DUR:.3f}" data-has-audio="true" data-track-index="0"></video></div>
<div id="feed"><div id="mas">{tiles}</div></div>
<div id="search">⌕ moodboard ideyaları…</div>
<span class="mono clip" id="spk" data-start="0.5" data-duration="3.6" data-track-index="18" style="left:64px;top:1365px;background:{INK};color:#fff;font-size:24px;z-index:9;padding:16px 26px 18px">SPİKER<b style="display:block;margin-top:8px;font:700 54px/1 PlayB;letter-spacing:.01em">{SPİKER_ADI}</b></span>
<div id="cnt">ŞƏKİL: <b>0</b></div>
<div id="stop"><b>DAYAN</b><span>///skrolinq_bitdi</span></div>
<span class="mono clip" id="good" data-start="{B[3]:.3f}" data-duration="{B[4] - B[3]:.3f}" data-track-index="19" style="left:64px;top:1300px;background:{INK};color:{NEO};font-size:36px">///gözəl_moodboard ✓</span>
{cell_html}
<span class="mono clip" id="lnk" data-start="{t_lin - 0.1:.3f}" data-duration="{TEND - t_lin:.3f}" data-track-index="20" style="left:340px;top:1720px;background:#fff;color:{INK};font-size:36px">↗ ///linkə_keçid</span>
<div id="btn" class="clip" data-start="{t_sem - 0.15:.3f}" data-duration="{TEND - t_sem + 0.1:.3f}" data-track-index="21">SEMİNARA QOŞUL ↗</div>
<div id="cur" class="clip" data-start="{t_sem + 0.1:.3f}" data-duration="{TEND - t_sem - 0.1:.3f}" data-track-index="22">{CURSOR}</div>
<div class="ring clip" id="rg" data-start="{t_qos:.3f}" data-duration="0.5" data-track-index="23"></div>
{cap_html}
<div class="ec clip" id="e1" data-start="{TEND:.3f}" data-duration="{DUR - TEND:.3f}" data-track-index="24" style="left:24px;top:24px;width:1032px;height:700px;background:{NEO}"><b style="position:absolute;left:50px;top:230px;font:900 116px/0.98 Arc;font-stretch:110%;color:{INK}">MOODBOARD<br>SƏNƏTİ</b></div>
<div class="ec clip" id="e2" data-start="{TEND:.3f}" data-duration="{DUR - TEND:.3f}" data-track-index="25" style="left:24px;top:748px;width:504px;height:560px;background-image:url(assets/k_ilham.jpg)"></div>
<div class="ec clip" id="e3" data-start="{TEND:.3f}" data-duration="{DUR - TEND:.3f}" data-track-index="26" style="left:552px;top:748px;width:504px;height:560px;background-image:url(assets/k_tekstura.jpg)"></div>
<div class="ec clip" id="e4" data-start="{TEND:.3f}" data-duration="{DUR - TEND:.3f}" data-track-index="27" style="left:24px;top:1332px;width:1032px;height:560px;background:{PNK}"><b style="position:absolute;left:60px;top:105px;font:700 84px/1 PlayB;letter-spacing:.01em;color:#fff">{SPİKER_ADI}</b><span style="position:absolute;left:60px;top:250px;font:34px/1 Mono;background:{NEO};color:{INK};padding:12px 20px">5 DEKABR · {BREND}</span><span style="position:absolute;left:60px;top:330px;font:34px/1 Mono;background:{INK};color:#fff;padding:12px 20px">ÖDƏNİŞSİZ SEMİNAR · ətraflı linkdə</span></div>
'''
js = f'''
tl.set("#stop",{{scaleY:0}},0); tl.set("#v0",{{y:70,transformOrigin:"50% 0%"}},0);
tl.fromTo("#search",{{opacity:0,y:-40}},{{opacity:1,y:0,duration:0.3,ease:"power3.out"}},0);
tl.fromTo("#mas",{{y:0}},{{y:-900,duration:{t_cox - 0.1:.3f},ease:"none"}},0);
tl.fromTo("#mas",{{y:-900}},{{y:-3600,duration:{t_bil - t_cox + 0.1:.3f},ease:"power1.in",immediateRender:false}},{t_cox - 0.1:.3f});
tl.to("#mas",{{filter:"blur(4px)",duration:0.4}},{t_cox + 0.6:.3f});
tl.fromTo("#cnt",{{opacity:0,scale:1.5}},{{opacity:1,scale:1,duration:0.2,ease:"back.out(2)"}},{t_cox - 0.1:.3f});
{cnt_js}
tl.to("#stop",{{scaleY:1,duration:0.16,ease:"power4.in"}},{t_bil - 0.05:.3f});
tl.to("#cnt",{{opacity:0,duration:0.1}},{t_bil + 0.05:.3f});
tl.fromTo("#stop b",{{scale:1.5,opacity:0}},{{scale:1,opacity:1,duration:0.2,ease:"back.out(2)"}},{t_bil + 0.1:.3f});
// video tam ekrana
tl.to(["#feed","#stop","#search"],{{y:-800,duration:0.4,ease:"power3.in"}},{T_FULL - 0.15:.3f});
tl.to("#vbox",{{clipPath:"inset(0px 0px 0px 0px round 0px)",duration:0.4,ease:"power3.inOut"}},{T_FULL - 0.15:.3f}); tl.to("#v0",{{y:-100,scale:1.06,duration:0.4,ease:"power3.inOut"}},{T_FULL - 0.15:.3f});
tl.fromTo("#good",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:0.25}},{B[3] + 0.1:.3f});
// bento
tl.to("#dark",{{opacity:1,duration:0.2}},{T_BENTO - 0.05:.3f});
tl.to("#vbox",{{clipPath:"inset(24px 24px 996px 24px round 34px)",duration:0.45,ease:"power3.inOut"}},{T_BENTO - 0.05:.3f}); tl.to("#v0",{{y:-100,duration:0.45,ease:"power3.inOut"}},{T_BENTO - 0.05:.3f});
{cell_js}
// CTA: xanalar yığılır → neon düymə
tl.to(".cell",{{scale:0,opacity:0,duration:0.3,ease:"power3.in",stagger:0.05}},{B[6] - 0.3:.3f});
tl.to("#vbox",{{clipPath:"inset(24px 24px 596px 24px round 34px)",duration:0.4,ease:"power3.inOut"}},{B[6] - 0.1:.3f}); tl.to("#v0",{{y:-100,duration:0.4}},{B[6] - 0.1:.3f});
tl.fromTo("#lnk",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.25}},{t_lin - 0.1:.3f});
tl.fromTo("#btn",{{opacity:0,scaleY:0.2}},{{opacity:1,scaleY:1,duration:0.3,ease:"back.out(1.8)"}},{t_sem - 0.15:.3f});
tl.fromTo("#cur",{{x:0,y:0}},{{x:-320,y:-440,duration:0.45,ease:"power2.out"}},{t_sem + 0.1:.3f});
tl.fromTo("#rg",{{opacity:1,scale:0.5}},{{opacity:0,scale:2.8,duration:0.35}},{t_qos:.3f});
tl.to("#btn",{{scale:0.96,duration:0.07,yoyo:true,repeat:1}},{t_qos:.3f});
tl.to("#btn",{{backgroundColor:"{PNK}",color:"#fff",duration:0.1}},{t_qos + 0.12:.3f});
tl.fromTo("#spk",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:0.25}},0.5); tl.to("#spk",{{opacity:0,duration:0.2}},3.9);
tl.to("#vbox",{{opacity:0,duration:0.2}},{TEND + 0.25:.3f});
// son: bento-kolaj
tl.fromTo("#e1",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(1.6)"}},{TEND:.3f});
tl.fromTo(["#e2","#e3"],{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(1.6)",stagger:0.08}},{TEND + 0.12:.3f});
tl.fromTo("#e4",{{opacity:0,scaleY:0.3}},{{opacity:1,scaleY:1,duration:0.3,ease:"back.out(1.6)"}},{TEND + 0.3:.3f});
{cap_js}
'''
sfx = [(0.0, 'pro_air.wav', 0.15), (t_cox - 0.1, 'riser.wav', 0.14), (t_bil - 0.05, 'pro_thump.wav', 0.3), (T_FULL - 0.15, 'pro_whoosh.wav', 0.16),
       (B[3] + 0.1, 'ding.wav'), (T_BENTO - 0.05, 'pro_whoosh.wav', 0.16)] + [(t - 0.12, 'pop.wav', 0.16) for *_, t in cells] + \
      [(B[6] - 0.3, 'swish.wav'), (t_sem - 0.15, 'pop.wav'), (t_qos, 'softclick.wav', 0.25), (TEND, 'pro_whoosh.wav', 0.16), (TEND + 0.3, 'chime.wav')]
write(D, 'hf_C', css, body, js, sfx, '/root/montaj-data/music_mixkit/midnight-funk.mp3', clean_keep='#vbox')
print('C OK')
