"""Reklam videoları: danışıqdan təklif faktlarının çıxarılması və 3 storyboard variantı.

Qaydalar (VIDEO_TYPES.md → "Reklam üçün ayrıca qayda", istifadəçinin təsdiqi):
* Cümlələrin ardıcıllığı qorunur; hook avtomatik əvvələ çıxarılmır (yalnız təklif kimi, təsdiqlə).
* Qiymət, tarix, fayda, nəticə və çağırış UYDURULMUR — hər qrafika mətni danışıqdan götürülür.
* Variantlar vizual yanaşma ilə fərqlənir: A təmiz + vurğu (M01+M02), B qrafik izah (M03), C dinamik (M04 + punch-in).
Avtomatik qısaldılmış mətnlər "_review" siyahısında göstərilir — Claude onları danışığa sadiq qalaraq redaktə edir.
"""

from __future__ import annotations

import re
from typing import Any

from montaj import quality, transcribe

MONTHS = ("yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avqust", "sentyabr", "oktyabr", "noyabr", "dekabr")
CURRENCY = ("manat", "azn", "₼", "man")
NUM_WORDS = {"bir": 1, "iki": 2, "üç": 3, "dörd": 4, "beş": 5, "altı": 6, "yeddi": 7, "səkkiz": 8, "doqquz": 9, "on": 10,
             "iyirmi": 20, "otuz": 30, "qırx": 40, "əlli": 50, "altmış": 60, "yetmiş": 70, "səksən": 80, "doxsan": 90}
OFFER_WORDS = {"təlim": "təlim", "kurs": "təlim", "dərs": "təlim", "master": "təlim", "vebinar": "təlim", "konsultasiya": "xidmət",
               "məsləhət": "xidmət", "xidmət": "xidmət", "seans": "xidmət", "məhsul": "məhsul", "sifariş": "məhsul", "çatdırılma": "məhsul"}
BENEFIT_RX = re.compile(r"(öyrənəcəks|öyrənəcəy|əldə edəcəks|bacaracaqs|qazanacaqs|nəticə|fayda|üstünlük|imkan)", re.I)
FILLERS = {"yəni", "belə", "ki", "isə", "də", "da", "artıq", "həm", "çox", "biz", "siz", "mən", "bu", "o", "və"}


def _norm(w: str) -> str:
    return transcribe.norm_word(w)


def _parse_number(tokens: list[str]) -> int | None:
    """Rəqəm və ya Azərbaycanca say sözləri (iki yüz əlli → 250)."""
    if not tokens:
        return None
    if re.fullmatch(r"\d[\d\s.,]*", " ".join(tokens)):
        return int(re.sub(r"\D", "", " ".join(tokens)) or 0)
    total, cur = 0, 0
    for t in tokens:
        if t in NUM_WORDS:
            cur += NUM_WORDS[t]
        elif t == "yüz":
            cur = (cur or 1) * 100
        elif t == "min":
            total += (cur or 1) * 1000
            cur = 0
        else:
            return None
    return total + cur or None


def scan(words: list[dict[str, Any]]) -> dict[str, Any]:
    """Danışıqdan reklam faktları (mənbə vaxtı ilə). Heç nə uydurulmur: tapılmayan sahə boş qalır."""
    ss = quality.sentences(words)
    facts: list[dict[str, Any]] = []
    kinds: dict[str, int] = {}
    for s in ss:
        toks = [_norm(w["w"]) for w in s["words"]]
        raw = [w["w"].strip(".,!?;:") for w in s["words"]]
        txt = s["text"]
        for t in toks:
            for k, v in OFFER_WORDS.items():
                if t.startswith(k):
                    kinds[v] = kinds.get(v, 0) + 1
        # qiymət: rəqəm (+ say sözləri) + valyuta
        for i, t in enumerate(toks):
            if any(t.startswith(c) for c in CURRENCY) or "₼" in raw[i]:
                j = i
                while j > 0 and (re.fullmatch(r"[\d.,]+", raw[j - 1]) or toks[j - 1] in NUM_WORDS or toks[j - 1] in ("yüz", "min")):
                    j -= 1
                val = _parse_number([raw[k] if re.fullmatch(r"[\d.,]+", raw[k]) else toks[k] for k in range(j, i)])
                if val:
                    facts.append({"kind": "price", "value": f"{val} AZN", "t": s["words"][j]["s"], "text": txt})
        if any(t.startswith("endirim") or t == "faiz" for t in toks) or "%" in txt:
            m = re.search(r"(\d+)\s*(%|faiz)", txt)
            facts.append({"kind": "discount", "value": f"{m.group(1)}% endirim" if m else "endirim", "t": s["s"], "text": txt})
        for i, t in enumerate(toks):
            if t.startswith(MONTHS) and i > 0 and re.fullmatch(r"\d{1,2}", raw[i - 1]):
                facts.append({"kind": "date", "value": f"{raw[i - 1]} {raw[i].lower()}", "t": s["words"][i - 1]["s"], "text": txt})
        m = re.search(r"(\d+)\s+(yer|nəfər)", txt, re.I)
        if m or re.search(r"yerlər?\s+məhdud", txt, re.I):
            facts.append({"kind": "seats", "value": f"Son {m.group(1)} {m.group(2)}" if m else "Yerlər məhduddur", "t": s["s"], "text": txt})
        # çağırış: "şərhlərdə X yazın", direkt/DM, link, zəng, WhatsApp, qeydiyyat
        low = txt.lower()
        m = re.search(r"şərh\w*\s+(.{1,40}?)\s+(?:sözünü\s+|kəlməsini\s+)?yaz", low)
        if m:
            kw = [w for w in re.split(r"\s+", m.group(1)) if w not in ("sözünü", "kəlməsini", "bir", "mənə")]
            facts.append({"kind": "cta", "value": "Şərhlərdə yazın", "keyword": (kw[-1] if kw else "").strip("\"'«»“”.,").upper(),
                          "t": s["s"], "text": txt})
        elif re.search(r"(direkt|dm|şəxsiyə|whatsapp|zəng ed|linkə|bio|qeydiyyatdan keç|müraciət ed)", low):
            facts.append({"kind": "cta", "value": txt, "keyword": "", "t": s["s"], "text": txt})
        if BENEFIT_RX.search(txt):
            facts.append({"kind": "benefit", "value": txt, "t": s["s"], "text": txt})
    offer = max(kinds, key=kinds.get) if kinds else None
    return {"offer": offer, "facts": facts, "sentences": [{"s": x["s"], "e": x["e"], "text": x["text"]} for x in ss]}


def short(text: str, n: int = 6) -> str:
    """Qrafika üçün qısa mətn — YALNIZ cümlənin öz sözləri (sıra qorunur, doldurucular atılır)."""
    ws = [w.strip(",;:") for w in text.split()]
    kept = [w for w in ws if _norm(w) not in FILLERS] or ws
    out = " ".join(kept[:n]).rstrip(".,!?")
    return out[:1].upper() + out[1:]


def timeline_map(cards: list[dict[str, Any]]) -> list[tuple[str, float, float, float]]:
    """Storyboard kartları (daxil olanlar, sıra ilə) → [(media, srcIn, srcOut, timeline_start)]."""
    out, t = [], 0.0
    for c in cards:
        if not c.get("include", True):
            continue
        out.append((c["mediaId"], float(c["srcIn"]), float(c["srcOut"]), t))
        t += float(c["srcOut"]) - float(c["srcIn"])
    return out


def to_timeline(tm: list[tuple[str, float, float, float]], src_t: float, media: str | None = None) -> float | None:
    for mid, a, b, t0 in tm:
        if (media is None or mid == media) and a - 0.05 <= src_t <= b:
            return round(t0 + max(0.0, src_t - a), 2)
    return None


def plans(scan_res: dict[str, Any], tm: list[tuple[str, float, float, float]], total: float) -> dict[str, dict[str, Any]]:
    """3 variant: A təmiz + vurğu, B qrafik izah, C dinamik. Ardıcıllıq dəyişmir; mətnlər danışıqdan."""
    F = [dict(f, tl=to_timeline(tm, f["t"])) for f in scan_res["facts"]]
    F = [f for f in F if f["tl"] is not None]  # montajdan çıxarılan hissədəki faktlar işlədilmir
    price = next((f for f in F if f["kind"] == "price"), None)
    disc = next((f for f in F if f["kind"] == "discount"), None)
    badges = [f for f in F if f["kind"] in ("date", "seats")][:2]
    cta = next((f for f in reversed(F) if f["kind"] == "cta"), None)
    bens = [f for f in F if f["kind"] == "benefit"][:4]
    review: list[str] = []
    common: list[dict[str, Any]] = []
    if price:
        prices = [f for f in F if f["kind"] == "price"]
        old = prices[0]["value"] if len(prices) > 1 else None
        new = prices[-1] if len(prices) > 1 else price
        g = {"type": "offer", "heading": "QİYMƏT", "price": new["value"], "start": new["tl"], "dur": 3.5, "anim": {"in": "pop", "out": "fade"}}
        if old and old != new["value"]:
            g["oldPrice"] = old
        if disc:
            g["note"] = disc["value"]
        common.append(g)
        review.append(f"qiymət kartı: “{g['price']}” — danışıqda: “{new['text'][:80]}”")
    for b in badges:
        common.append({"type": "badge", "text": b["value"], "start": b["tl"], "dur": 3.0, "anim": {"in": "slide-up", "out": "fade"}})
        review.append(f"nişan: “{b['value']}” — danışıqda: “{b['text'][:80]}”")
    if cta:
        dur = max(2.5, min(5.0, total - cta["tl"]))
        g = {"type": "cta", "text": cta["value"] if cta.get("keyword") else short(cta["value"], 7), "start": cta["tl"], "dur": round(dur, 2),
             "anim": {"in": "pop", "out": "fade"}}
        if cta.get("keyword"):
            g["keyword"] = cta["keyword"]
        common.append(g)
        review.append(f"çağırış: “{g.get('keyword') or g['text']}” — danışıqda: “{cta['text'][:80]}”")
    caps = {"enabled": True, "style": {"type": "caption"}}
    A = {"title": "Təmiz + vurğu", "approach": "M01+M02", "captions": caps, "graphics": [
        {"type": "emphasis", "text": short(b["value"], 5), "start": b["tl"], "dur": 2.2, "anim": {"in": "pop", "out": "fade"}} for b in bens[:3]
    ] + common}
    items = [{"text": short(b["value"], 6), "at": round(b["tl"] - bens[0]["tl"], 2)} for b in bens] if bens else []
    B = {"title": "Qrafik izah", "approach": "M03", "captions": caps, "graphics": common + ([
        {"type": "list", "heading": "Nə qazanırsınız", "items": items, "start": bens[0]["tl"],
         "dur": round(min(8.0, bens[-1]["tl"] - bens[0]["tl"] + 3.0), 2), "anim": {"in": "slide-up", "out": "fade"}}] if items else [])}
    C = {"title": "Dinamik", "approach": "M04 + punch-in", "captions": caps, "graphics": list(common), "zooms": [], "broll": []}
    if bens:
        C["broll"].append({"make": {"kind": "checklist", "props": {"title": "Nə qazanırsınız", "items": [i["text"] for i in items][:4],
                                                                  "times": [round(0.3 + 0.5 * k, 2) for k in range(len(items[:4]))]}},
                           "mode": "cover", "at": bens[0]["tl"], "dur": 3.0})
    hook = scan_res["sentences"][0] if scan_res["sentences"] else None
    for tt in [x for x in ((to_timeline(tm, hook["s"]) if hook else None), price["tl"] if price else None) if x is not None]:
        if total - tt > 2.0:
            C["zooms"].append({"from": round(tt + 0.25, 2), "to": round(min(total - 0.3, tt + 2.0), 2), "scale": 1.1, "cy": 0.42})
    for p in (A, B, C):
        p["_review"] = review + [f"vurğu/siyahı mətni danışıqdan avtomatik qısaldılıb — yoxla: {', '.join(short(b['value'], 6) for b in bens)}"] if bens else list(review)
    return {"A": A, "B": B, "C": C}
