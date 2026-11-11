"""Brend anketi: assets/anket.json (build_doc spesifikasiyası) -> PDF + DOCX.
python3 build_anket.py <outDir>"""
import json, sys, os, subprocess
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
H = os.path.dirname(os.path.abspath(__file__)); out = sys.argv[1]; os.makedirs(out, exist_ok=True)
spec = os.path.join(H, '..', 'assets', 'anket.json'); S = json.load(open(spec, encoding='utf-8'))
subprocess.run(['python3', os.path.join(H, 'build_doc.py'), spec, os.path.join(out, 'Brend_Anketi.pdf')], check=True)
PLUM, MAUVE = '3B1832', '7A3B6C'
doc = Document()
for s in doc.sections: s.left_margin = s.right_margin = Cm(2); s.top_margin = s.bottom_margin = Cm(1.8)
doc.styles['Normal'].font.name = 'Calibri'; doc.styles['Normal'].font.size = Pt(11)
def run(p, t, size=11, bold=False, color=PLUM, italic=False):
    r = p.add_run(t); r.font.size = Pt(size); r.bold = bold; r.italic = italic; r.font.color.rgb = RGBColor.from_string(color); return r
def shade(c):
    pr = c._tc.get_or_add_tcPr(); sh = OxmlElement('w:shd'); sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto'); sh.set(qn('w:fill'), 'F3EFF6'); pr.append(sh)
run(doc.add_paragraph(), 'AYNUR MƏMMƏDOVA · BREND MENECMENT', 9, True, MAUVE)
run(doc.add_paragraph(), 'Brend anketi', 28, True)
n = sec = 0
for b in S['blocks']:
    if 'lead' in b: run(doc.add_paragraph(), b['lead'], 11, color=MAUVE, italic=True)
    elif 'h' in b:
        sec += 1; p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(14); run(p, f'{sec:02d}  {b["h"]}', 15, True)
    elif 'q' in b:
        n += 1; p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(6); run(p, f'{n:02d}. {b["q"]}', 11, True)
        if b.get('hint'): run(doc.add_paragraph(), b['hint'], 9, color=MAUVE, italic=True)
        if b.get('o'): run(doc.add_paragraph(), '     '.join('☐ ' + o for o in b['o']), 10.5)
        if b.get('lines', 0 if b.get('o') else 2):
            t = doc.add_table(rows=1, cols=1); c = t.rows[0].cells[0]; shade(c); c.paragraphs[0].text = ''
            for _ in range(b.get('lines', 2) - 1): c.add_paragraph('')
    elif 'note' in b: p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(14); run(p, b['note'], 10, True)
doc.add_paragraph(); run(doc.add_paragraph(), 'Seçimləri ☐ → ☒ edin və ya altından xətt çəkin. Faylı geri göndərin.', 9, color=MAUVE, italic=True)
doc.save(os.path.join(out, 'Brend_Anketi.docx')); print(os.path.join(out, 'Brend_Anketi.docx'))
