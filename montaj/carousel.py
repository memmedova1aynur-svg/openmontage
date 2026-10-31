"""Video karusel (Instagram): bir paylaşımda bir neçə qısa video slayd (4:5, hər biri ≤60 s).

* Mənbə — təsdiqlənmiş əsas montaj (zaman xətti); hər slayd ondan kəsilir, əsas montaj dəyişmir.
* Slayd = bir fikir (danışıqdakı "birincisi, ikincisi…" sıralaması və ya təbii pauzalar). Örtük slaydı — hook (ilk cümlə),
  sonuncu — çağırış (danışıqda varsa). Başlıqlar YALNIZ danışıqdan (qısaldılmış) — Claude yoxlayıb redaktə edir.
* Hər slaydda eyni dizayn: başlıq, sayğac "2/6", söz-söz altyazı; müştəri rəngi.
"""

from __future__ import annotations

import copy
import re
from typing import Any

from montaj import quality, transcribe

ORDINAL = re.compile(r"^(birinci|ikinci|üçüncü|dördüncü|beşinci|altıncı|yeddinci|səkkizinci|doqquzuncu|onuncu|"
                     r"\d+[-.)]?(ci|cı|cu|cü)?|sonuncu|son olaraq|növbəti|həmçinin)\w*", re.I)


def _az_lower(t: str) -> str:
    return t.replace("İ", "i").replace("I", "ı").lower()


def is_ordinal(text: str) -> bool:
    """Cümlə sıra sözü ilə başlayır ("Birincisi,", "İkincisi", "3-cü", "Sonuncu")."""
    return bool(ORDINAL.match(_az_lower(text.strip()).lstrip("\"'«“-—– ")))


MAX_SLIDE = 58.0


def split_ideas(words: list[dict[str, Any]], min_s: float = 4.0, max_s: float = MAX_SLIDE) -> list[dict[str, Any]]:
    """Cümlələri fikirlərə qruplaşdırır: sıra sözü ilə başlayan cümlə yeni fikirdir; yoxdursa uzun pauza (≥0.9 s)."""
    ss = quality.sentences(words, gap=0.6)
    if not ss:
        return []
    has_ord = sum(1 for s in ss if is_ordinal(s["text"])) >= 2
    groups: list[list[dict[str, Any]]] = [[ss[0]]]
    for prev, s in zip(ss, ss[1:]):
        cur = groups[-1]
        dur = s["e"] - cur[0]["s"]
        new = is_ordinal(s["text"]) if has_ord else (s["s"] - prev["e"] >= 0.9 and cur[-1]["e"] - cur[0]["s"] >= min_s)
        if new or dur > max_s:
            groups.append([s])
        else:
            cur.append(s)
    total = ss[-1]["e"] - ss[0]["s"]
    if len(groups) < 3 and total > 18 and len(ss) >= 3:
        # aydın bölgü yoxdur: cümlə sərhədlərində 3–7 bərabər hissə (hər biri tam cümlələrdən)
        target = min(7, max(3, round(total / 10)))
        size = total / target
        groups = [[ss[0]]]
        for s_ in ss[1:]:
            if s_["s"] - groups[-1][0]["s"] >= size * 0.85 and len(groups) < target:
                groups.append([s_])
            else:
                groups[-1].append(s_)
    out = []
    for g in groups:
        out.append({"s": g[0]["s"], "e": g[-1]["e"], "text": " ".join(x["text"] for x in g), "first": g[0]["text"]})
    return out


def short_title(text: str, n: int = 6) -> str:
    t = text.strip()
    if is_ordinal(t):
        t = t.split(None, 1)[1] if len(t.split()) > 1 else t
    t = t.strip(" ,:;—-")
    ws = t.split()
    out = " ".join(ws[:n]).rstrip(".,!?;:")
    return (out[:1].upper() + out[1:]) if out else text[:40]


def slice_project(q: dict[str, Any], a: float, b: float, node_tl) -> dict[str, Any]:
    """Zaman xəttinin [a, b] hissəsi ayrıca layihə kimi (video maqnitlidir; yazı/səs/üst qat kliplərinin vaxtı sürüşür)."""
    p = copy.deepcopy(q)
    for t in (b, a):  # əvvəl sonu, sonra başı böl (sıra dəyişməsin)
        acc = 0.0
        for c in node_tl("videoClips", p):
            d = c["srcOut"] - c["srcIn"]
            if acc + 0.1 < t < acc + d - 0.1:
                p = node_tl("split", p, c["id"], t)
                break
            acc += d
    acc, kill, a_eff, b_eff = 0.0, [], None, a
    for c in node_tl("videoClips", p):
        d = c["srcOut"] - c["srcIn"]
        if min(acc + d, b) - max(acc, a) < 0.15:  # sərhəddə qalan qısa qırıq (≤0.15 s) da çıxır
            kill.append(c["id"])
        else:
            a_eff = acc if a_eff is None else a_eff
            b_eff = acc + d
        acc += d
    a, b = (a_eff if a_eff is not None else a), b_eff
    for cid in kill:
        p = node_tl("deleteClip", p, cid)
    keep = []
    for c in p["clips"]:
        if c["track"] in ("v1",) or c.get("linkedTo"):
            keep.append(c)
            continue
        if c["track"] == "c1" and c.get("autoSub"):
            keep.append(c)  # altyazı yenidən qurulur
            continue
        s0 = float(c.get("start") or 0)
        e0 = s0 + c["srcOut"] - c["srcIn"]
        if e0 <= a or s0 >= b:
            continue
        cut_in = max(0.0, a - s0)
        c = dict(c, start=round(max(0.0, s0 - a), 3))
        if cut_in and c["track"] in ("m1", "s1", "a1", "v2"):
            c["srcIn"] = round(c["srcIn"] + cut_in, 3)
        if c["track"] in ("t1", "c1") and cut_in:
            c["srcOut"] = round(c["srcOut"] - cut_in, 3)
        over = (c["start"] + c["srcOut"] - c["srcIn"]) - (b - a)
        if over > 0:
            c["srcOut"] = round(c["srcOut"] - over, 3)
        if c["srcOut"] - c["srcIn"] >= 0.15:
            keep.append(c)
    p["clips"] = keep
    return p


def plan(words: list[dict[str, Any]], tl, total: float, cta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Slayd planı: örtük (hook) + fikir slaydları + çağırış. Vaxtlar zaman xəttindədir."""
    ideas = split_ideas(words)
    merged: list[dict[str, Any]] = []
    carry = None
    for g in ideas:  # 2 s-dən qısa fikir (məs. qısa hook) atılmır — növbəti fikirlə birləşir
        if carry:
            g = {"s": carry["s"], "e": g["e"], "text": carry["text"] + " " + g["text"], "first": carry["first"]}
            carry = None
        if g["e"] - g["s"] < 2.0:
            carry = g
            continue
        merged.append(g)
    if carry:
        if merged:
            merged[-1] = dict(merged[-1], e=carry["e"], text=merged[-1]["text"] + " " + carry["text"])
        else:
            merged.append(carry)
    ideas = merged
    slides = []
    for i, g in enumerate(ideas):
        a, b = tl(g["s"]), tl(g["e"])
        if a is None or b is None or b - a < 1.0:
            continue
        slides.append({"from": round(max(0.0, a - 0.15), 2), "to": round(min(total, b + 0.35), 2),
                       "title": short_title(g["first"]), "text": g["text"][:160]})
    if not slides:
        return {"slides": [], "_review": ["fikir slaydları tapılmadı"]}
    for x, y in zip(slides, slides[1:]):  # qonşu slaydlar üst-üstə düşmür (eyni söz iki slaydda təkrarlanmasın)
        if y["from"] < x["to"]:
            mid = round((x["to"] + y["from"]) / 2, 2)
            x["to"], y["from"] = mid, mid
    slides[0]["cover"] = True
    slides[0]["title"] = short_title(ideas[0]["first"], 8)
    review = [f"slayd {i + 1}: “{s['title']}” — danışıqda: “{s['text'][:70]}”" for i, s in enumerate(slides)]
    if cta and cta.get("tl") is not None:
        last = slides[-1]
        if last["from"] <= cta["tl"] <= last["to"]:
            last["cta"] = {"text": cta.get("value") or "", "keyword": cta.get("keyword") or ""}
    return {"aspect": "4:5", "slides": slides, "_review": review}
