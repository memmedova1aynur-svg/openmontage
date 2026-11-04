"""Mərhələ 1 — qəbul: Drive linklərindən layihələr (paralel).

İstifadə:
  python3 ingest.py batch.json
batch.json:
  {"client": "Xəyyam Hüseynov", "prefix": "xeyyam-video", "start": 9,
   "videos": [{"link": "https://drive.google.com/...", "type": "talk|ad", "title": "Təxirəsalma", "script": "(istəyə görə)"}]}

Hər video üçün: endir → ASR + storyboard → kadraj (framefix) → <PRO_WORK>/vN.json qaralama
(danışığa sadiq mətn, növ, ev qaydaları) + vN_words.txt (vaxtlı sözlər — səhnə planı üçün).
Səhnələri (scenes) Claude yazır; sonra batch.py hamısını paralel qurur.
"""
import json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

A = Path(__file__).resolve().parent; REPO = A.parent.parent.parent
DATA = Path(os.environ.get("MONTAJ_DATA_DIR", "/root/montaj-data"))
WORK = Path(os.environ.get("PRO_WORK", str(DATA / "plans" / "pro"))); WORK.mkdir(parents=True, exist_ok=True)
ENV = {**os.environ, "MONTAJ_DATA_DIR": str(DATA), "MONTAJ_OUT_DIR": str(DATA / "out")}
B = json.load(open(sys.argv[1]))


def sh(*args):
    r = subprocess.run([sys.executable, "-m", "montaj.session", *args], cwd=REPO, env=ENV, capture_output=True, text=True)
    if r.returncode: raise RuntimeError(f"{args[0]}: {(r.stderr or r.stdout)[-600:]}")
    return r.stdout


def one(k, v):
    n = B.get("start", 1) + k
    title = f"{B.get('prefix', 'video')} {n}".replace("-", " ").title()
    out = sh("new", "--title", title, "--link", v["link"], *(["--client", B["client"]] if B.get("client") else []), "--cut", "auto")
    pid = re.search(r"layihə: (\S+)", out).group(1)
    sh("storyboard", pid)
    try: sh("framefix", pid)
    except RuntimeError as e: print(f"v{n}: framefix xəbərdarlığı: {e}")
    P = DATA / "projects" / pid
    af = next((P / "analysis").glob("*.json"))
    a = json.load(open(af)); kw, ks = ("word", "start") if "word" in a["words"][0] else ("w", "s")
    words = [(w[kw], w[ks]) for w in a["words"]]
    text = v.get("script") or " ".join(w for w, _ in words)
    slug = re.sub(r"[^A-Za-z0-9]+", "", (v.get("title") or f"Video{n}").title().replace(" ", ""))
    cfg = {"n": n, "pid": pid, "type": v.get("type", "talk"), "ad": v.get("type") == "ad",
           "title": f"{n:02d} {v.get('title', '')} — PRO", "file": f"{n:02d}_{slug}", "text": text, "scenes": []}
    dst = WORK / f"v{n}.json"
    if dst.exists() and json.load(open(dst)).get("scenes"): print(f"v{n}: mövcud səhnələr saxlanıldı"); return n, pid
    json.dump(cfg, open(dst, "w"), ensure_ascii=False, indent=1)
    (WORK / f"v{n}_words.txt").write_text("\n".join(f"{s:7.2f}  {w}" for w, s in words), encoding="utf-8")
    print(f"v{n}: {pid}  {len(words)} söz → {dst}")
    return n, pid


with ThreadPoolExecutor(max_workers=int(os.environ.get("PRO_INGEST_JOBS", "3"))) as ex:
    res = list(ex.map(lambda kv: one(*kv), enumerate(B["videos"])))
print("QƏBUL BİTDİ:", res)
