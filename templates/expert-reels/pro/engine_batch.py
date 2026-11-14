"""Paket rejimi: bir neçə video paralel (standart 2 xətt — 4 nüvəli CPU üçün ölçülmüş optimum), uğursuz video digərlərini dayandırmır.

İstifadə: python3 engine_batch.py paket.json
paket.json: {"client": "...", "work": "/yol", "lanes": 2, "videos": [{"src": "/yol/IMG.MOV", "name": "01_movzu", "title": "Sətir|Sətir"}]}
Çıxış: <work>/paket.json — hər video: QC, mərhələ vaxtları; paket ümumi vaxtı (faktiki ölçü).
"""
import json, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
A = Path(__file__).resolve().parent
P = json.load(open(sys.argv[1])); W = Path(P["work"]); W.mkdir(parents=True, exist_ok=True); T0 = time.time()
sys.path.insert(0, str(A)); import deliver
DAY = time.strftime("%Y-%m-%d")


def one(v):
    t = time.time(); wd = W / v["name"]; wd.mkdir(exist_ok=True)
    cmd = [sys.executable, str(A / "engine.py"), v["src"], "--client", P["client"], "--name", v["name"], "--work", str(wd)] + (["--title", v["title"]] if v.get("title") else [])
    r = subprocess.run(cmd, stdout=open(wd / "log.txt", "w"), stderr=subprocess.STDOUT)
    res = json.load(open(wd / "engine.json")) if (wd / "engine.json").exists() else {"video": v["name"], "qc": "XƏTA"}
    res["wall_s"] = round(time.time() - t, 1)
    try: deliver.set_status(P["client"], DAY, v["name"], "QC keçdi" if res.get("qc") == "KEÇDİ" else "düzəliş tələb edir", res.get("qc_line", "")[:200])
    except Exception: pass
    print(f"[{time.time() - T0:6.0f}s] {v['name']}: {res.get('qc')} ({res['wall_s']} s, video {res.get('out_dur')} s)", flush=True)
    return res


with ThreadPoolExecutor(max_workers=int(P.get("lanes", 2))) as ex:
    out = list(ex.map(one, P["videos"]))
tot = round(time.time() - T0, 1); vid = round(sum(r.get("out_dur", 0) for r in out), 1)
summary = {"total_wall_s": tot, "videos": len(out), "qc_passed": sum(r.get("qc") == "KEÇDİ" for r in out), "output_s": vid,
           "wall_per_output_min": round(tot / max(1, vid), 2), "results": out}
json.dump(summary, open(W / "paket.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in summary.items() if k != "results"}, ensure_ascii=False))
