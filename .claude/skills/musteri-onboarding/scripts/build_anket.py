"""Brend anketi: assets/anket.json -> PDF (təqdimat) + DOCX (doldurulan).
python3 build_anket.py <outDir> [--brand "Aynur Məmmədova" --sub "Brend Menecment" --contact "@1aynurmemmedova"]"""
import json, sys, os, subprocess, argparse, html
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
H = os.path.dirname(os.path.abspath(__file__))
a = argparse.ArgumentParser(); a.add_argument('out'); a.add_argument('--brand', default='Aynur Məmmədova')
a.add_argument('--sub', default='Brend Menecment'); a.add_argument('--contact', default='@1aynurmemmedova')
x = a.parse_args(); os.makedirs(x.out, exist_ok=True)
D = json.load(open(os.path.join(H, '..', 'assets', 'anket.json'), encoding='utf-8'))
PLUM, LIME, LAV, CREAM, MAUVE = '3B1832', 'CDF46B', 'CFC3F5', 'EFE7D8', '7A3B6C'

# ---------- PDF ----------
e = html.escape
secs = ''
n = 0
for i, s in enumerate(D['sections']):
    qs = ''
    for q in s['q']:
        n += 1
        qs += f'<div class="q"><span class="qn">{n:02d}</span><div class="qt">{e(q)}</div><div class="ln"></div><div class="ln"></div></div>'
    secs += f'<section><div class="sh"><span class="si">{i+1:02d}</span><h2>{e(s["t"])}</h2></div>{qs}</section>'
steps = ''.join(f'<div class="st"><b>{i+1}</b><div><div class="stt">{e(t)}</div><div class="std">{e(d)}</div></div></div>' for i, (t, d) in enumerate(D['steps']))
page = f'''<!doctype html><html lang="az"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&family=Lora:ital,wght@1,500;1,600&family=JetBrains+Mono:wght@500;700&display=block" rel="stylesheet">
<style>@page{{size:A4;margin:16mm 0 14mm}}@page:first{{margin:0}}*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:Inter;color:#{PLUM};-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.cover{{height:297mm;background:#{PLUM};color:#FBFAF6;padding:22mm 20mm;position:relative;page-break-after:always}}
.mono{{font-family:'JetBrains Mono';font-weight:700;letter-spacing:.18em;font-size:9pt;text-transform:uppercase}}
.cover h1{{font:900 64pt/0.95 Inter;letter-spacing:-.04em;margin-top:70mm}}.cover h1 span{{color:#{LIME}}}
.cover .sub{{font:italic 500 17pt/1.35 Lora;color:#{LAV};margin-top:10mm;max-width:150mm}}
.steps{{position:absolute;left:20mm;right:20mm;bottom:28mm;display:grid;grid-template-columns:repeat(4,1fr);gap:5mm}}
.st{{display:flex;gap:3mm;border-top:1.5pt solid #{LIME};padding-top:4mm}}.st b{{font:900 18pt Inter;color:#{LIME}}}.stt{{font:700 10.5pt Inter}}.std{{font:400 8.5pt/1.35 Inter;color:#{LAV};margin-top:1mm}}
.foot{{position:absolute;left:20mm;right:20mm;bottom:12mm;display:flex;justify-content:space-between;color:#{LAV}}}
.body{{padding:2mm 20mm 0}}
.intro{{font:italic 500 13pt/1.5 Lora;color:#{MAUVE};margin-bottom:10mm;border-left:2pt solid #{LIME};padding-left:5mm}}
section{{margin-bottom:9mm;break-inside:auto}}.sh{{display:flex;align-items:baseline;gap:4mm;border-bottom:1pt solid #{PLUM};padding-bottom:2.5mm;margin-bottom:4mm;break-after:avoid}}
.si{{font:700 10pt 'JetBrains Mono';color:#{MAUVE}}}h2{{font:900 20pt Inter;letter-spacing:-.03em}}
.q{{display:grid;grid-template-columns:10mm 1fr;column-gap:2mm;margin-bottom:5mm;break-inside:avoid}}.qn{{font:700 9pt 'JetBrains Mono';color:#{MAUVE};padding-top:1mm}}
.qt{{font:500 11pt/1.4 Inter}}.ln{{grid-column:2;border-bottom:.6pt solid #CDBFD4;height:8mm}}
.end{{margin-top:8mm;background:#{CREAM};padding:8mm;border-radius:4mm}}.end b{{font:900 14pt Inter}}.end p{{font:400 10pt/1.5 Inter;margin-top:2mm}}
</style></head><body>
<div class="cover"><div class="mono" style="display:flex;justify-content:space-between"><span>{e(x.brand)}</span><span>{e(x.sub)}</span></div>
<h1>{e(D["title"]).replace(" ","<br><span>",1)}</span></h1><div class="sub">{e(D["subtitle"])}</div>
<div class="steps">{steps}</div><div class="foot mono"><span>Məxfi · yalnız əməkdaşlıq üçün</span><span>{e(x.contact)}</span></div></div>
<div class="body"><div class="intro">{e(D["intro"])}</div>{secs}
<div class="end"><b>Təşəkkür edirik.</b><p>Anketi göndərdikdən sonra 1 iş günü ərzində sizə strateji paket təqdim olunur: brend xülasəsi, auditoriya, mövqe, Instagram profili, kontent sistemi, 3 aylıq yol xəritəsi və ilk ayın təqvimi.</p></div></div>
</body></html>'''
hp = os.path.join(x.out, 'Brend_Anketi.html'); open(hp, 'w', encoding='utf-8').write(page)
js = f"""const {{chromium}}=require('/opt/node22/lib/node_modules/playwright');(async()=>{{const b=await chromium.launch();const p=await b.newPage();await p.goto('file://{hp}');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(300);await p.pdf({{path:'{os.path.join(x.out,'Brend_Anketi.pdf')}',format:'A4',printBackground:true}});await b.close()}})()"""
subprocess.run(['node', '-e', js], check=True); os.remove(hp)

# ---------- DOCX ----------
doc = Document()
for s in doc.sections: s.left_margin = s.right_margin = Cm(2); s.top_margin = s.bottom_margin = Cm(1.8)
st = doc.styles['Normal']; st.font.name = 'Calibri'; st.font.size = Pt(11)
def shade(cell, hexc):
    tcPr = cell._tc.get_or_add_tcPr(); sh = OxmlElement('w:shd'); sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto'); sh.set(qn('w:fill'), hexc); tcPr.append(sh)
def run(p, t, size=11, bold=False, color=PLUM, italic=False):
    r = p.add_run(t); r.font.size = Pt(size); r.bold = bold; r.italic = italic; r.font.color.rgb = RGBColor.from_string(color); return r
p = doc.add_paragraph(); run(p, f'{x.brand.upper()} · {x.sub.upper()}', 9, True, MAUVE)
p = doc.add_paragraph(); run(p, D['title'], 30, True)
p = doc.add_paragraph(); run(p, D['subtitle'], 12, color=MAUVE, italic=True)
p = doc.add_paragraph(); run(p, D['intro'], 10.5)
p = doc.add_paragraph(); run(p, 'Cavabları boz qutulara yazın və faylı geri göndərin.', 10, True, MAUVE)
n = 0
for i, s in enumerate(D['sections']):
    h = doc.add_paragraph(); h.paragraph_format.space_before = Pt(14); run(h, f'{i+1:02d}  {s["t"]}', 16, True)
    for q in s['q']:
        n += 1
        t = doc.add_table(rows=2, cols=1); t.autofit = True
        c0 = t.rows[0].cells[0]; c0.paragraphs[0].text = ''; run(c0.paragraphs[0], f'{n:02d}. {q}', 11, True)
        c1 = t.rows[1].cells[0]; shade(c1, 'F3EFF6'); c1.paragraphs[0].text = ''; c1.add_paragraph(''); 
        doc.add_paragraph().paragraph_format.space_after = Pt(2)
p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(16); run(p, 'Təşəkkür edirik! Anketi göndərdikdən sonra 1 iş günü ərzində strateji paketiniz hazır olacaq.', 11, True)
doc.save(os.path.join(x.out, 'Brend_Anketi.docx')); print(os.path.join(x.out, 'Brend_Anketi.pdf')); print(os.path.join(x.out, 'Brend_Anketi.docx'))
