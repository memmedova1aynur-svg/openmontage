"""M10 — sürətli, əyləncəli sual-cavab (VIDEO_TYPES növ 10).

* Suallar danışıqdan: sual işarəsi, sual sözləri və ədatları; kadrarxası səs — həmin cümlədə kadrdakı üzün ağzı
  tərpənmir (speakers.mouth_tracks). Sual mətni ekranda yalnız danışıqdan (ASR səhvini Claude düzəldir).
* Ölü pauza çıxır, reaksiya (gülüş, tərəddüd, səsli pauza) qalır — onlar məna daşıyır.
* Variantlar: A yüngül yumor (sual səsi + yazı, reaksiyada yaxınlaşma, yüngül "pop"), B sual yalnız yazı ilə
  (cavab tək başına anlaşılmalıdır — `_review`), C sakit (M01).
* Ekspert alçaldılmır, demədiyi fikir yaradılmır: cavablar yenidən sıralanmır, cümlə ortasından kəsilmir.
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np

from montaj import quality, transcribe

Q_WORDS = ("nə", "niyə", "necə", "kim", "kimə",  # "kimi" yoxdur: əsasən "...kimi" (bənzətmə) "hansı", "harada", "hara", "haradan", "nə vaxt", "neçə", "nəyi",
           "nədir", "kimdir", "hansıdır", "nəyə", "nədən", "niyəsə", "bəs")
# sual ədatı: ayrıca söz ("mi"), şəxs sonluqlu forma ("mısan", "midir") və ya fel sonluğundan sonra ("gəlmisənmi",
# "işləyirmi"); "kimi", "elmi", "rəsmi" kimi sözlər sual sayılmır
Q_PARTICLE = re.compile(r"(^(mı|mi|mu|mü)$|(mıdır|midir|mudur|müdür|mısan|misən|musan|müsən|mısınız|misiniz|musunuz|müsünüz)$|"
                        r"(sən|san|sınız|siniz|dır|dir|dur|dür|ıq|ik|uq|ük|əm|am|ıb|ib|ub|üb|ar|ər|ır|ir|ur|ür|dı|di|du|dü)"
                        r"(mı|mi|mu|mü)$)", re.I)
LAUGH = re.compile(r"^(ha|he|hi|xa|xe)+[!.?,]*$|gülür|gülüş|\(.*gül.*\)", re.I)


def is_question(text: str) -> bool:
    t = text.strip()
    if t.endswith("?"):
        return True
    if t.endswith("!"):
        return False  # "Nə gözəl!" — nida
    low = transcribe.norm_word(t.split()[0]) if t.split() else ""
    ws = [transcribe.norm_word(w) for w in t.split()]
    edge = ws[:3] + ws[-2:]  # sual sözü adətən əvvəldə və ya sonda olur ("Ən sevdiyin yemək nədir")
    return low in Q_WORDS or any(w in Q_WORDS for w in edge) or bool(Q_PARTICLE.search(t.split()[-1].strip("?.!,").lower() if t.split() else ""))


def reactions(words: list[dict[str, Any]], rms: np.ndarray | None, hop: float = quality.HOP,
              min_gap: float = 0.3) -> list[tuple[float, float]]:
    """Səsli, amma sözsüz anlar (gülüş, "hmm", nəfəs-reaksiya) və gülüş sözləri: [(s, e)]."""
    out = [(w["s"], w["e"]) for w in words if LAUGH.search(w["w"].strip())]
    if rms is None or not len(rms):
        return out
    speech = [rms[int(w["s"] / hop):max(int(w["s"] / hop) + 1, int(w["e"] / hop))].mean() for w in words if w["e"] / hop < len(rms)]
    ref = float(np.median(speech)) if speech else float(np.median(rms))
    for a, b in zip(words, words[1:]):
        g0, g1 = a["e"], b["s"]
        if g1 - g0 < min_gap:
            continue
        seg = rms[int(g0 / hop):int(g1 / hop)]
        if len(seg) and float(np.percentile(seg, 80)) > ref * 0.35:  # pauzada güclü səs: reaksiya
            out.append((round(g0, 2), round(g1, 2)))
    return sorted(out)


def classify(sentences: list[dict[str, Any]], motion: list[float | None] | None = None) -> list[str]:
    """Hər cümlə: "q" (sual tərəfi) və ya "a" (cavab). Sual əlaməti olan cümlə sualdır; ağız hərəkəti verilibsə,
    kadrdakı şəxsin ağzı tərpənməyən cümlə də (kadrarxası səs: sual, "əla", "bəs sonra") sual tərəfinə düşür."""
    ms = [m for m in motion or [] if m is not None]
    med = float(np.median(ms)) if ms else None
    out = []
    for i, s in enumerate(sentences):
        off = med is not None and motion is not None and motion[i] is not None and motion[i] < 0.35 * med
        if med is not None and motion is not None and motion[i] is not None:
            s["onCam"] = not off  # sualı kadrdakı şəxs özü verir (ritorik ola bilər)
        out.append("q" if is_question(s["text"]) or off else "a")
    return out


def pairs(sentences: list[dict[str, Any]], kinds: list[str]) -> list[dict[str, Any]]:
    """Ardıcıl sual cümlələri bir sual, ardınca gələn cavab cümlələri onun cavabıdır."""
    out: list[dict[str, Any]] = []
    cur: dict[str, Any] | None = None
    for s, k in zip(sentences, kinds):
        if k == "q":
            if cur is None or cur["a"]:
                cur = {"q": [], "a": []}
                out.append(cur)
            cur["q"].append(s)
        else:
            if cur is None:
                cur = {"q": [], "a": []}
                out.append(cur)
            cur["a"].append(s)
    return [p for p in out if p["a"]]


def _segments(sents: list[dict[str, Any]], all_words: list[dict[str, Any]], keep: list[tuple[float, float]],
              max_gap: float) -> list[tuple[float, float]]:
    """Cümlələri saxlanılan aralıqlara çevirir: `max_gap`-dan uzun ölü pauza çıxır, reaksiya pauzası qalır."""
    ws = [w for s in sents for w in s["words"]]
    if not ws:
        return []
    starts = sorted(w["s"] for w in all_words)
    ends = sorted(w["e"] for w in all_words)

    def pad_in(t):
        prev_e = max([e for e in ends if e <= t - 0.01], default=0.0)
        return max(prev_e + 0.02, t - 0.1, 0.0)

    def pad_out(t):
        nxt = min([s for s in starts if s >= t + 0.01], default=t + 1)
        return min(nxt - 0.02, t + 0.15)
    segs = [[pad_in(ws[0]["s"]), pad_out(ws[0]["e"])]]
    for w in ws[1:]:
        gap = w["s"] - segs[-1][1]
        react = any(a < w["s"] and b > segs[-1][1] - 0.15 for a, b in keep)
        if gap > max_gap and not react:
            segs.append([pad_in(w["s"]), pad_out(w["e"])])
        else:
            segs[-1][1] = pad_out(w["e"])
    return [(round(a, 3), round(b, 3)) for a, b in segs if b - a > 0.15]


def plans(words: list[dict[str, Any]], media_id: str, rms: np.ndarray | None = None,
          motion: list[float | None] | None = None, same_aspect: bool = True) -> dict[str, Any]:
    """3 variant planı (storyboard.cards ilə). Vaxtlar mənbə vaxtıdır; qrafika vaxtları zaman xəttinə çevrilir."""
    ss = quality.sentences(words, gap=0.5)
    kinds = classify(ss, motion)
    ps = pairs(ss, kinds)
    react = reactions(words, rms)
    review: list[str] = []
    if not any(p["q"] for p in ps):
        review.append("sual tapılmadı — bu növ (10) üçün sual-cavab materialı olduğunu yoxla")
    for p in ps:
        if p["q"]:
            rhet = " (kadrdakı şəxs özü soruşur — ritorik ola bilər; sual-cavab deyilsə bu planları seçmə)" \
                if all(s.get("onCam") for s in p["q"]) and any("onCam" in s for s in p["q"]) else ""
            review.append(f"sual: “{' '.join(s['text'] for s in p['q'])[:90]}” → cavab: “{p['a'][0]['text'][:60]}”{rhet}")
    caps = {"enabled": True, "style": {"type": "caption"}}
    out: dict[str, Any] = {}
    for key, title, approach in (("A", "Yüngül yumor: sual + reaksiya", "M10"), ("B", "Sual ekranda yazı ilə", "M10+M02"),
                                 ("C", "Sakit sual-cavab", "M01")):
        cards, gfx, sfx, zooms = [], [], [], []
        t = 0.0
        for n, p in enumerate(ps):
            qtext = " ".join(s["text"] for s in p["q"]).strip()
            q_segs = _segments(p["q"], words, react, 0.3 if key == "A" else 0.6) if p["q"] and key != "B" else []
            a_segs = _segments(p["a"], words, react, {"A": 0.3, "B": 0.35, "C": 0.8}[key])
            t_q = t
            for a, b in q_segs + a_segs:
                cards.append({"id": f"{key.lower()}{len(cards) + 1}", "mediaId": media_id, "srcIn": a, "srcOut": b, "include": True,
                              "words": [w for w in words if a <= w["s"] and w["e"] <= b]})
                t += b - a
            if qtext and key in ("A", "B"):
                show = round(t_q + (0 if key == "A" else 0.0), 2)
                dur = (sum(b - a for a, b in q_segs) + 1.6) if key == "A" else 2.2
                gfx.append({"type": "title", "text": qtext[:70], "start": show, "dur": round(dur, 2), "size": 0.034,
                            "anim": {"in": "pop", "out": "fade"}})
                if key == "A":
                    sfx.append({"kind": "pop", "t": show, "vol": 0.22})
                elif n:
                    sfx.append({"kind": "whoosh", "t": max(0.0, show - 0.15), "vol": 0.18})
            if key == "A" and same_aspect:  # reaksiya anında yüngül yaxınlaşma (zaman xəttində)
                acc = t_q
                for a, b in q_segs + a_segs:
                    for r0, r1 in react:
                        if a <= r0 and r1 <= b and r1 - r0 >= 0.3:
                            z0 = round(acc + (r0 - a), 2)
                            zooms.append({"from": z0, "to": round(min(acc + (b - a), z0 + max(0.8, r1 - r0 + 0.4)), 2), "scale": 1.1})
                    acc += b - a
        plan = {"title": title, "approach": approach, "storyboard": {"cards": cards}, "captions": caps,
                "graphics": gfx, "sfx": sfx, "zooms": zooms[:4], "dropStoryboardText": True}
        if key == "B":
            plan["_review"] = ["sual səsi çıxarılıb — hər cavabın tək başına anlaşıldığını yoxla (anlaşılmırsa A və ya C)"]
        out[key] = plan
    return {"plans": out, "pairs": len(ps), "reactions": react, "review": review}
