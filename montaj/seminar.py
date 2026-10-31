"""Seminar və uzun çıxışlar: uzun videodan müstəqil qısa Reels hissələrinin tapılması, hissənin ayrıca layihəyə
çıxarılması (təkrar transkripsiya və orijinalın surəti olmadan) və danışan şəxsin tapılması.

Qaydalar (VIDEO_TYPES.md, növ 4 "Seminardan çıxarış"): hissə kontekstsiz də anlaşılmalıdır, səbəb əlaqəsi təhrif
olunmur, fikir yarımçıq kəsilmir. Hissə cümlə başlanğıcında başlayıb cümlə sonunda bitir. Seçim təklifdir —
yekun qərar transkripti oxuyan Claude-un və istifadəçinin təsdiqi ilədir.
"""

from __future__ import annotations

import re
from typing import Any

from montaj import quality, transcribe

# Hissənin əvvəlki kontekstə bağlı olduğunu göstərən başlanğıclar (müstəqil başlamır)
DEPENDENT_START = ("bu", "bunu", "buna", "bunun", "o", "onu", "ona", "onun", "onlar", "ona görə", "həmin", "yəni", "amma", "ancaq",
                   "lakin", "və", "həm də", "eyni zamanda", "sonra", "dediyim", "yuxarıda", "əvvəldə", "elə", "beləliklə")
HOOK_RX = re.compile(r"(\?|niyə|nə üçün|necə|səhv|sirr|ən vacib|ən böyük|əsas|heç vaxt|mütləq|diqqət|bilirsinizmi|təsəvvür edin|"
                     r"problem|həll|nəticə|\d+\s*(faiz|%|il|ay|addım|qayda|səbəb))", re.I)
# Təşkilati cümlələr (salamlaşma, sual-cavaba keçid, "sonra danışarıq") — hissənin başlanğıcı/içi üçün zəif
ORG_RX = re.compile(r"(xoş gəlmisiniz|salam|sualı var|suallara keçək|buyurun|söz verirəm|təşəkkür edirəm|sağ olun|"
                    r"sonra (ətraflı )?danış|növbəti mövzu|fasilə|mikrofon|eşidilir)", re.I)
CLOSE_RX = re.compile(r"(yəni|beləliklə|nəticədə|ona görə də|qısası|ən əsası|unutmayın|yadda saxlayın)", re.I)


def _starts_dependent(text: str) -> bool:
    t = text.strip().lower().strip("\"'«“")
    return any(t == d or t.startswith(d + " ") or t.startswith(d + ",") for d in DEPENDENT_START)


def highlights(words: list[dict[str, Any]], min_s: float = 20, max_s: float = 75, top: int = 8) -> list[dict[str, Any]]:
    """Müstəqil qısa hissə namizədləri (mənbə vaxtı ilə), bal və səbəblə. Hissələr bir-birini örtmür."""
    ss = quality.sentences(words, gap=0.7)
    cands = []
    for i, a in enumerate(ss):
        if _starts_dependent(a["text"]) or len(a["words"]) < 3 or ORG_RX.search(a["text"]):
            continue
        for j in range(i, len(ss)):
            dur = ss[j]["e"] - a["s"]
            if dur > max_s:
                break
            if dur < min_s:
                continue
            last = ss[j]["text"].strip()
            if not last.endswith((".", "!", "?", "…")):
                continue  # fikir sonlanmayıb
            seg = ss[i:j + 1]
            txt = " ".join(x["text"] for x in seg)
            score, why = 0.0, []
            if HOOK_RX.search(a["text"]):
                score += 3; why.append("güclü giriş (sual/iddia/rəqəm)")
            hooks = sum(1 for x in seg if HOOK_RX.search(x["text"]))
            score += min(3, hooks) * 0.7
            if CLOSE_RX.search(last) or last.endswith("!"):
                score += 1.5; why.append("yekunlaşdıran sonluq")
            dep = sum(1 for x in seg[1:] if _starts_dependent(x["text"]))
            score -= 0.15 * dep
            org = sum(1 for x in seg if ORG_RX.search(x["text"]))
            if org:
                score -= 1.2 * org; why.append(f"{org} təşkilati cümlə (salam/sual-cavab/keçid) — çıxarmaq olar")
            pron = len(re.findall(r"\b(o|bu|həmin)\s+(mövzu|məsələ|hissə|şey)", txt.lower()))
            if pron:
                score -= 1; why.append("əvvəlki mövzuya istinad var — yoxla")
            score += 1.0 - abs(dur - 45) / 45  # 30–60 s ideal
            ppl = [w.get("p", 1) for x in seg for w in x["words"]]
            if ppl and sum(ppl) / len(ppl) < 0.6:
                score -= 1; why.append("transkript zəif tanınıb")
            cands.append({"s": round(a["s"], 2), "e": round(ss[j]["e"], 2), "dur": round(dur, 1), "score": round(score, 2),
                          "why": why, "start_text": a["text"][:120], "end_text": last[-120:], "sentences": j - i + 1})
    cands.sort(key=lambda c: -c["score"])
    picked: list[dict[str, Any]] = []
    for c in cands:
        if all(c["e"] <= p["s"] or c["s"] >= p["e"] for p in picked):
            picked.append(c)
        if len(picked) >= top:
            break
    return sorted(picked, key=lambda c: c["s"])


# ---------------------------------------------------------------------------
# Danışan şəxs (bir neçə nəfər kadrda olanda)
# ---------------------------------------------------------------------------

def active_speaker(src, start: float, end: float, fps: float = 4.0) -> dict[str, Any]:
    """Bir neçə üz varsa, kimin danışdığını ağız nahiyəsindəki hərəkətdən tapır (əlavə model yoxdur).
    Nəticə: {"faces": [{cx, cy, w, h, motion}], "speaker": index | None}. Üzlər x-mövqeyinə görə izlənir."""
    import numpy as np

    from montaj import reframe

    step = 1.0 / fps
    frames = list(reframe.sample_frames(src, start, end, step, width=480))
    if len(frames) < 3:
        return {"faces": [], "speaker": None}
    dets = reframe.detect_faces(src, start, end, step=step)
    tracks: list[dict[str, Any]] = []
    for d in dets:
        for f in d["faces"]:
            cx = f["x"] + f["w"] / 2
            tr = next((t for t in tracks if abs(t["cx"] - cx) < max(0.08, f["w"] * 0.6)), None)
            if tr is None:
                tr = {"cx": cx, "cy": f["y"] + f["h"] / 2, "w": f["w"], "h": f["h"], "n": 0, "boxes": {}}
                tracks.append(tr)
            tr["n"] += 1
            tr["cx"] += (cx - tr["cx"]) / tr["n"]
            tr["boxes"][round(d["t"], 3)] = f
    tracks = [t for t in tracks if t["n"] >= max(2, len(dets) * 0.3)]
    if not tracks:
        return {"faces": [], "speaker": None}
    for tr in tracks:
        diffs, prev = [], None
        for t, rgb in frames:
            f = tr["boxes"].get(round(t, 3))
            if f is None:
                f = {"x": tr["cx"] - tr["w"] / 2, "y": tr["cy"] - tr["h"] / 2, "w": tr["w"], "h": tr["h"]}
            h, w = rgb.shape[:2]
            x0, x1 = int((f["x"] + f["w"] * 0.25) * w), int((f["x"] + f["w"] * 0.75) * w)
            y0, y1 = int((f["y"] + f["h"] * 0.62) * h), int((f["y"] + f["h"] * 0.95) * h)
            crop = rgb[max(0, y0):max(y0 + 1, y1), max(0, x0):max(x0 + 1, x1)].astype(float).mean(axis=2)
            if prev is not None and prev.shape == crop.shape and crop.size:
                diffs.append(float(np.abs(crop - prev).mean()))
            prev = crop
        tr["motion"] = round(float(np.mean(diffs)) if diffs else 0.0, 3)
    order = sorted(range(len(tracks)), key=lambda i: -tracks[i]["motion"])
    spk = order[0] if len(tracks) == 1 or tracks[order[0]]["motion"] > 1.3 * tracks[order[1]]["motion"] else None
    return {"faces": [{k: round(v, 4) if isinstance(v, float) else v for k, v in t.items() if k != "boxes"} for t in tracks],
            "speaker": spk}
