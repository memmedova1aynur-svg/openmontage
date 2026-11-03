"""Musiqi — Claude özü seçir, istifadəçidən "necə qoyum" soruşulmur.

* Mənbə: Freesound, YALNIZ CC0 (müəllif qeydi tələb etmir) — `FREESOUND_API_KEY` (pulsuz).
* Sorğu avtomatik: müştəri profilinin `music` sahəsi (query, avoid), yoxdursa video növü / mövzu üzrə standart.
  İstifadəçi qaydası (2026-11-01, bütün müştərilər): piano / yavaş / kədərli YOX; uşaq inkişafı mövzusunda şən kids,
  təhsil reklamında educational/corporate.
* Yerləşmə (standart, soruşulmur): Reels — bütün video boyu, danışıqda azalır (ducking); kurs dərsi — yalnız açılışda və
  sonda qısa, çox yumşaq (dərs boyu musiqi yoxdur).
"""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API = "https://freesound.org/apiv2/search/text/"
AVOID = ["piano", "sad", "slow", "dark", "horror", "ambient drone"]
CC0 = 'license:"Creative Commons 0"'

# video növü → standart sorğu (müştəri profilində `music.query` varsa o üstündür)
BY_TYPE = {
    1: "upbeat positive background", 2: "upbeat positive background", 3: "corporate upbeat background",
    4: "inspiring corporate background", 5: "upbeat motivational", 6: "happy acoustic background", 7: "upbeat motivational",
    8: "inspiring corporate background", 9: "children fairy tale happy", 10: "funny happy ukulele", 11: "light corporate background",
    12: "upbeat positive background", 13: "light corporate background", 14: "warm acoustic background",
    15: "soft corporate background", 16: "technology corporate upbeat",
}
KIDS_WORDS = ("uşaq", "körpə", "ana", "laktasiya", "analıq", "bağça", "məktəbəqədər", "kids", "child")


def auto_query(profile: dict[str, Any] | None, vtype: int | None, goal: str = "") -> tuple[str, list[str]]:
    """(sorğu, qaçınılan sözlər): profil → mövzu (uşaq) → reklam → növ."""
    pm = (profile or {}).get("music") or {}
    avoid = list(dict.fromkeys(AVOID + list(pm.get("avoid") or [])))
    if pm.get("query"):
        return pm["query"], avoid
    act = ((profile or {}).get("activity") or "").lower()
    if any(w in act for w in KIDS_WORDS) and vtype not in (15,):
        return "kids happy ukulele background", avoid
    if vtype in (3, 8) or "reklam" in (goal or "").lower():
        return "corporate upbeat background", avoid
    return BY_TYPE.get(int(vtype or 1), "upbeat positive background"), avoid


def search(query: str, avoid: list[str], min_dur: float, max_dur: float, n: int = 3) -> list[dict[str, Any]]:
    key = os.environ.get("FREESOUND_API_KEY")
    if not key:
        raise RuntimeError("FREESOUND_API_KEY yoxdur")
    q = query + "".join(f" -{w.split()[0]}" for w in avoid)
    params = urllib.parse.urlencode({"query": q, "filter": f"{CC0} duration:[{int(min_dur)} TO {int(max_dur)}]",
                                     "sort": "rating_desc", "fields": "id,name,duration,previews,tags,avg_rating,username,license",
                                     "page_size": 30, "token": key})
    with urllib.request.urlopen(urllib.request.Request(f"{API}?{params}", headers={"User-Agent": "montaj"}), timeout=30) as r:
        res = json.loads(r.read().decode("utf-8")).get("results", [])
    out = []
    for s in res:
        lic = str(s.get("license") or "")
        tags = " ".join(s.get("tags") or []).lower() + " " + str(s.get("name", "")).lower()
        if "publicdomain/zero" not in lic and "Creative Commons 0" not in lic:
            continue  # yalnız CC0
        if any(re.search(rf"\b{re.escape(w.split()[0])}\b", tags) for w in avoid):
            continue
        out.append(s)
        if len(out) >= n:
            break
    return out


def download(sounds: list[dict[str, Any]], dst: Path) -> list[dict[str, Any]]:
    dst.mkdir(parents=True, exist_ok=True)
    done = []
    for i, s in enumerate(sounds, 1):
        url = (s.get("previews") or {}).get("preview-hq-mp3") or (s.get("previews") or {}).get("preview-lq-mp3")
        if not url:
            continue
        f = dst / f"musiqi_{i}_{s['id']}.mp3"
        if not f.is_file():
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "montaj"}), timeout=60) as r:
                f.write_bytes(r.read())
        done.append({"n": i, "file": str(f), "id": s["id"], "name": s.get("name"), "duration": s.get("duration"),
                     "author": s.get("username"), "license": "CC0 (Freesound)",
                     "url": f"https://freesound.org/people/{s.get('username', '')}/sounds/{s['id']}/"})
    (dst / "manifest.json").write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
    return done


def placement(vtype: int | None, total: float) -> list[dict[str, Any]]:
    """Standart yerləşmə (plan `music` siyahısı üçün şablon, `file` əlavə olunur)."""
    if int(vtype or 0) == 15:  # kurs dərsi: dərs boyu musiqi yoxdur — açılış və sonluq, çox yumşaq
        end = max(0.0, total - 5.0)
        return [{"start": 0.0, "dur": 7.0, "volume": 0.06, "fadeIn": 0.5, "fadeOut": 2.5, "duck": True},
                {"start": round(end, 2), "dur": 5.0, "volume": 0.06, "fadeIn": 1.5, "fadeOut": 2.0, "duck": True}]
    return [{"start": 0.0, "volume": 0.12, "fadeIn": 1.2, "fadeOut": 2.0, "duck": True}]
