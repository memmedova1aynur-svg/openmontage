"""Mərhələ 2 — paralel montaj + QA darvazası.

İstifadə: python3 batch.py v9.json v10.json ...   (və ya: python3 batch.py --all)
PRO_LANES (standart 3) paralel xətt. Hər video build.py → render → qa.py.
QA keçməyən video "HAZIR" siyahısına düşmür; səbəbi qa.json-dadır.
"""
import json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
A = Path(__file__).resolve().parent
DATA = Path(os.environ.get("MONTAJ_DATA_DIR", "/root/montaj-data"))
WORK = Path(os.environ.get("PRO_WORK", str(DATA / "plans" / "pro")))
sys.path.insert(0, str(A)); import sfx_premium; sfx_premium.ensure()
cfgs = sorted(WORK.glob("v*.json"), key=lambda p: int(p.stem[1:])) if sys.argv[1:] == ["--all"] else [Path(x) for x in sys.argv[1:]]
cfgs = [c if c.is_absolute() or c.exists() else WORK / c for c in cfgs]
T0 = time.time()


def build(c):
    t = time.time(); log = WORK / f"{c.stem}.log"
    r = subprocess.run([sys.executable, str(A / "build.py"), str(c)], stdout=open(log, "w"), stderr=subprocess.STDOUT)
    out = log.read_text()
    ready = next((l.split()[1] for l in out.splitlines() if l.startswith("HAZIR")), None)
    qa = next((l for l in out.splitlines() if l.startswith("QA ")), "QA yoxdur")
    st = "OK" if r.returncode == 0 else ("QA" if r.returncode == 3 else "XƏTA")
    print(f"[{time.time() - T0:5.0f}s] {c.stem}: {st} ({time.time() - t:.0f}s) {ready or ''}\n    {qa[:300]}", flush=True)
    return c.stem, st, ready


with ThreadPoolExecutor(max_workers=int(os.environ.get("PRO_LANES", "3"))) as ex:
    res = list(ex.map(build, cfgs))
print("\nNƏTİCƏ:", json.dumps(res, ensure_ascii=False))
print("HAZIR (QA keçdi):", [r[2] for r in res if r[1] == "OK"])
