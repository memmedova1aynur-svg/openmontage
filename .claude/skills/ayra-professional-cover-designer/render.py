#!/usr/bin/env python3
"""HTML şablonunu JSON spec ilə doldurub Playwright ilə PNG çəkir.
  render.py <şablon.html> <spec.json> <out.png> [--w 1080 --h 1920]
Şablonda {{açar}} yer tutucuları spec-dən doldurulur; fayl yolları file:// olur."""
import sys, json, re, argparse, os, tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
ap = argparse.ArgumentParser(); ap.add_argument("tpl"); ap.add_argument("spec"); ap.add_argument("out")
ap.add_argument("--w", type=int, default=1080); ap.add_argument("--h", type=int, default=1920); ap.add_argument("--scale", type=float, default=1)
a = ap.parse_args()
spec = json.load(open(a.spec))
def val(v):
    s = str(v)
    return Path(s).resolve().as_uri() if (s.endswith((".png", ".jpg", ".jpeg", ".ttf", ".otf", ".svg", ".css")) and os.path.exists(s)) else s
html = re.sub(r"\{\{(\w+)\}\}", lambda m: val(spec.get(m.group(1), "")), open(a.tpl).read())
missing = re.findall(r"\{\{(\w+)\}\}", open(a.tpl).read()); missing = [k for k in missing if k not in spec]
if missing: print("XƏBƏRDARLIQ: spec-də yoxdur:", sorted(set(missing)))
tmp = Path(tempfile.mkdtemp()) / "page.html"; tmp.write_text(html)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": a.w, "height": a.h}, device_scale_factor=a.scale)
    pg.goto(tmp.as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(150)
    over = pg.evaluate("""() => [...document.querySelectorAll('[data-check]')].flatMap(e => { const r = e.getBoundingClientRect();
        const bad = []; if (r.left < 60 || r.top < 60 || r.right > innerWidth - 60 || r.bottom > innerHeight - 60) bad.push(e.dataset.check + ': kənara 60px-dən yaxın');
        if (e.scrollWidth > e.clientWidth + 1) bad.push(e.dataset.check + ': mətn sığmır'); return bad; })""")
    for o in over: print("YOXLAMA:", o)
    pg.screenshot(path=a.out); b.close()
print(a.out)
