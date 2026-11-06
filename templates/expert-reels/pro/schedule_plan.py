"""Paylaşım planı: hazır videolar + Metricool ən yaxşı saatları → tarix/saat cədvəli və Metricool qaralamaları.

  python3 schedule_plan.py <müştəri> <plan.json>
plan.json:
  {"start": "2026-11-10", "perWeek": 3, "tz": "Asia/Baku", "blogId": "...",
   "best": [{"day": 1..7, "hour": 0..23, "value": n}, ...],          # getBestTimeToPostByNetwork nəticəsi
   "items": [{"id": "07", "kind": "reel|post|carousel", "media": ["<Drive linki>"], "cover": "<Drive linki>", "caption": "..."}]}
Grid qaydası: iki reel ardıcıl düşmür (reellər griddə yan-yana olmasın).
Çıxış: <plan>_cədvəl.md və <plan>_metricool.json (hər element üçün createScheduledPost "info", draft=true).
Claude yalnız istifadəçi təsdiqindən sonra bu qaralamaları Metricool-a göndərir.
"""
import datetime as dt, json, sys
from pathlib import Path

CL = sys.argv[1]; P = json.load(open(sys.argv[2])); items = list(P["items"])
order = []  # reellər arasında ən az bir post
while items:
    nxt = next((x for x in items if not (order and order[-1]["kind"] == "reel" and x["kind"] == "reel")), items[0]); items.remove(nxt); order.append(nxt)
best = sorted(P.get("best", []), key=lambda b: -b["value"])
slots_by_day = {}
for b in best: slots_by_day.setdefault(b["day"], b["hour"])
days = sorted(slots_by_day, key=lambda d: -max(x["value"] for x in best if x["day"] == d))[:P.get("perWeek", 3)] or [1, 3, 5]
start = dt.date.fromisoformat(P["start"]); out, k, d = [], 0, start
while k < len(order):
    if d.isoweekday() in days:
        h = slots_by_day.get(d.isoweekday(), 19); it = order[k]; k += 1
        when = f"{d.isoformat()}T{h:02d}:{7 + 3 * (k % 4):02d}:00"  # dəqiqə 00 deyil (növbə yükü)
        ig = {"type": "REEL" if it["kind"] == "reel" else "POST", "showReelOnFeed": True}
        info = {"autoPublish": True, "draft": True, "text": it.get("caption", ""), "media": it.get("media", []), "providers": [{"network": "instagram"}],
                "publicationDate": {"dateTime": when, "timezone": P.get("tz", "Asia/Baku")}, "instagramData": ig, "firstCommentText": "", "shortener": False,
                "smartLinkData": {"ids": []}, "descendants": [], "hasNotReadNotes": False, "mediaAltText": []}
        if it.get("cover") and it["kind"] == "reel": info["videoThumbnailUrl"] = it["cover"]
        out.append({"id": it["id"], "kind": it["kind"], "when": when, "info": info})
    d += dt.timedelta(days=1)
base = Path(sys.argv[2]).with_suffix("")
Path(f"{base}_metricool.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
wd = ["", "B.e.", "Ç.a.", "Ç.", "C.a.", "C.", "Ş.", "B."]
md = [f"# Paylaşım cədvəli — {CL}", "", "| # | tarix | saat | növ | element | media |", "|---|---|---|---|---|---|"]
for i, o in enumerate(out, 1):
    t = dt.datetime.fromisoformat(o["when"]); md.append(f"| {i} | {wd[t.isoweekday()]} {t:%d.%m} | {t:%H:%M} | {o['kind']} | {o['id']} | {'✓' if o['info']['media'] else 'link lazımdır'} |")
clash = [out[i]["id"] for i in range(1, len(out)) if out[i]["kind"] == out[i - 1]["kind"] == "reel"]
if clash: md += ["", f"⚠ Reellər ardıcıl düşür ({', '.join(clash)}): araya post/karusel əlavə edin ki, griddə yan-yana olmasın."]
md += ["", "Qaralama kimi göndərilir (draft). Təsdiqdən sonra Metricool-da yayına hazır olur."]
Path(f"{base}_cədvəl.md").write_text("\n".join(md), encoding="utf-8"); print(f"cədvəl: {len(out)} paylaşım → {base}_cədvəl.md")
