"""Daimi montaj kitabxanası: musiqi və B-roll (və SFX) — kiçik KATALOQ repoda, fayllar lazım olanda endirilir.

Niyə belə: hər yeni sessiyada "kitabxana yoxdur" olmasın, repo isə şişməsin və token az getsin — agent kataloqdan axtarır
(`search`), yalnız seçilmiş faylı endirir (`get`). Mənbələr:
  * mixkit  — Mixkit Free License (kommersiya pulsuz, qeyd tələb etmir); başlanğıc kataloq `seed` ilə yığılır; mühitin şəbəkəsində açıqdır
  * drive   — istifadəçinin öz fayllar qovluğu (Drive: "OpenMontage Kitabxana": musiqi/, broll/, sfx/); `sync` fayl adlarından kataloqa yazır.
              Qovluq "Linki olan hər kəs — Baxan" olmalıdır (skriptlər Drive-a anonim girir).

Fayl adı qaydası (Drive): `teq1_teq2_..._ad.mp3|mp4` — alt xətt ilə ayrılmış teqlər axtarışda istifadə olunur.
Müştərinin musiqili/musiqisiz olması burada deyil, müştəri profilindədir (`rhythm_audio.music`).

CLI:  python -m montaj.library search "kitab beyin" [--kind broll|music|sfx] [--n 5]
      python -m montaj.library get <id>            → yerli yol (keş: data_dir()/library_cache)
      python -m montaj.library sync                → Drive qovluğundakı yeni faylları kataloqa yaz
      python -m montaj.library seed                → Mixkit-dən başlanğıc kataloq (bir dəfə; yenidən işlədilsə yeniləyir)
      python -m montaj.library stats
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

CATALOG = Path(__file__).parent / "library" / "catalog.json"
DRIVE_ROOT_ID = "1KxLir8Y0FEf4HOC1HQ8KkWVS4U-gMG21"  # "OpenMontage Kitabxana" (Drive, 2026-11-25-dən yeni hesab); alt qovluqlar: musiqi, broll, sfx
DRIVE_SUB = {"music": "17aahDHsPYiEMT-y6P73qEW3QzAOMw7aV", "broll": "1WunrdEDYxcNY6l2G3AaZVgrD2mrF7EG5", "sfx": "1P7_R4h0RzJcYfM-WF2WMuN_QP9zQZeOT"}
# Hazır videolar (çıxış) qovluğu: "OpenMontage Hazır videolar/<müştəri>" — müştəri alt qovluğu: DRIVE_OUT_CLIENTS
DRIVE_OUT_ID = "1UCL6Gki_-UmXwctPW4uAu0ZH6GUTfiDB"
DRIVE_OUT_CLIENTS = {"xeyyam-huseynov": "1VlZsbIKazsv7c3qf56DwpcsQInB4BWKC"}
KINDS = ("music", "broll", "sfx")
# Azərbaycanca → ingiliscə axtarış sinonimləri (kataloq teqləri ingiliscədir)
SYN = {"kitab": "book library", "kitabxana": "library books", "beyin": "brain mind", "yaddaş": "memory", "yuxu": "sleep night", "telefon": "phone smartphone",
       "saat": "clock time", "vaxt": "clock time", "diqqət": "focus concentration", "öyrənmə": "study learning", "dərs": "study classroom", "məktəb": "school classroom",
       "yazı": "writing notes", "qeyd": "writing notes", "kompüter": "laptop computer", "iş": "office work", "təbiət": "nature", "şəhər": "city", "səhər": "morning sunrise",
       "qəhvə": "coffee", "sakit": "calm", "ilham": "inspiring", "dinamik": "upbeat energetic", "musiqi": "music", "plan": "planning notes", "emosional": "emotional", "enerji": "energetic dynamic", "motivasiya": "motivational inspiring", "rahat": "relaxing calm", "reklam": "corporate upbeat", "sürətli": "energetic dynamic", "hədəf": "goal target", "uşaq": "children kids"}


def load() -> dict[str, Any]:
    return json.loads(CATALOG.read_text(encoding="utf-8")) if CATALOG.exists() else {"version": 1, "drive_root": DRIVE_ROOT_ID, "items": []}


def save(cat: dict[str, Any]) -> None:
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf-8")


def _tokens(q: str) -> list[str]:
    out: list[str] = []
    for w in re.findall(r"[\wəıöüçşğİ]+", q.lower()):
        out += (SYN.get(w, w)).split()
    return out


def search(query: str, kind: str | None = None, n: int = 5, cat: dict[str, Any] | None = None, orient: str | None = None) -> list[dict[str, Any]]:
    cat = cat or load(); toks = _tokens(query); res = []
    for it in cat["items"]:
        if kind and it["kind"] != kind: continue
        if orient and it.get("orient") != orient: continue
        hay = set(it.get("tags", [])) | set(_tokens(it.get("name", "")))
        sc = sum(2 if t in it.get("tags", []) else 1 for t in toks if t in hay)
        if sc: res.append((sc + (0.5 if it.get("source") == "drive" else 0), it))  # istifadəçinin öz faylı üstün
    return [it for _, it in sorted(res, key=lambda x: -x[0])[:n]]


def _cache_dir() -> Path:
    from montaj.config import data_dir
    d = data_dir() / "library_cache"; d.mkdir(parents=True, exist_ok=True)
    return d


def get(item_id: str, cat: dict[str, Any] | None = None) -> Path:
    cat = cat or load()
    it = next((x for x in cat["items"] if x["id"] == item_id), None)
    if not it: raise KeyError(f"kataloqda yoxdur: {item_id}")
    ext = ".mp3" if it["kind"] in ("music", "sfx") else ".mp4"
    dst = _cache_dir() / f"{item_id}{ext}"
    if dst.exists() and dst.stat().st_size > 10_000: return dst
    if it.get("drive_id"):
        from montaj import drive
        try:
            tmp, _name = drive.download(f"https://drive.google.com/file/d/{it['drive_id']}/view", _cache_dir())  # (müvəqqəti yol, fayl adı)
            Path(tmp).replace(dst); return dst
        except Exception as e:  # noqa: BLE001
            if not it.get("url"): raise RuntimeError(f"Drive-dan alınmadı ({e}); qovluq 'Linki olan hər kəs — Baxan' olmalıdır") from e
    req = urllib.request.Request(it["url"], headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r: dst.write_bytes(r.read())
    return dst


# ── başlanğıc kataloq (Mixkit) ────────────────────────────────────────────────────────────────────────────────────────────
SEED_BROLL = [  # təhsil/öyrənmə/inkişaf + ümumi həyat tərzi mövzuları (müştərilər üçün geniş)
    "library books", "reading book", "studying student", "writing notes", "notebook pen", "office desk", "workspace", "brain", "neuron", "science laboratory", "thinking person", "meditation calm", "focus concentration",
    "clock time lapse", "alarm clock", "calendar", "planning", "target arrow", "success", "mountain climbing", "sunrise morning", "forest nature", "ocean waves", "rain window", "night city", "city traffic",
    "walking street", "people talking", "business meeting", "handshake", "laptop typing", "smartphone scrolling", "social media phone", "coffee cup", "tea", "kitchen cooking", "family together",
    "children playing", "school classroom", "teacher blackboard", "graduation", "exam test", "light bulb idea", "puzzle", "chess", "maze", "stairs", "road path", "compass", "hourglass", "lightning",
    "abstract particles", "abstract lines", "data network", "coding computer", "sleeping bed", "gym workout", "running", "yoga", "healthy food", "flowers", "clouds timelapse", "drone city",
    "modern architecture", "cafe", "shopping", "hands working", "painting art", "piano", "headphones music", "podcast microphone", "video camera filming", "woman portrait", "man working",
]
SEED_MUSIC = [  # əhval/janr (Mixkit musiqisi əsasən instrumentaldır)
    "calm inspiring", "ambient piano", "corporate inspiring", "uplifting", "cinematic emotional", "light electronic", "tech background", "motivational", "documentary", "lo-fi chill",
    "acoustic guitar", "soft piano", "epic cinematic", "upbeat happy", "energetic dynamic", "minimal ambient", "dreamy", "emotional strings", "hip hop beat", "jazz", "relaxing", "positive",
    "serious tension", "inspirational", "reflective", "playful", "elegant", "futuristic", "nature peaceful", "confident",
]


def _mixkit_pages3(url: str) -> str:
    """Kateqoriyanın ilk 3 səhifəsi (hər biri ~12–24 trek); sorğular arası gecikmə."""
    import time
    out = []
    for k in (1, 2, 3):
        time.sleep(1.2)
        try:
            out.append(urllib.request.urlopen(urllib.request.Request(f"{url}?page={k}", headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode("utf-8", "ignore"))
        except Exception:  # noqa: BLE001
            break
    return "".join(out)


def _polite(fn, *a, tries: int = 4):
    """Mixkit sorğu limiti (429): gecikmə + təkrar. Alınmayan sorğu atlanır, seed dayanmır."""
    import time
    for k in range(tries):
        try:
            time.sleep(1.4); return fn(*a)
        except Exception as e:  # noqa: BLE001
            if "429" in str(e) and k < tries - 1: time.sleep(10 * (k + 1)); continue
            print("  atlandı:", a[0], str(e)[:60], file=sys.stderr); return []
    return []


def seed(verbose: bool = False, only_broll: list[str] | None = None, skip_music: bool = False) -> dict[str, int]:
    from montaj import music, stock
    cat = load(); have = {x["id"] for x in cat["items"]}; added = {"broll": 0, "music": 0}
    for q in (only_broll or SEED_BROLL):
        for v in _polite(stock.mixkit, q, 5):
            iid = f"mk-v-{v['id']}"
            if iid in have: continue
            cat["items"].append({"id": iid, "kind": "broll", "name": q.title(), "tags": sorted(set(q.split())), "orient": "landscape", "res": "1280x720",
                                 "license": "Mixkit Stock Video Free License", "source": "mixkit", "url": v["url"].replace("-360.mp4", "-720.mp4"), "page": v.get("page", "")})
            have.add(iid); added["broll"] += 1
        if verbose: print("b-roll:", q, added["broll"], flush=True)
    save(cat)
    for q in ([] if skip_music else SEED_MUSIC):
        for m in _polite(lambda qq: music.mixkit_search(qq, [], 20, 400, 60, get=_mixkit_pages3), q):
            if not m.get("previews"): continue
            iid = f"mk-m-{str(m['previews'].get('preview-hq-mp3', '')).rsplit('/', 1)[-1].split('.')[0] or m['id']}"
            if iid in have: continue
            cat["items"].append({"id": iid, "kind": "music", "name": m["name"], "tags": sorted(set(q.split()) | {t.lower() for t in (m.get("tags") or []) if isinstance(t, str)}),
                                 "dur": m.get("duration"), "instrumental": True, "license": "Mixkit Stock Music Free License", "source": "mixkit",
                                 "url": m["previews"].get("preview-hq-mp3"), "page": m.get("page", "")})
            have.add(iid); added["music"] += 1
        if verbose: print("musiqi:", q, added["music"], flush=True)
    save(cat); return added


def probe_all(workers: int = 6) -> int:
    """B-roll üfüqi/şaquli və müddəti: 360p variantın başlığını ffprobe ilə oxuyur (tam endirmə yoxdur); kataloqa yazır."""
    import subprocess
    from concurrent.futures import ThreadPoolExecutor
    cat = load(); todo = [x for x in cat["items"] if x["kind"] == "broll" and x.get("source") == "mixkit" and not x.get("probed")]

    def one(it: dict[str, Any]) -> None:
        u = it["url"].replace("-720.mp4", "-360.mp4")
        try:  # ffprobe birbaşa URL-ə proksi vasitəsilə çıxa bilmir — ilk 256 KB (Range) + boru ilə
            d = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Range": "bytes=0-262143"}), timeout=30).read()
            r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration", "-of", "csv=p=0", "-"],
                               input=d, capture_output=True, timeout=30).stdout.decode().split()
            w, h = (int(x) for x in r[0].split(",")[:2]); dur = float(r[1]) if len(r) > 1 else None
        except Exception:  # noqa: BLE001
            return
        k = 720 / min(w, h)  # 720p variantın ölçüsü
        it.update(orient="vertical" if h > w else "landscape", res=f"{round(w * k)}x{round(h * k)}", probed=True, **({"dur": round(dur, 1)} if dur else {}))
    with ThreadPoolExecutor(workers) as ex: list(ex.map(one, todo))
    save(cat); return sum(1 for x in todo if x.get("probed"))


def sync() -> dict[str, int]:
    """Drive qovluğundakı faylları kataloqa yaz (fayl adı: teq1_teq2_ad.ext)."""
    from montaj import drive
    cat = load(); have = {x.get("drive_id") for x in cat["items"] if x.get("drive_id")}; added = {k: 0 for k in DRIVE_SUB}
    for kind, fid in DRIVE_SUB.items():
        try:
            files = drive.list_folder(f"https://drive.google.com/drive/folders/{fid}")
        except Exception as e:  # noqa: BLE001
            if "fayl tapılmadı" in str(e): continue  # boş qovluq — normal haldır
            raise
        for f in files:
            if f["id"] in have: continue
            stem = Path(f["name"]).stem; parts = [p.lower() for p in re.split(r"[_\-\s]+", stem) if p]
            cat["items"].append({"id": f"dr-{f['id'][:10]}", "kind": kind, "name": stem, "tags": sorted(set(parts)), "source": "drive", "drive_id": f["id"],
                                 "license": "istifadəçinin öz faylı"}); added[kind] += 1
    save(cat); return added


def _cli() -> None:
    ap = argparse.ArgumentParser(prog="python -m montaj.library"); sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("--kind", choices=KINDS); s.add_argument("--orient", choices=("vertical", "landscape")); s.add_argument("--n", type=int, default=5)
    g = sub.add_parser("get"); g.add_argument("id")
    sub.add_parser("sync"); sub.add_parser("probe"); sd = sub.add_parser("seed"); sd.add_argument("-v", action="store_true"); sub.add_parser("stats")
    a = ap.parse_args()
    if a.cmd == "search":
        for it in search(a.query, a.kind, a.n, orient=a.orient): print(f"{it['id']}  {it['kind']:5s} {it['name'][:30]:30s} {','.join(it['tags'][:5]):28s}" + (f" {it['dur']}s" if it.get("dur") else "") + (f" {it['orient']} {it['res']}" if it.get("probed") else ""))
    elif a.cmd == "get": print(get(a.id))
    elif a.cmd == "sync": print(sync())
    elif a.cmd == "probe": print("ölçüsü oxunan:", probe_all())
    elif a.cmd == "seed": print(seed(a.v))
    else:
        c = load(); print({k: sum(1 for x in c["items"] if x["kind"] == k) for k in KINDS}, "drive:", sum(1 for x in c["items"] if x.get("source") == "drive"))


if __name__ == "__main__":
    _cli()
