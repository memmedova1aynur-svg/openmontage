"""Fotodan reklam (generativ AI YOX): foto üzərində pan/zoom + mətn + motion qrafika + səs → Instagram MP4.
Generativ AI video (şəkli "canlandırmaq", danışdırmaq) ayrı funksiyadır və bu alətdə yoxdur.

İstifadə:  python3 photo_ad.py plan.json
plan.json:
{
  "photos": [{"file": "a.jpg", "dur": 4.5, "move": "zoom_in", "focus": [0.5, 0.4]}, ...],   # move: zoom_in|zoom_out|pan_left|pan_right|pan_up|still
  "texts": [{"t0": 0.4, "t1": 4.2, "kind": "headline", "text": "Başlıq"},                     # kind: label|headline|sub|cta|list
            {"t0": 5.0, "t1": 9.0, "kind": "list", "text": "Bənd 1\\nBənd 2\\nBənd 3"}],
  "brand": {"name": "Ekspert", "accent": "#6CC57E", "dark": "#0B2A20", "font": "Montserrat"},
  "music": "mus.mp3",            # istəyə görə
  "voice": "voice.wav",          # istəyə görə: hazır səsləndirmə faylı (TTS ayrıca yaradılır)
  "out": "out/Reklam.mp4"        # nəticə: _vN versiyası
}
Mətnlər yalnız müştərinin təsdiqlənmiş reklam mətnindən götürülür; qiymət, tarix, nəticə uydurulmur.
"""
import json, sys, shutil, html as H
from pathlib import Path
A = Path(__file__).resolve().parent; sys.path.insert(0, str(A))
import avkit as K
import numpy as np

P = json.load(open(sys.argv[1])); ROOT = Path(sys.argv[1]).resolve().parent
rp = lambda x: str((ROOT / x).resolve()) if x and not Path(x).is_absolute() else x
OUT = K.next_version(rp(P["out"])); WORK = OUT.parent / (OUT.stem + "_work"); WORK.mkdir(parents=True, exist_ok=True)
br = {"name": "", "accent": "#6CC57E", "dark": "#0B2A20", "font": "Montserrat", **P.get("brand", {})}
XF = 0.45  # fotolar arası keçid
photos, t = [], 0.0
for i, ph in enumerate(P["photos"]):
    ext = Path(ph["file"]).suffix; dst = WORK / f"p{i}{ext}"; shutil.copy(rp(ph["file"]), dst)
    photos.append({"src": dst.name, "t0": t, "dur": ph["dur"], "move": ph.get("move", "zoom_in"), "focus": ph.get("focus", [0.5, 0.45])})
    t += ph["dur"] - (XF if i < len(P["photos"]) - 1 else 0)
TOTAL = round(t, 3)
cfg = {"photos": photos, "texts": P.get("texts", []), "XF": XF, "TOTAL": TOTAL}

page = f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family={br['font'].replace(' ', '+')}:wght@500;600;700;800;900&family=JetBrains+Mono:wght@600&display=block" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}} html,body{{width:1080px;height:1920px;overflow:hidden;background:#000;font-family:'{br['font']}',sans-serif}}
.ph{{position:absolute;inset:0;overflow:hidden}} .ph img{{position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover;will-change:transform}}
.shade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.45) 0%,rgba(0,0,0,0) 30%,rgba(0,0,0,0) 52%,rgba(0,0,0,.72) 100%)}}
.tx{{position:absolute;left:72px;right:72px;opacity:0;color:#fff}}
.label{{top:236px;right:auto;font-family:'JetBrains Mono',monospace;font-size:28px;letter-spacing:4px;text-transform:uppercase;color:{br['accent']};background:rgba(0,0,0,.62);padding:10px 18px;border-radius:12px}}
.headline{{top:318px;font-weight:900;font-size:96px;line-height:1.04;letter-spacing:-3px;text-shadow:0 6px 30px rgba(0,0,0,.35)}}
.headline b{{background:{br['accent']};color:{br['dark']};padding:0 .16em;border-radius:.12em;display:inline-block;transform:rotate(-1.2deg)}}
.sub{{bottom:560px;font-weight:600;font-size:44px;line-height:1.3}}
.list{{bottom:520px;font-weight:700;font-size:46px;line-height:1.25}} .list div{{display:flex;gap:22px;align-items:center;margin:16px 0;opacity:0}}
.list i{{width:44px;height:44px;border-radius:50%;background:{br['accent']};flex:none}}
.cta{{bottom:430px;display:flex;justify-content:center}} .cta span{{background:{br['accent']};color:{br['dark']};font-weight:900;font-size:50px;padding:28px 56px;border-radius:24px;box-shadow:0 0 0 6px rgba(255,255,255,.18)}}
.chip{{position:absolute;left:72px;top:160px;font-weight:700;font-size:28px;color:#fff;border:3px solid rgba(255,255,255,.85);border-radius:999px;padding:10px 26px}}
</style></head><body>
<div id="ph"></div><div class="shade"></div>{'<div class="chip">' + H.escape(br['name']) + '</div>' if br['name'] else ''}<div id="tx"></div>
<script>
const C={json.dumps(cfg, ensure_ascii=False)};
const cl=(x,a=0,b=1)=>Math.min(b,Math.max(a,x)), eio=x=>{{x=cl(x);return x<.5?2*x*x:1-Math.pow(-2*x+2,2)/2}}, back=x=>{{x=cl(x);const c=1.6;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)}};
const PH=document.getElementById('ph'), TX=document.getElementById('tx');
C.photos.forEach((p,i)=>{{const d=document.createElement('div');d.className='ph';d.innerHTML=`<img src="${{p.src}}">`;PH.appendChild(d);p.el=d;p.img=d.firstChild}});
C.texts.forEach(x=>{{const d=document.createElement('div');d.className='tx '+x.kind;
  if(x.kind==='list') d.innerHTML=x.text.split('\\n').map(s=>`<div><i></i><span>${{s}}</span></div>`).join('');
  else if(x.kind==='cta') d.innerHTML=`<span>${{x.text}}</span>`; else d.innerHTML=x.text.replace(/\\*([^*]+)\\*/g,'<b>$1</b>').replace(/\\n/g,'<br>');
  TX.appendChild(d);x.el=d}});
window.EVENTS=[]; C.texts.forEach(x=>EVENTS.push({{t:x.t0,type:x.kind==='cta'?'pop':'pop2',v:0}})); C.photos.slice(1).forEach(p=>EVENTS.push({{t:p.t0,type:'swish',v:0}}));
window.TIMES={{TOTAL:C.TOTAL}};
window.renderFrame=function(t){{
  C.photos.forEach((p,i)=>{{const u=cl((t-p.t0)/p.dur), fx=p.focus[0], fy=p.focus[1];
    let s=1.0,dx=0,dy=0; const e=eio(u);
    if(p.move==='zoom_in') s=1.04+0.16*e; else if(p.move==='zoom_out') s=1.2-0.16*e;
    else if(p.move==='pan_left'){{s=1.18;dx=60-120*e}} else if(p.move==='pan_right'){{s=1.18;dx=-60+120*e}} else if(p.move==='pan_up'){{s=1.18;dy=80-160*e}} else s=1.04;
    p.img.style.transformOrigin=`${{fx*100}}% ${{fy*100}}%`; p.img.style.transform=`translate(${{dx}}px,${{dy}}px) scale(${{s}})`;
    const fin=i===0?1:cl((t-p.t0)/C.XF), fout=i===C.photos.length-1?1:1-cl((t-(p.t0+p.dur-C.XF))/C.XF);
    p.el.style.opacity=(t>=p.t0-0.001&&t<=p.t0+p.dur)?Math.min(fin,fout):0}});
  C.texts.forEach(x=>{{const a=cl((t-x.t0)/.45), b=cl((x.t1-t)/.3), on=t>=x.t0&&t<=x.t1;
    x.el.style.opacity=on?Math.min(a,b):0; x.el.style.transform=x.kind==='cta'?`scale(${{.7+.3*back((t-x.t0)/.45)}})`:`translateY(${{(1-eio(a))*40}}px)`;
    if(x.kind==='list')[...x.el.children].forEach((c,j)=>{{const q=cl((t-x.t0-.25-j*.45)/.35);c.style.opacity=on?Math.min(q,b):0;c.style.transform=`translateX(${{(1-eio(q))*-40}}px)`}})}});
}};
window.renderFrame(0);
</script></body></html>"""
(WORK / "ad.html").write_text(page)
FR = WORK / "fr"; K.ensure_font(br["font"])
K.run(["node", str(A / "games/render.js"), str(WORK / "ad.html"), str(FR), ""])
N = int(TOTAL * K.SR); mix = np.zeros((N, 2))
if P.get("voice"):
    v = K.load(rp(P["voice"])); m = min(N, len(v)); mix[:m] += v[:m] * 10 ** ((-20 - K.rms_db(v[np.abs(v).max(1) > 1e-4])) / 20)
mask = np.abs(mix).max(1) > 1e-3
if P.get("music"):
    mix += K.music_bed(K.load(rp(P["music"])), N, mask if mask.any() else None, level=P.get("music_level", -29 if mask.any() else -20), fade_in=0.6, fade_out=1.5)
for e in json.load(open(FR / "events.json"))["E"]:
    mix = K.add_sfx(mix, K.synth({"pop": "pop", "pop2": "pop", "swish": "swoosh"}[e["type"]]), e["t"], -32 if e["type"] != "pop" else -28)
MIX, FIN = WORK / "mix.wav", WORK / "final.wav"; K.save(mix, MIX); K.finalize(MIX, FIN)
VID = WORK / "v.mp4"
K.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", str(FR / "%05d.jpg"), "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "4.5M", "-bufsize", "9M",
       "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p", "-r", "30", "-g", "60", str(VID)])
K.export_ig(VID, FIN, OUT, copy_video=True)
K.cover(OUT, P.get("cover_t", 1.2), OUT.parent / (OUT.stem + "_kadr.jpg")); shutil.rmtree(FR)
q = K.qa(OUT); json.dump(q, open(OUT.parent / (OUT.stem + "_qa.json"), "w"), ensure_ascii=False, indent=1)
print(f"{'OK' if q['ok'] else 'YOXLA'} {OUT} {q}")
