"""Premium sənəd mühərriki: JSON spesifikasiya -> A4 PDF (agentlik üslubu).
python3 build_doc.py spec.json out.pdf
Bloklar: {"h":"Başlıq"} bölmə; {"p":"mətn"}; {"lead":"italik giriş"}; {"cards":[{"t","d","items":[]}],"cols":2|3,"dark":bool};
{"table":{"head":[...],"rows":[[...]]}}; {"check":[...]} (☐ siyahı); {"q":"sual","o":[seçimlər],"lines":n,"hint":"..."} (anket sualı);
{"swatches":[["ad","#hex"]]}; {"steps":[["t","d"]]}; {"packages":[{"name","tag","for","items":[],"price"}]}; {"note":"kiçik qeyd"}; {"pb":1} səhifə keçidi."""
import json, sys, os, subprocess, html
src, out = sys.argv[1], sys.argv[2]
S = json.load(open(src, encoding='utf-8')); e = lambda s: html.escape(str(s))
A = S.get('agency', {'name': 'Aynur Məmmədova', 'sub': 'Brend Menecment', 'contact': '@1aynurmemmedova'})
n = [0, 0]
def blk(b):
    if 'h' in b:
        n[0] += 1; return f'<div class="sh"><span class="n">{n[0]:02d}</span><h2>{e(b["h"])}</h2></div>'
    if 'p' in b: return f'<p>{e(b["p"])}</p>'
    if 'lead' in b: return f'<div class="lead">{e(b["lead"])}</div>'
    if 'note' in b: return f'<div class="note">{e(b["note"])}</div>'
    if 'pb' in b: return '<div style="break-after:page"></div>'
    if 'cards' in b:
        cs = ''.join(f'<div class="card{" dark" if b.get("dark") or c.get("dark") else ""}">{f"<div class=k>{e(c[chr(107)])}</div>" if c.get("k") else ""}<h3>{e(c.get("t",""))}</h3>{f"<div>{e(c[chr(100)])}</div>" if c.get("d") else ""}{"<ul>"+"".join(f"<li>{e(i)}</li>" for i in c.get("items",[]))+"</ul>" if c.get("items") else ""}</div>' for c in b['cards'])
        return f'<div class="grid" style="grid-template-columns:repeat({b.get("cols",2)},1fr)">{cs}</div>'
    if 'table' in b:
        t = b['table']; return '<table><tr>' + ''.join(f'<th>{e(h)}</th>' for h in t['head']) + '</tr>' + ''.join('<tr>' + ''.join(f'<td>{e(c)}</td>' for c in r) + '</tr>' for r in t['rows']) + '</table>'
    if 'check' in b: return '<ul class="chk">' + ''.join(f'<li>{e(i)}</li>' for i in b['check']) + '</ul>'
    if 'q' in b:
        n[1] += 1; o = ''.join(f'<span class="op">☐ {e(x)}</span>' for x in b.get('o', []))
        ln = ''.join('<div class="ln"></div>' for _ in range(b.get('lines', 0 if b.get('o') else 2)))
        return f'<div class="q"><span class="qn">{n[1]:02d}</span><div><div class="qt">{e(b["q"])}</div>{f"<div class=hint>{e(b[chr(104)+chr(105)+chr(110)+chr(116)])}</div>" if b.get("hint") else ""}<div class="ops">{o}</div>{ln}</div></div>'
    if 'swatches' in b: return '<div class="sw">' + ''.join(f'<div style="background:{h}"><span>{e(nm)}<br>{e(h)}</span></div>' for nm, h in b['swatches']) + '</div>'
    if 'steps' in b: return '<div class="steps">' + ''.join(f'<div class="st"><b>{i+1}</b><div><div class="stt">{e(t)}</div><div class="std">{e(d)}</div></div></div>' for i, (t, d) in enumerate(b['steps'])) + '</div>'
    if 'packages' in b:
        return '<div class="pk">' + ''.join(f'<div class="pc{" hi" if p.get("hi") else ""}"><div class="pt">{e(p.get("tag",""))}</div><h3>{e(p["name"])}</h3><div class="pf">{e(p.get("for",""))}</div><ul>' + ''.join(f'<li>{e(i)}</li>' for i in p['items']) + f'</ul><div class="pp">{e(p.get("price",""))}</div></div>' for p in b['packages']) + '</div>'
    return ''
body = ''.join(blk(b) for b in S['blocks'])
cv = S['cover']; steps = ''.join(f'<div class="cst"><b>{i+1}</b><div><div class="stt">{e(t)}</div><div class="std">{e(d)}</div></div></div>' for i, (t, d) in enumerate(cv.get('steps', [])))
page = f'''<!doctype html><html lang="az"><head><meta charset="utf-8"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&family=Lora:ital,wght@1,500;1,600&family=JetBrains+Mono:wght@500;700&display=block" rel="stylesheet">
<style>@page{{size:A4;margin:16mm 0 14mm}}@page:first{{margin:0}}*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter;color:#3B1832;font-size:10.5pt;line-height:1.5;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.mono{{font-family:'JetBrains Mono';font-weight:700;letter-spacing:.16em;font-size:8.5pt;text-transform:uppercase}}
.cover{{height:297mm;background:#3B1832;color:#FBFAF6;padding:22mm 20mm;position:relative;break-after:page}}
.cover h1{{font:900 56pt/.95 Inter;letter-spacing:-.04em;margin-top:60mm}}.cover h1 span{{color:#CDF46B}}.cover .sub{{font:italic 500 16pt/1.4 Lora;color:#CFC3F5;margin-top:9mm;max-width:160mm}}
.csteps{{position:absolute;left:20mm;right:20mm;bottom:30mm;display:grid;grid-template-columns:repeat({max(1,len(cv.get("steps",[])))},1fr);gap:5mm}}.cst{{display:flex;gap:3mm;border-top:1.5pt solid #CDF46B;padding-top:4mm}}.cst b{{font:900 18pt Inter;color:#CDF46B}}.cst .std{{color:#CFC3F5}}
.stt{{font:700 10.5pt Inter}}.std{{font:400 8.5pt/1.35 Inter;margin-top:1mm}}
.foot{{position:absolute;left:20mm;right:20mm;bottom:12mm;display:flex;justify-content:space-between;color:#CFC3F5}}
main{{padding:0 20mm}}.sh{{display:flex;align-items:baseline;gap:4mm;border-bottom:1.2pt solid #3B1832;padding-bottom:2.5mm;margin:8mm 0 5mm;break-after:avoid}}.sh .n{{font:700 10pt 'JetBrains Mono';color:#7A3B6C}}h2{{font:900 21pt Inter;letter-spacing:-.03em}}
p{{margin-bottom:3mm}}.lead{{font:italic 600 15pt/1.4 Lora;color:#7A3B6C;margin-bottom:5mm;border-left:2pt solid #CDF46B;padding-left:5mm}}.note{{font-size:8.5pt;color:#7A3B6C;margin:2mm 0 4mm}}
.grid{{display:grid;gap:4mm;margin-bottom:4mm}}.card{{background:#EFE7D8;border-radius:3mm;padding:5mm;break-inside:avoid}}.card h3{{font:900 12pt Inter;margin-bottom:1.5mm}}.card .k{{font:700 7.5pt 'JetBrains Mono';letter-spacing:.12em;color:#7A3B6C;text-transform:uppercase;margin-bottom:1mm}}
.dark{{background:#3B1832;color:#FBFAF6}}.dark .k{{color:#CDF46B}}ul{{padding-left:4.5mm}}li{{margin:.7mm 0}}
table{{width:100%;border-collapse:collapse;font-size:9.5pt;margin-bottom:4mm}}th{{text-align:left;font:700 7.5pt 'JetBrains Mono';letter-spacing:.1em;text-transform:uppercase;color:#7A3B6C;border-bottom:1pt solid #3B1832;padding:1.8mm}}td{{border-bottom:.5pt solid #D9CFDD;padding:1.8mm;vertical-align:top}}tr{{break-inside:avoid}}
.chk{{list-style:none;padding:0;columns:2;column-gap:8mm}}.chk li{{padding-left:6mm;position:relative;break-inside:avoid}}.chk li:before{{content:'✓';position:absolute;left:0;color:#7A3B6C;font-weight:900}}
.q{{display:grid;grid-template-columns:10mm 1fr;margin-bottom:5mm;break-inside:avoid}}.qn{{font:700 9pt 'JetBrains Mono';color:#7A3B6C;padding-top:.8mm}}.qt{{font:700 11pt/1.4 Inter}}.hint{{font-size:8.5pt;color:#7A3B6C;margin-top:.5mm}}
.ops{{margin-top:1.5mm}}.op{{display:inline-block;margin:0 5mm 1.5mm 0;font-size:10pt}}.ln{{border-bottom:.6pt solid #CDBFD4;height:8mm}}
.sw{{display:flex;gap:3mm;margin-bottom:4mm}}.sw div{{flex:1;height:26mm;border-radius:2mm;border:.6pt solid rgba(0,0,0,.12);position:relative}}.sw span{{position:absolute;left:2mm;bottom:2mm;font:700 7.5pt 'JetBrains Mono';background:rgba(255,255,255,.85);padding:.5mm 1mm;border-radius:1mm}}
.steps{{display:grid;grid-template-columns:repeat(auto-fit,minmax(35mm,1fr));gap:4mm;margin-bottom:4mm}}.st{{display:flex;gap:3mm;border-top:1.5pt solid #3B1832;padding-top:3mm;break-inside:avoid}}.st b{{font:900 16pt Inter;color:#7A3B6C}}
.pk{{display:grid;grid-template-columns:repeat(3,1fr);gap:4mm;margin-bottom:4mm}}.pc{{border:1.2pt solid #3B1832;border-radius:4mm;padding:5mm;break-inside:avoid;display:flex;flex-direction:column}}.pc.hi{{background:#3B1832;color:#FBFAF6}}
.pt{{font:700 7.5pt 'JetBrains Mono';letter-spacing:.12em;text-transform:uppercase;color:#7A3B6C}}.hi .pt{{color:#CDF46B}}.pc h3{{font:900 20pt Inter;letter-spacing:-.03em;margin:1mm 0}}.pf{{font:italic 500 10pt Lora;margin-bottom:3mm}}.pc ul{{font-size:9.5pt;flex:1}}.pp{{margin-top:4mm;font:900 13pt Inter;border-top:1pt dashed currentColor;padding-top:3mm}}
</style></head><body><div class="cover"><div class="mono" style="display:flex;justify-content:space-between;color:#CFC3F5"><span>{e(A["name"])}</span><span>{e(A["sub"])}</span></div>
<h1>{cv["title"]}</h1><div class="sub">{e(cv.get("sub",""))}</div><div class="csteps">{steps}</div><div class="foot mono"><span>{e(cv.get("foot","Məxfi"))}</span><span>{e(A["contact"])}</span></div></div><main>{body}</main></body></html>'''
hp = os.path.splitext(out)[0] + '.tmp.html'; open(hp, 'w', encoding='utf-8').write(page)
js = f"const {{chromium}}=require('/opt/node22/lib/node_modules/playwright');(async()=>{{const b=await chromium.launch();const p=await b.newPage();await p.goto('file://{os.path.abspath(hp)}');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(300);await p.pdf({{path:'{os.path.abspath(out)}',format:'A4',printBackground:true}});await b.close()}})()"
subprocess.run(['node', '-e', js], check=True); os.remove(hp); print(out)
