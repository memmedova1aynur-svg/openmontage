"""AYRA Visual Research — ortaq funksiyalar (axtarış, yükləmə, metadata, lisenziya yoxlaması).

Yalnız Python stdlib + Pillow. Açar tələb etmir.
Mənbə: Openverse API (Wikimedia Commons, Flickr, StockSnap, Rawpixel və s. indeksləyir).
"""
import json, os, re, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]          # repo kökü
LIB = Path(os.environ.get("AYRA_LIBRARY", ROOT / "assets" / "ayra-library"))
UA = "AYRADesignResearch/1.0 (design research; respects licences)"
FOLDERS = ["real-photos", "product-cutouts", "education", "montessori", "toys", "motherhood",
           "books", "mockups", "textures", "icons", "client-portraits", "licenses"]

# Kommersiya + dəyişdirmə icazəsi olan lisenziyalar
OK_LICENSES = {"cc0", "pdm", "by", "by-sa"}
NOTES = {"cc0": "Atribusiya tələb olunmur.",
         "pdm": "İctimai mülkiyyət.",
         "by": "Müəllif adı göstərilməlidir (caption/ilk şərh).",
         "by-sa": "Müəllif adı göstərilməlidir; dəyişdirilmiş şəkil eyni lisenziya ilə paylaşılmalıdır (ShareAlike)."}


def http(url, data=None, timeout=30, retries=3):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read(), r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 503):
                time.sleep(2 * (i + 1)); continue
            raise
        except Exception as e:  # şəbəkə xətası
            last = e; time.sleep(1 + i)
    raise last


def wikimedia_thumb(url, width=1280):
    """upload.wikimedia.org orijinal URL → icazəli standart thumbnail ölçüsü (960/1280)."""
    m = re.match(r"https://upload\.wikimedia\.org/wikipedia/commons/(\w)/(\w\w)/(.+)$", url)
    if not m or url.lower().endswith(".svg"):
        return url
    a, b, name = m.groups()
    return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{a}/{b}/{name}/{width}px-{name}"


def openverse(q, n=20, page=1, commercial=True, category="photograph", source=None, aspect=None):
    p = {"q": q, "page_size": n, "page": page}
    if commercial:
        p["license_type"] = "commercial,modification"
    if category:
        p["category"] = category
    if source:
        p["source"] = source
    if aspect:
        p["aspect_ratio"] = aspect
    raw, _ = http("https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(p))
    out = []
    for r in json.loads(raw).get("results", []):
        lic = (r.get("license") or "").lower()
        if commercial and lic not in OK_LICENSES:
            continue
        out.append({
            "id": r["id"], "title": r.get("title") or "", "creator": r.get("creator") or "naməlum",
            "creator_url": r.get("creator_url"), "license": lic, "license_version": r.get("license_version"),
            "license_url": r.get("license_url"), "source": r.get("source"), "provider": r.get("provider"),
            "landing": r.get("foreign_landing_url"), "url": r.get("url"),
            "download": wikimedia_thumb(r.get("url") or "") if r.get("source") == "wikimedia" else r.get("url"),
            "thumb": r.get("thumbnail"), "w": r.get("width"), "h": r.get("height"),
            "tags": [t.get("name") for t in (r.get("tags") or [])][:15], "query": q,
        })
    return out


def attribution(m):
    lic = m["license"].upper().replace("BY", "CC BY") if m["license"] in ("by", "by-sa") else m["license"].upper()
    v = f" {m['license_version']}" if m.get("license_version") else ""
    return f"“{m['title']}” — {m['creator']} ({m['source']}), {lic}{v}. {m.get('landing') or ''}".strip()


def library_index():
    p = LIB / "index.json"
    return json.loads(p.read_text()) if p.exists() else []


def library_search(q):
    words = [w for w in re.split(r"\W+", q.lower()) if len(w) > 2]
    res = []
    for m in library_index():
        hay = " ".join([m.get("title", ""), m.get("topic", ""), " ".join(m.get("tags", [])), m.get("query", "")]).lower()
        score = sum(w in hay for w in words)
        if score:
            res.append((score, m))
    return [m for s, m in sorted(res, key=lambda x: -x[0])]


def save_index(items):
    LIB.mkdir(parents=True, exist_ok=True)
    (LIB / "index.json").write_text(json.dumps(items, ensure_ascii=False, indent=1))
