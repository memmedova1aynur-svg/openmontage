"""Nəticə ölçmə: Metricool reel göstəriciləri → hesabat + öyrənilənlər (brend kitinə yazılır).

  python3 metrics_report.py <müştəri> <metrics.json>
metrics.json (Claude Metricool-dan çəkib saxlayır):
  {"period": ["2026-10-01", "2026-10-31"], "followers": [başlanğıc, son],
   "reels": [{"date": "...", "url": "...", "text": "...", "reach": 0, "views": 0, "watch": 0, "duration": 0,
              "retention": 0, "viewRate": 0, "likes": 0, "comments": 0, "saves": 0, "shares": 0}, ...]}
Paylaşım jurnalı instagram-clients/<müştəri>/posted.json: [{"url": "...", "file": "...", "tags": {"hook": "sual", "kart": "editorial", ...}}]
Çıxış: instagram-clients/<müştəri>/hesabat_<tarix>.html və brand_kit.json → "learnings".
"""
import html, json, statistics as st, sys
from pathlib import Path
import kit

CL = sys.argv[1]; M = json.load(open(sys.argv[2]))
D = Path(kit.A.parent.parent.parent / "instagram-clients" / CL); kitf = D / "brand_kit.json"
posted = {p["url"]: p for p in (json.load(open(D / "posted.json")) if (D / "posted.json").exists() else [])}
R = M.get("reels", [])
for r in R:
    r["eng"] = (r.get("saves", 0) * 3 + r.get("shares", 0) * 4 + r.get("comments", 0) * 2 + r.get("likes", 0)) / max(1, r.get("reach", 0)) * 100
    r["tags"] = posted.get(r.get("url"), {}).get("tags", {})
def med(k): v = [r[k] for r in R if r.get(k)]; return round(st.median(v), 2) if v else None
L = {"period": M.get("period"), "reels": len(R), "median": {k: med(k) for k in ("reach", "retention", "viewRate", "watch", "eng")}}
by = {}
for r in R:
    for k, v in r["tags"].items(): by.setdefault(f"{k}={v}", []).append(r)
L["byTag"] = {t: {"n": len(rs), "retention": round(st.mean(x.get("retention", 0) for x in rs), 1), "eng": round(st.mean(x["eng"] for x in rs), 2)}
              for t, rs in sorted(by.items()) if len(rs) >= 2}  # tək nümunədən nəticə çıxarılmır
dur = {"<30s": [], "30–60s": [], ">60s": []}
for r in R: dur["<30s" if r.get("duration", 0) < 30 else "30–60s" if r.get("duration", 0) <= 60 else ">60s"].append(r)
L["byDuration"] = {k: {"n": len(v), "retention": round(st.mean(x.get("retention", 0) for x in v), 1)} for k, v in dur.items() if v}
top = sorted(R, key=lambda r: r["eng"], reverse=True)[:3]
L["top"] = [{"url": r.get("url"), "text": (r.get("text") or "")[:80], "eng": round(r["eng"], 2), "retention": r.get("retention")} for r in top]
if kitf.exists():
    k = json.load(open(kitf)); k["learnings"] = L; json.dump(k, open(kitf, "w"), ensure_ascii=False, indent=1)

f0, f1 = (M.get("followers") or [None, None]) + [None] * (2 - len(M.get("followers") or []))
def bar(v, mx, c="#6CC57E"): return f'<div style="background:#eee;border-radius:6px;height:12px"><div style="width:{0 if not mx else 100 * (v or 0) / mx:.0f}%;background:{c};height:12px;border-radius:6px"></div></div>'
mx = max([r["eng"] for r in R] or [1])
rows = "".join(f'<tr><td>{html.escape(str(r.get("date", ""))[:10])}</td><td>{html.escape((r.get("text") or "")[:60])}</td><td>{r.get("reach", 0)}</td>'
               f'<td>{r.get("retention", "—")}</td><td>{r.get("saves", 0)}</td><td>{r.get("shares", 0)}</td><td style="width:140px">{bar(r["eng"], mx)}</td></tr>' for r in sorted(R, key=lambda r: r.get("date", "")))
tags = "".join(f'<li><b>{html.escape(t)}</b>: {v["n"]} reel · izləmə {v["retention"]}% · təsir {v["eng"]}</li>' for t, v in L["byTag"].items()) or "<li>Hələ kifayət qədər nümunə yoxdur (hər qrupda ən az 2 reel lazımdır).</li>"
page = f"""<!doctype html><html lang="az"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hesabat — {html.escape(CL)}</title>
<style>body{{font-family:-apple-system,system-ui,sans-serif;margin:0;background:#f6f6f3;color:#1d1d1b}}main{{max-width:900px;margin:0 auto;padding:20px}}
.k{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}}.c{{background:#fff;border-radius:14px;padding:16px}}.c b{{font-size:28px;display:block}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:14px;overflow:hidden;font-size:14px}}td,th{{padding:8px;border-bottom:1px solid #eee;text-align:left}}</style></head>
<body><main><h1>{html.escape(CL)} · {html.escape(" — ".join(M.get("period") or []))}</h1>
<div class="k"><div class="c">İzləyici<b>{f1 if f1 is not None else "—"}</b>{f"+{f1 - f0}" if f0 is not None and f1 is not None else ""}</div>
<div class="c">Reel<b>{len(R)}</b></div><div class="c">Median çatma<b>{L["median"]["reach"] or "—"}</b></div>
<div class="c">Median izləmə<b>{L["median"]["retention"] or "—"}%</b></div><div class="c">3 s-dən sonra qalan<b>{L["median"]["viewRate"] or "—"}%</b></div></div>
<h2>Nə işləyir</h2><ul>{tags}</ul><h2>Uzunluq</h2><ul>{"".join(f"<li>{k}: {v['n']} reel · izləmə {v['retention']}%</li>" for k, v in L["byDuration"].items()) or "<li>—</li>"}</ul>
<h2>Bütün reellər</h2><table><tr><th>tarix</th><th>mətn</th><th>çatma</th><th>izləmə %</th><th>save</th><th>share</th><th>təsir</th></tr>{rows or '<tr><td colspan=7>Bu dövrdə reel məlumatı yoxdur.</td></tr>'}</table>
<p style="color:#888;font-size:12px">Təsir = (save×3 + share×4 + şərh×2 + like) / çatma × 100. Mənbə: Metricool.</p></main></body></html>"""
out = D / f"hesabat_{(M.get('period') or ['x', 'x'])[1]}.html"; out.write_text(page, encoding="utf-8")
print(f"hesabat: {out} · reel {len(R)} · öyrənilənlər brend kitinə yazıldı" if kitf.exists() else f"hesabat: {out}")
