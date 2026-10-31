"""Nağıl və cizgi videoları: danışıqdakı obraz və məkanlardan səhnə planı (VIDEO_TYPES növ 9 / M12).

* Səhnələr səsləndirmənin (danışığın) ardıcıllığı ilə gəlir; mətn danışıqdan.
* Obraz bir dəfə tanınandan sonra bütün videoda EYNİ görünür (tale.tsx-də sabit dizayn).
* Kitabxanada olmayan obraz (məs. əjdaha) uydurulmur — "_review"-da bildirilir, Claude istifadəçiyə alternativ təklif edir.
"""

from __future__ import annotations

import re
from typing import Any

from montaj import quality, transcribe

CHARS = {"tülkü": "fox", "dovşan": "rabbit", "ayı": "bear", "pişik": "cat", "uşaq": "child", "oğlan": "child", "qız": "child",
         "bala": "child", "balaca": "child"}
UNKNOWN = ("canavar", "qurd", "əjdaha", "div", "pəri", "şir", "fil", "it", "toyuq", "xoruz", "qarğa", "siçan", "kirpi", "dələ", "at",
           "inək", "keçi", "qoyun", "padşah", "şahzadə", "nənə", "baba", "ana", "ata", "cırtdan", "məlikməmməd")
PLACES = {"meşə": "forest", "ağac": "forest", "gecə": "night", "ulduz": "night", "yuxu": "night", "qaranlıq": "night", "ev": "house",
          "otaq": "house", "yuva": "house", "çəmən": "meadow", "çöl": "meadow", "bağ": "meadow", "gül": "meadow", "çiçək": "meadow"}
SPEECH = re.compile(r"(dedi|soruşdu|cavab verdi|qışqırdı|pıçıldadı|söylədi|dilləndi|[«“\"])", re.I)
JOY = re.compile(r"(sevindi|tullandı|atıldı|oynadı|güldü|şad)", re.I)
HELLO = re.compile(r"(salam|əl yellədi|qarşıladı|rastlaşdı|tanış oldu|görüşdü)", re.I)
SLOTS = [(330, 1370), (760, 1390), (540, 1410)]  # ayaqlar altyazının (y≈0.72) üstündə, yerdə (zəmin y≈1300)


def _stem_hits(toks: list[str], table: dict[str, str]) -> list[str]:
    out = []
    for t in toks:
        for k, v in table.items():
            if t.startswith(k) and (len(t) - len(k) <= 5):
                out.append(v)
    return out


def plan(words: list[dict[str, Any]], tl, total: float, mode: str = "cover_pip") -> dict[str, Any]:
    """Cümlələrdən nağıl səhnələri: obraz görünəndə səhnə, danışan obraz danışır, sevinəndə tullanır, salamlaşanda əl yelləyir."""
    ss = quality.sentences(words)
    seen: dict[str, int] = {}
    unknown: set[str] = set()
    bg = "forest"
    broll, review = [], []
    for s in ss:
        toks = [transcribe.norm_word(w["w"]) for w in s["words"]]
        kinds = list(dict.fromkeys(_stem_hits(toks, CHARS)))
        places = _stem_hits(toks, PLACES)
        for t in toks:
            for u in UNKNOWN:
                if t.startswith(u) and len(t) - len(u) <= 4:
                    unknown.add(u)
        if places:
            bg = places[0]
        if not kinds:
            continue
        at = tl(s["s"])
        if at is None:
            continue
        dur = round(max(2.2, min(6.0, s["e"] - s["s"] + 0.4)), 2)
        dur = min(dur, max(0.5, total - at))
        chars = []
        for i, k in enumerate(kinds[:3]):
            first = k not in seen
            seen.setdefault(k, len(seen))
            slot = seen[k] % len(SLOTS)  # obraz video boyu öz yerində qalır (ardıcıllıq)
            x, y = SLOTS[slot]
            a = {"kind": k, "x": x, "y": y, "scale": 1.3, "flip": slot == 1,
                 "enterFrom": ("right" if slot == 1 else "left") if first else "none"}
            if SPEECH.search(s["text"]) and i == 0:
                a.update(action="talk", actAt=0.3, actFor=dur)
            elif JOY.search(s["text"]):
                a.update(action="jump", actAt=0.5, actFor=dur)
            elif HELLO.search(s["text"]):
                a.update(action="wave", actAt=0.6, actFor=dur)
            chars.append(a)
        b = {"make": {"kind": "tale_scene", "props": {"bg": bg, "title": s["text"].strip(), "chars": chars}},
             "mode": mode, "at": at, "dur": dur}
        if mode == "cover_pip":  # nağıl səhnəsində danışanın dairəsi səmada (obrazlar aşağıdadır, başlıq yuxarıda)
            b.update(x=0.07, y=0.33)
        broll.append(b)
    if unknown:
        review.append("kitabxanada olmayan obraz(lar): " + ", ".join(sorted(unknown)) +
                      " — uydurma; istifadəçiyə de: mövcud obrazla (tülkü, dovşan, ayı, pişik, uşaq) əvəz etmək və ya səhnəsiz saxlamaq")
    if not broll:
        review.append("danışıqda tanınan obraz yoxdur — nağıl səhnəsi qurulmadı")
    return {"title": "Nağıl (cizgi səhnələri)", "approach": "M12", "captions": {"enabled": True, "style": {"type": "caption"}},
            "broll": broll, "_review": review, "_characters": sorted(seen, key=seen.get)}
