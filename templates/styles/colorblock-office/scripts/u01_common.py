"""{MÜŞTƏRİ} U01 B/C versiyaları üçün ümumi hissə: söz vaxtları (base vaxtı), altyazı, SFX/musiqi, fayl yazımı."""
import json, os, shutil
SH = 0.30
PAUSES = [(9.433, 0.16), (22.48, 0.12), (23.60, 0.15)]   # base_u01.py ilə eyni (19.11: 7.02 pauzası çıxarıldı)
CUT = (9.433, 9.62)                                       # base_u01.py ilə eyni (göz yumulan hissə kəsilib)
def bt(src): return round(src - SH - ((CUT[1] - CUT[0]) if src >= CUT[1] - 0.001 else 0) + sum(p for t, p in PAUSES if src >= t - 0.001), 3)   # mənbə vaxtı → base vaxtı
DUR = 29.02 - (CUT[1] - CUT[0]) + sum(p for _, p in PAUSES)
SP = '/tmp/claude-0/-home-user-openmontage/75c47652-31ab-5cc9-b432-aff8ff258064/scratchpad/{musteri}/IMG_3018.json'
FIX = {'yıqıbsan,': 'yığmısan,', 'yorulmuşsan,': 'yorulmusan?', 'yorulmusan,': 'yorulmusan?', 'istəyirsən,': 'istəyirsən?', 'linke': 'linkə', 'eləyib,': 'eləyib'}   # 19.11 müştəri: durğu işarələri tam   # 18.11 agentlik: danışıq forması
WS = []
for s in json.load(open(SP)):
    for a, b, w in s['w']:
        if w.startswith('-') and WS: WS[-1][1] = bt(b); WS[-1][2] += w; continue
        WS.append([bt(a), bt(b), FIX.get(w, w)])
# 19.11 müştəri: cümlə sonu/sadalama işarələri
WS[15][2] = 'bilmirsən.'; WS[29][2] = 'lazımdır:'
def at(word, after=0):
    for a, b, w in WS:
        if a >= after - 0.01 and w.lower().strip('.,').startswith(word): return a
    raise KeyError(word)
UP = lambda s: s.replace('i', 'İ').replace('ı', 'I').upper()
ULT, NEO, LAV, INK, CRM, PNK = '#2515C9', '#C6FF00', '#D6B9F8', '#100C1C', '#F6F1E8', '#FF249B'
B = [0, 2.65, 5.30] + [bt(x + SH) for x in (11.50, 12.90, 14.90, 20.00, 25.83)]; TEND = B[-1]
GROUPS = [[0, 1], [2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18], [19, 20, 21], [22, 23, 24], [25, 26, 27], [28, 29],
          [37, 38], [39, 40], [41, 42], [43], [44], [45], [46]]
CURSOR = f'<svg viewBox="0 0 70 96" width="92" height="124"><polygon points="4,4 4,74 22,58 34,88 48,82 36,54 60,54" fill="#fff" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/></svg>'

def captions(top_of, cls='cap'):
    """söz-söz altyazı: top_of(t) → piksel. Aktiv söz 'on', keçmiş 'done'."""
    html, js = [], []
    for k, g in enumerate(GROUPS):
        s0 = WS[g[0]][0] - 0.06
        nx = GROUPS[k + 1] if k + 1 < len(GROUPS) else None
        e0 = (WS[nx[0]][0] - 0.06) if nx and WS[nx[0]][0] - WS[g[-1]][1] < 0.6 else WS[g[-1]][1] + 0.35
        e0 = min(e0, TEND - 0.3)
        spans = ''.join(f'<span class="w" id="w{k}_{j}">{UP(WS[i][2])}</span>' for j, i in enumerate(g))   # 19.11 müştəri: vergül/sual işarəsi silinmir
        html.append(f'<div class="{cls} clip" id="k{k}" style="top:{top_of(s0)}px" data-start="{s0:.3f}" data-duration="{e0 - s0:.3f}" data-track-index="8">{spans}</div>')
        js.append(f'tl.fromTo("#k{k}",{{opacity:0,y:18}},{{opacity:1,y:0,duration:0.14,ease:"power2.out"}},{s0:.3f});')
        for j, i in enumerate(g):
            js.append(f'tl.set("#w{k}_{j}",{{className:"w on"}},{WS[i][0]:.3f});')
            nxt = WS[g[j + 1]][0] if j + 1 < len(g) else e0
            js.append(f'tl.set("#w{k}_{j}",{{className:"w done"}},{min(nxt, WS[i][0] + 1.1):.3f});')
    return ''.join(html), ''.join(js)

FONTS = '''@font-face { font-family:"Arc"; src:url("assets/Archivo.ttf"); font-weight:100 900; font-stretch:62% 125%; }
@font-face { font-family:"Mono"; src:url("assets/SpaceMono-Bold.ttf"); }
@font-face { font-family:"PlayI"; src:url("assets/PlayI.ttf"); }
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1920px; overflow:hidden; }
#root { position:relative; width:1080px; height:1920px; overflow:hidden; }
.mono { position:absolute; font:30px/1 "Mono"; padding:12px 20px; white-space:nowrap; }
#prog { position:absolute; left:0; top:1908px; width:1080px; height:12px; z-index:50; background:rgba(16,12,28,.2); }
#prog b { display:block; height:100%; width:100%; background:#FF249B; transform-origin:0 50%; transform:scaleX(0); }
'''

def write(D, name, css, body, js, sfx, music, musvol=0.11, clean_keep='#vbox'):
    """D = esas qovluğu; name = hf qovluq adı (hf_B / hf_C)."""
    HF = os.path.join(D, name); A = HF + '/assets'; os.makedirs(A + '/sfx', exist_ok=True)
    src = os.path.join(D, 'hf', 'assets')   # A versiyasının hazır asset-ləri (şriftlər, şəkillər)
    if not os.path.isdir(src): src = os.path.join(D, name, 'assets')
    for f in os.listdir(src):
        if f.endswith(('.ttf', '.jpg')) and os.path.abspath(src) != os.path.abspath(A): shutil.copy(os.path.join(src, f), A + '/' + f)
    shutil.copy(os.path.join(D, 'base.mp4'), A + '/base.mp4')
    shutil.copy(music, A + '/music.mp3')
    sh = ''
    for i, (t, f, *v) in enumerate(sfx):
        shutil.copy(f'/root/montaj-data/sfx/{f}', f'{A}/sfx/{f}')
        sh += f'<audio id="sfx{i}" class="clip" src="assets/sfx/{f}" data-start="{max(0, t):.3f}" data-duration="1.0" data-volume="{v[0] if v else 0.2}" data-track-index="{40 + i}"></audio>'
    def page(extra_css='', sfx_html=sh):
        return f'''<!DOCTYPE html>
<html lang="az"><head><meta charset="UTF-8"><meta name="viewport" content="width=1080, height=1920">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>{FONTS}{css}{extra_css}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{DUR:.3f}" data-width="1080" data-height="1920">
{body}
<div id="prog"><b></b></div>
<audio id="mus" class="clip" src="assets/music.mp3" data-start="0" data-duration="{DUR:.3f}" data-volume="{musvol}" data-fade-in="0.5" data-fade-out="1.5" data-track-index="30"></audio>
{sfx_html}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
tl.to("#prog b", {{ scaleX:1, duration:{DUR:.3f}, ease:"none" }}, 0);
{js}
window.__timelines["main"] = tl;
tl.seek(0);
</script></body></html>'''
    open(HF + '/index.html', 'w', encoding='utf-8').write(page())
    json.dump({'name': name, 'private': True, 'type': 'module'}, open(HF + '/package.json', 'w'))
    json.dump({'id': name, 'name': name}, open(HF + '/meta.json', 'w'))
    CL = HF + '_clean'; os.makedirs(CL, exist_ok=True)
    for f in ['package.json', 'meta.json']: shutil.copy(f'{HF}/{f}', f'{CL}/{f}')
    if os.path.islink(f'{CL}/assets'): os.remove(f'{CL}/assets')
    if not os.path.exists(f'{CL}/assets'): os.symlink(os.path.abspath(A), f'{CL}/assets')
    # QC təmiz versiya: yalnız video qutusu görünür, eyni hərəkətlərlə
    open(f'{CL}/index.html', 'w', encoding='utf-8').write(page(f'#root *:not({clean_keep}):not({clean_keep} *) {{ visibility:hidden !important; }} {clean_keep}, {clean_keep} * {{ visibility:visible !important; }}', ''))
    return HF
