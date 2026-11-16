#!/usr/bin/env python3
"""Girişsiz brauzer araşdırması (Playwright). Yalnız səhifədə görünən məlumat.
  python3 research_browser.py adslib --country AZ --out ads.json "uşaq bağçası" "ana südü"      # Meta Ad Library: aktiv reklam mətnləri
  python3 research_browser.py behance --out be_dir "fashion editorial typography" "museum poster" # Behance: nəticə səhifəsinin ekran görüntüsü + layihə başlıqları
Qeyd: reklamın aktiv qalması uğurun sübutu DEYİL; Behance işləri referansdır, materialı yekun dizayna qoyulmur."""
import argparse, asyncio, json, os, re, urllib.parse
from playwright.async_api import async_playwright
ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=["adslib", "behance"]); ap.add_argument("queries", nargs="+")
ap.add_argument("--country", default="AZ"); ap.add_argument("--out", required=True); a = ap.parse_args()
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
async def main():
    res = {}
    async with async_playwright() as p:
        try: b = await p.chromium.launch()
        except Exception: b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--no-sandbox"])
        pg = await (await b.new_context(user_agent=UA, viewport={"width": 1300, "height": 2400})).new_page()
        if a.mode == "behance": os.makedirs(a.out, exist_ok=True)
        for i, q in enumerate(a.queries):
            qq = urllib.parse.quote(q)
            if a.mode == "adslib":
                await pg.goto(f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country={a.country}&q={qq}&search_type=keyword_unordered", timeout=45000)
                await pg.wait_for_timeout(7000)
                t = await pg.inner_text("body"); n = re.search(r"~?([\d,.]+) results?", t)
                blocks = [x.strip() for x in t.split("Library ID:")[1:]]
                ads = []
                for bl in blocks[:25]:
                    lines = [l for l in bl.split("\n") if l.strip()]
                    started = next((l for l in lines if l.startswith("Started running")), "")
                    sp = lines.index("Sponsored") if "Sponsored" in lines else -1
                    adv = lines[sp - 1] if sp > 0 else ""
                    body = " ".join(lines[sp + 1: sp + 8]) if sp >= 0 else ""
                    ads.append({"advertiser": adv, "started": started, "text": body[:600]})
                res[q] = {"results": n.group(1) if n else None, "ads": ads}; print(q, res[q]["results"], len(ads))
            else:
                await pg.goto(f"https://www.behance.net/search/projects/{qq}", timeout=45000); await pg.wait_for_timeout(6000)
                shot = os.path.join(a.out, f"{i:02d}.png"); await pg.screenshot(path=shot, clip={"x": 0, "y": 150, "width": 1300, "height": 1700})
                titles = await pg.eval_on_selector_all("a[href*='/gallery/']", "els=>[...new Set(els.map(e=>(e.getAttribute('title')||e.innerText||'').trim()+' | '+e.href))].filter(s=>s.length>8).slice(0,30)")
                res[q] = {"screenshot": shot, "projects": titles}; print(q, len(titles))
        await b.close()
    json.dump(res, open(a.out if a.mode == "adslib" else os.path.join(a.out, "projects.json"), "w"), ensure_ascii=False, indent=1)
asyncio.run(main())
