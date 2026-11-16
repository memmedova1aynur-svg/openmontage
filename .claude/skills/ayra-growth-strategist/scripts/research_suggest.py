#!/usr/bin/env python3
"""Google axtarış təklifləri (autocomplete) — açarsız. Axtarış HƏCMİ deyil, yalnız insanların nə yazdığını göstərir.
  python3 research_suggest.py --hl az --out teklifler.json "uşaq bağçada" "ana südü" ...   (hər açar söz + ' niyə', ' nə' variantları)"""
import argparse, json, time, urllib.parse, urllib.request
ap = argparse.ArgumentParser(); ap.add_argument("seeds", nargs="+"); ap.add_argument("--hl", default="az"); ap.add_argument("--gl", default="az"); ap.add_argument("--out", required=True)
ap.add_argument("--suffixes", default=", niyə, nə"); a = ap.parse_args()
res = {}
for s in a.seeds:
    out = set()
    for suf in a.suffixes.split(","):
        q = (s + " " + suf.strip()).strip()
        try:
            u = f"https://suggestqueries.google.com/complete/search?client=firefox&hl={a.hl}&gl={a.gl}&q=" + urllib.parse.quote(q)
            r = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=10).read())
            out.update(x for x in r[1] if x != q)
        except Exception as e:
            print("[!]", q, e)
        time.sleep(0.2)
    res[s] = sorted(out)
json.dump(res, open(a.out, "w"), ensure_ascii=False, indent=1)
print(sum(len(v) for v in res.values()), "təklif →", a.out)
