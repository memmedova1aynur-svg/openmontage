#!/usr/bin/env python3
"""AYRA Studio idarəetmə paneli (yerli HTML, gizli qovluqda): workspace.py nəticəsi + istehsal.json.
  dashboard.py  → instagram-clients/_agency/panel.html"""
import json, html, datetime, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; AG = ROOT / "instagram-clients/_agency"
subprocess.run([sys.executable, str(Path(__file__).parent / "workspace.py")], capture_output=True)
W = json.loads((AG / "workspaces.json").read_text()); J = json.loads((AG / "istehsal.json").read_text())
ST = {"novbede": ("Növbədə", "#8C7369"), "montaj": ("Montaj", "#DC5063"), "qc": ("QC", "#E29999"), "gonderildi": ("Göndərilib · cavab gözlənir", "#AF2240"),
      "duzelis": ("Düzəliş", "#DC5063"), "tesdiq": ("Təsdiq", "#3D7A5A"), "saxla": ("Saxlanılıb", "#9A9A9A")}
cnt = {k: sum(1 for r in J if r["merhele"] == k) for k in ST}
e = html.escape
def chip(m): l, c = ST.get(m, (m, "#666")); return f'<span class="chip" style="--c:{c}">{e(l)}</span>'
rows = "".join(f"<tr><td>{e(r['musteri'])}</td><td>{e(r['video'])}</td><td>{chip(r['merhele'])}</td><td>{e(r.get('tehvil') or '—')}</td><td class='q'>{e(r.get('qeyd',''))}</td></tr>" for r in J)
cards = "".join(f"""<article><h3>{e(w['ad'])}</h3><p class="meta">{e(w['musteri'])} · {len(w['jobs'])} iş · {w['rules']} qayda · palitra {'təsdiqli' if w['approved'] else ('qaralama' if w['palette'] else 'yoxdur')}</p>
<ul>{''.join(f'<li>{e(m)}</li>' for m in w['missing']) or '<li class=ok>çatışan yoxdur</li>'}</ul></article>""" for w in W)
kp = "".join(f'<div class="k"><b>{cnt[k]}</b><span>{e(ST[k][0])}</span></div>' for k in ST)
out = f"""<!doctype html><html lang="az"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AYRA Studio Panel</title><style>
:root{{--bg:#FBF8F7;--ink:#2B1D20;--mut:#7A6A6D;--line:#EADFDD;--acc:#AF2240}}
@media (prefers-color-scheme:dark){{:root{{--bg:#1B1517;--ink:#F3E9E7;--mut:#B3A2A5;--line:#3A2E31;--acc:#FFB4B4}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:28px 16px 60px}} h1{{font-size:26px;margin:0}} h2{{font-size:17px;margin:34px 0 12px;color:var(--acc)}}
.sub{{color:var(--mut);margin:4px 0 18px}} .kp{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px}}
.k{{border:1px solid var(--line);border-radius:12px;padding:12px 14px}} .k b{{display:block;font-size:26px}} .k span{{color:var(--mut);font-size:13px}}
table{{width:100%;border-collapse:collapse;font-size:14px}} td,th{{text-align:left;padding:8px 6px;border-bottom:1px solid var(--line);vertical-align:top}} th{{color:var(--mut);font-weight:600}}
.q{{color:var(--mut);max-width:420px}} .chip{{display:inline-block;white-space:nowrap;padding:2px 9px;border-radius:20px;font-size:12px;color:var(--c);border:1px solid var(--c)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}} article{{border:1px solid var(--line);border-radius:12px;padding:14px}}
article h3{{margin:0;font-size:16px}} .meta{{color:var(--mut);font-size:13px;margin:4px 0 8px}} article ul{{margin:0;padding-left:18px;font-size:13px}} .ok{{color:#3D7A5A}}
.tw{{overflow-x:auto}} .flow{{display:flex;flex-wrap:wrap;gap:6px;font-size:13px}} .flow span{{border:1px solid var(--line);border-radius:8px;padding:5px 9px}}
</style></head><body><main>
<h1>AYRA STUDIO — idarəetmə paneli</h1><p class="sub">Yenilənib: {datetime.datetime.now():%d.%m.%Y %H:%M} · mənbə: _agency/istehsal.json, müştəri WORKSPACE.md</p>
<div class="kp">{kp}</div>
<h2>Montaj növbəsi və təhvillər</h2><div class="tw"><table><tr><th>Müştəri</th><th>İş</th><th>Mərhələ</th><th>Təhvil</th><th>Qeyd</th></tr>{rows}</table></div>
<h2>Brand Workspace-lər · çatışmayan məlumat</h2><div class="grid">{cards}</div>
<h2>Şöbələr və axın</h2><div class="flow"><span>Studio Director</span><span>Brand Strategy</span><span>Creative Direction</span><span>Graphic Design</span><span>Video &amp; Motion</span><span>Post-Production (8)</span><span>Copy</span><span>Growth</span><span>Design Critic / Video QC</span><span>Studio Manager</span></div>
<h2>Həftəlik prioritet qaydası</h2><p>Hər müştəri üçün çəkilişdən sonra əvvəl 3–5 video → növbəti müştəri → qalanlar mərhələli. Təsdiq gözləyənlər hər səhər yoxlanır.</p>
</main></body></html>"""
(AG / "panel.html").write_text(out); print(AG / "panel.html")
