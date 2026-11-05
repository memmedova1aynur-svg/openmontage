"""Baxış və düzəliş səhifəsi: telefonda açılan tək HTML fayl (video daxilində).

  python3 review_page.py <hazır.mp4> [başlıq]
Video saniyəsində dayandırıb şərh yazılır ("0:14 — səs gəlir"); "Kopyala" düyməsi bütün qeydləri
mətn kimi kopyalayır — chat-a yapışdırılır, yalnız həmin hissələr düzəldilir. Şərhlər brauzerdə saxlanılır.
"""
import base64, html, subprocess, sys, tempfile
from pathlib import Path

MP4 = Path(sys.argv[1]); TITLE = sys.argv[2] if len(sys.argv) > 2 else MP4.stem
prox = Path(tempfile.mkdtemp()) / "p.mp4"  # yüngül nüsxə (540p) — fayl kiçik qalsın
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(MP4), "-vf", "scale=540:-2", "-c:v", "libx264", "-crf", "28", "-preset", "veryfast",
                "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(prox)], check=True)
b64 = base64.b64encode(prox.read_bytes()).decode(); key = "rv_" + MP4.stem
page = f"""<!doctype html><html lang="az"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(TITLE)}</title><style>
body{{margin:0;font-family:-apple-system,system-ui,sans-serif;background:#111;color:#eee}}main{{max-width:520px;margin:0 auto;padding:16px}}
video{{width:100%;border-radius:14px;background:#000}}h1{{font-size:18px;margin:6px 0 12px}}
.row{{display:flex;gap:8px;margin:12px 0}}input{{flex:1;padding:12px;border-radius:10px;border:1px solid #444;background:#1c1c1c;color:#eee;font-size:16px}}
button{{padding:12px 14px;border:0;border-radius:10px;background:#6CC57E;color:#0F3B2C;font-weight:700;font-size:15px}}
.b2{{background:#333;color:#eee}}li{{margin:8px 0;line-height:1.35}}li b{{color:#6CC57E;cursor:pointer}}li span{{color:#888;margin-left:6px;cursor:pointer}}
</style></head><body><main><h1>{html.escape(TITLE)}</h1>
<video id="v" controls playsinline src="data:video/mp4;base64,{b64}"></video>
<div class="row"><input id="t" placeholder="Bu saniyədə nə düzəlməlidir?"><button onclick="add()">+ Qeyd</button></div>
<ol id="l"></ol><div class="row"><button class="b2" onclick="cp()">Hamısını kopyala</button><button class="b2" onclick="clr()">Təmizlə</button></div>
<script>
const K="{key}",v=document.getElementById('v');let N=[];try{{N=JSON.parse(localStorage.getItem(K)||'[]')}}catch(e){{}}
const f=s=>Math.floor(s/60)+':'+String(Math.floor(s%60)).padStart(2,'0');
function save(){{try{{localStorage.setItem(K,JSON.stringify(N))}}catch(e){{}}draw()}}
function draw(){{document.getElementById('l').innerHTML=N.map((n,i)=>`<li><b onclick="v.currentTime=${{n.t}}">${{f(n.t)}}</b> — ${{n.x.replace(/</g,'&lt;')}}<span onclick="N.splice(${{i}},1);save()">✕</span></li>`).join('')}}
function add(){{const x=document.getElementById('t').value.trim();if(!x)return;N.push({{t:v.currentTime,x}});N.sort((a,b)=>a.t-b.t);document.getElementById('t').value='';save()}}
function cp(){{const s="{html.escape(TITLE)} — düzəlişlər:\\n"+N.map(n=>f(n.t)+' — '+n.x).join('\\n');navigator.clipboard.writeText(s).then(()=>alert('Kopyalandı — chat-a yapışdırın'),()=>prompt('Kopyalayın:',s))}}
function clr(){{if(confirm('Bütün qeydlər silinsin?')){{N=[];save()}}}}
document.getElementById('t').addEventListener('keydown',e=>{{if(e.key==='Enter')add()}});draw();
</script></main></body></html>"""
out = MP4.with_name(MP4.stem + "_baxis.html"); out.write_text(page, encoding="utf-8")
print(f"baxış səhifəsi: {out} ({out.stat().st_size / 1e6:.1f} MB)")
