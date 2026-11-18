#!/usr/bin/env python3
"""YouTube axtarış nəticələri (başlıq, kanal, görünən baxış sayı, tarix) — açarsız, Playwright ilə.
  python3 research_youtube.py --gl AZ --hl az --out youtube.json "bağçaya adaptasiya" "tərbiyəçi üçün" ...
Yalnız axtarış səhifəsində görünən məlumat; videonun məzmunu baxılmadan təsvir edilmir."""
import argparse, asyncio, json, re
from playwright.async_api import async_playwright
ap = argparse.ArgumentParser(); ap.add_argument("queries", nargs="+"); ap.add_argument("--gl", default="AZ"); ap.add_argument("--hl", default="az"); ap.add_argument("--out", required=True); ap.add_argument("--n", type=int, default=15)
a = ap.parse_args()
def walk(o, items):
    if isinstance(o, dict):
        if "videoRenderer" in o:
            v = o["videoRenderer"]; j = lambda k: "".join(r.get("text", "") for r in v.get(k, {}).get("runs", []))
            items.append({"id": v.get("videoId"), "url": f"https://www.youtube.com/watch?v={v.get('videoId')}", "title": j("title"), "channel": j("ownerText"),
                          "views": v.get("viewCountText", {}).get("simpleText") or j("viewCountText"), "age": v.get("publishedTimeText", {}).get("simpleText", "")})
        for x in o.values(): walk(x, items)
    elif isinstance(o, list):
        for x in o: walk(x, items)
async def main():
    res = {}
    async with async_playwright() as p:
        try: b = await p.chromium.launch()
        except Exception: b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--no-sandbox"])
        pg = await (await b.new_context(locale=f"{a.hl}-{a.gl}")).new_page()
        for q in a.queries:
            await pg.goto(f"https://www.youtube.com/results?search_query={q.replace(' ', '+')}&gl={a.gl}&hl={a.hl}", timeout=40000); await pg.wait_for_timeout(3000)
            m = re.search(r"var ytInitialData = (\{.*?\});</script>", await pg.content()); items = []
            if m: walk(json.loads(m.group(1)), items)
            res[q] = items[:a.n]; print(q, len(items))
        await b.close()
    json.dump(res, open(a.out, "w"), ensure_ascii=False, indent=1)
asyncio.run(main())
