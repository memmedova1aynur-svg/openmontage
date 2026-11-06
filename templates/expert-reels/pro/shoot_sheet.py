"""Çəkiliş vərəqi: bir səhifəlik, çap olunan / telefonda açılan HTML.

  python3 shoot_sheet.py <çəkiliş.json>
çəkiliş.json:
  {"client": "Nərgiz", "date": "2026-11-12", "place": "...", "looks": ["qara köynək", "bej pencək"],
   "videos": [{"n": 1, "title": "Cambridge metodu nədir?", "type": "talk|ad|short", "look": 0,
               "prompts": ["Bu təlimdə nə öyrənirik?", "..."], "note": "kameraya yox, sual verənə bax"}]}
Çıxış: <çəkiliş>.html — video sırası (paltar dəyişikliyinə görə qruplaşdırılır), suallar, texniki checklist.
"""
import html, json, sys
from pathlib import Path

P = json.load(open(sys.argv[1])); V = sorted(P["videos"], key=lambda v: (v.get("look", 0), v.get("n", 0)))
looks = P.get("looks") or ["—"]; e = html.escape
blocks, cur = [], None
for v in V:
    if v.get("look", 0) != cur:
        cur = v.get("look", 0); blocks.append(f'<h2>Görünüş {cur + 1}: {e(looks[cur] if cur < len(looks) else "")}</h2>')
    blocks.append(f'''<div class="v"><div class="h"><span class="n">{v.get("n", "")}</span><b>{e(v["title"])}</b><span class="t">{e({"talk": "danışıq", "ad": "reklam", "short": "qısa"}.get(v.get("type"), v.get("type", "")))}</span><span class="ck">☐</span></div>
<ol>{"".join(f"<li>{e(q)}</li>" for q in v.get("prompts", []))}</ol>{f'<p class="note">{e(v["note"])}</p>' if v.get("note") else ""}</div>''')
check = ["Telefon şaquli, 1080p/4K, 25–30 fps", "Taxma mikrofon üzə yaxın, sınaq yazısı dinlənildi", "Kondisioner/ventilyator sönülü, qapı bağlı",
         "İşıq üzə qarşıdan (pəncərə və ya softbox), arxada pəncərə yoxdur", "Kamera göz səviyyəsində, tripodda", "Ekspoziya və fokus kilidləndi (ekrana uzun basın)",
         "Hər videodan əvvəl 2 s sükut, sonunda 2 s sükut", "Səhv olanda dayanmayın — cümləni yenidən deyin, montajda kəsilir",
         "10 s sınaq kadrı → preflight yoxlaması HAZIR", "Uşaq kadrdadırsa: valideyn razılıq forması imzalanıb"]
page = f"""<!doctype html><html lang="az"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Çəkiliş — {e(P.get("client", ""))}</title>
<style>body{{font-family:-apple-system,system-ui,sans-serif;margin:0;color:#1d1d1b}}main{{max-width:760px;margin:0 auto;padding:20px}}h1{{margin:0}}h2{{margin-top:26px;border-bottom:2px solid #1d1d1b;padding-bottom:4px}}
.v{{border:1px solid #ddd;border-radius:12px;padding:12px 14px;margin:10px 0;break-inside:avoid}}.h{{display:flex;gap:10px;align-items:center}}.n{{background:#1d1d1b;color:#fff;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-weight:700}}
.t{{margin-left:auto;font-size:12px;color:#777}}.ck{{font-size:22px}}ol{{margin:8px 0 0 18px}}li{{margin:4px 0}}.note{{color:#8a5a00;font-size:14px;margin:8px 0 0}}.c li{{list-style:"☐  "}}
@media print{{main{{padding:0}}}}</style></head><body><main><h1>Çəkiliş vərəqi · {e(P.get("client", ""))}</h1>
<p>{e(P.get("date", ""))} · {e(P.get("place", ""))} · {len(V)} video</p><h2>Texniki yoxlama</h2><ul class="c">{"".join(f"<li>{e(c)}</li>" for c in check)}</ul>{"".join(blocks)}</main></body></html>"""
out = Path(sys.argv[1]).with_suffix(".html"); out.write_text(page, encoding="utf-8"); print(f"çəkiliş vərəqi: {out} ({len(V)} video)")
