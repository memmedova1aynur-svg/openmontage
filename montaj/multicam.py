"""Virtual multikamera: bir rakursdan çəkilmiş videoda fərqli PLAN ÖLÇÜLƏRİ (ümumi / orta / yaxın) və yavaş yaxınlaşma.

* Rakurs (kameranın hündürlüyü, istiqaməti) dəyişmir — yeni bucaq uydurulmur. Yalnız rəqəmsal kəsim.
* Keyfiyyət ehtiyatı ölçülür: kəsim pəncərəsinin piksel eni / çıxış eni. 4K → 1080 ≈ 2x ehtiyat (təmiz yaxın plan),
  1080 → 1080 ≈ 1x (yalnız 1.12x-ə qədər — fərq zəif, dürüst xəbərdarlıq).
* Kəsimlər cümlə sərhədlərində; eyni ölçülü iki plan ardıcıl gəlmir; vurğulu fikirdə (sual, nida, rəqəm, "ən vacib"...)
  yaxın plan və ya yavaş yaxınlaşma. Plan ölçüsünün dəyişməsi jump cut-ı da gizlədir.
"""

from __future__ import annotations

import re
from typing import Any

SOFT = 1.12      # 1x ehtiyatda belə hiss olunmayan yumşalma həddi
MAX_Z = 2.0
EMPH = re.compile(r"(!|\?|\d|ən vacib|ən böyük|əsas|heç vaxt|mütləq|diqqət|unutmayın|yadda saxlayın|sirr|səhv|problem|nəticə)", re.I)
STYLES = {"calm": {"min_len": 5.0, "push": True}, "dynamic": {"min_len": 2.5, "push": False}}


def headroom(m: dict[str, Any], frame: dict[str, Any] | None, out_w: int) -> float:
    """Kəsim pəncərəsinin piksel eni / çıxış eni (1.0 — böyütmə yoxdur, 2.0 — 4K→1080)."""
    fr = frame or {}
    if fr.get("mode") in ("auto", "manual") and fr.get("keys"):
        crop = float(m.get("width") or 0) * float(fr.get("baseW") or 1) * float(fr.get("s") or 1)
    else:
        crop = float(m.get("width") or 0)
    return crop / max(1, out_w)


def tiers(head: float) -> dict[str, float]:
    """Plan ölçüləri (yaxınlaşma əmsalı). Ehtiyat azdırsa yalnız ümumi + yüngül yaxın."""
    zmax = max(1.0, min(MAX_Z, head * SOFT))
    if zmax < 1.05:
        return {"wide": 1.0}
    if zmax < 1.3:
        return {"wide": 1.0, "close": round(zmax, 3)}
    return {"wide": 1.0, "medium": round(1 + (zmax - 1) * 0.45, 3), "close": round(zmax, 3)}


def segments(sents: list[dict[str, Any]], total: float, min_len: float) -> list[dict[str, Any]]:
    """Zaman xəttindəki cümlələrdən kadr hissələri (≥ min_len); sərhəd iki cümlənin arasındakı boşluğun ortası."""
    segs: list[dict[str, Any]] = []
    for s in sents:
        if segs and s["s"] - segs[-1]["a"] < min_len:
            segs[-1]["e_last"] = s["e"]
            segs[-1]["emph"] = segs[-1]["emph"] or bool(EMPH.search(s["text"]))
            continue
        cut = round((segs[-1]["e_last"] + s["s"]) / 2, 3) if segs else 0.0
        if segs:
            segs[-1]["b"] = cut
        segs.append({"a": cut, "e_last": s["e"], "emph": bool(EMPH.search(s["text"])), "text": s["text"]})
    if not segs:
        return [{"a": 0.0, "b": total, "emph": False, "text": ""}]
    segs[0]["a"] = 0.0
    segs[-1]["b"] = total
    if len(segs) > 1 and segs[-1]["b"] - segs[-1]["a"] < min_len * 0.5:  # çox qısa son hissə əvvəlkinə qatılır
        segs[-2]["b"] = segs[-1]["b"]
        segs[-2]["emph"] = segs[-2]["emph"] or segs[-1]["emph"]
        segs.pop()
    for g in segs:
        g.pop("e_last", None)
    return segs


def assign(segs: list[dict[str, Any]], ts: dict[str, float]) -> list[str]:
    """Hər hissəyə plan: giriş ümumi, vurğu yaxın, qalanı növbə ilə; eyni ölçü ardıcıl gəlmir."""
    names = list(ts)
    if len(names) == 1:
        return ["wide"] * len(segs)
    rest = [n for n in names if n != "close"] or names
    out: list[str] = []
    k = 0
    for i, g in enumerate(segs):
        prev = out[-1] if out else None
        if i == 0:
            pick = "wide"
        elif g["emph"] and "close" in ts and prev != "close":
            pick = "close"
        else:
            cand = [n for n in rest if n != prev] or [n for n in names if n != prev]
            pick = cand[k % len(cand)]
            k += 1
        out.append(pick)
    return out
