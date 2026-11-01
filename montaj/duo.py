"""İki nəfərin söhbəti (VIDEO_TYPES növ 11): bir geniş kadrdan iki yanaşma.

* "switch" — kadraj danışana keçir: hər cümlədə ağzı tərpənən şəxs (speakers.turns); çox qısa növbələr (< min_len)
  birləşir ki, kadr ora-bura atılmasın. Kəsim sözlərin arasındakı boşluğa düşür.
* "split" — bölünmüş ekran (9:16): yuxarıda soldakı, aşağıda sağdakı şəxs; ikisi də daim görünür, reaksiya itmir.
  Altyazı ortadakı xəttin üstündə.
Yalnız BİR mənbə (hər ikisi eyni kadrda) dəstəklənir; iki ayrı kameranın sinxronu yoxdur — iddia etmə.
"""

from __future__ import annotations

from typing import Any


def chunks(words: list[dict[str, Any]], sentences: list[dict[str, Any]], max_len: float = 2.0) -> list[dict[str, Any]]:
    """Uzun cümlə sözlər arasındakı boşluqlarda ≤ max_len hissələrə bölünür (iki nəfərin danışığı ASR-də bir cümləyə
    birləşə bilər; növbə cümlə ortasında dəyişə bilər)."""
    out = []
    for s in sentences:
        ws = s["words"]
        cur = [ws[0]]
        for a, b in zip(ws, ws[1:]):
            if b["e"] - cur[0]["s"] > max_len and b["s"] - a["e"] >= 0.08:
                out.append({"s": cur[0]["s"], "e": cur[-1]["e"], "words": cur, "text": " ".join(w["w"] for w in cur)})
                cur = []
            cur.append(b)
        out.append({"s": cur[0]["s"], "e": cur[-1]["e"], "words": cur, "text": " ".join(w["w"] for w in cur)})
    return out


def runs(sentences: list[dict[str, Any]], who: list[int | None], min_len: float = 1.5) -> list[dict[str, Any]]:
    """Ardıcıl eyni danışanın cümlələri bir növbədir; qısa növbə əvvəlkinə qatılır. [{"s","e","speaker"}] (mənbə vaxtı)."""
    out: list[dict[str, Any]] = []
    for s, w in zip(sentences, who):
        if w is None and out:
            w = out[-1]["speaker"]
        if out and out[-1]["speaker"] == w:
            out[-1]["e"] = s["e"]
        else:
            out.append({"s": s["s"], "e": s["e"], "speaker": w})
    merged: list[dict[str, Any]] = []
    for r in out:
        if merged and (r["e"] - r["s"] < min_len or r["speaker"] is None):
            merged[-1]["e"] = r["e"]
        else:
            merged.append(dict(r))
    # sonradan qonşu eyni danışanlar
    final: list[dict[str, Any]] = []
    for r in merged:
        if final and final[-1]["speaker"] == r["speaker"]:
            final[-1]["e"] = r["e"]
        else:
            final.append(r)
    return final


def cut_points(rs: list[dict[str, Any]]) -> list[float]:
    """Növbələr arasındakı kəsim nöqtələri: əvvəlki növbənin sonu ilə növbətinin başlanğıcının ortası."""
    return [round((a["e"] + b["s"]) / 2, 3) for a, b in zip(rs, rs[1:])]


def split_spec(tracks: list[dict[str, Any]], sw: float, sh: float, W: int, H: int) -> dict[str, Any]:
    """Bölünmüş ekran üçün iki kəsim pəncərəsi (mənbə ölçüsünün hissəsi kimi): {"top": {x,y,w,h}, "bottom": {...}}.
    Hər yarının nisbəti W:(H/2); üz yarının ortasına yaxın (baş üstündə boşluq), çiyinlər görünür."""
    half = W / (H / 2)
    out = {}
    for key, tr in zip(("top", "bottom"), sorted(tracks, key=lambda t: t["cx"])[:2]):
        cw = min(sw, max(tr["w"] * sw * 3.6, sw * 0.25))
        ch = cw / half
        if ch > sh:
            ch, cw = sh, sh * half
        x = min(max(0.0, tr["cx"] * sw - cw / 2), sw - cw)
        y = min(max(0.0, tr["cy"] * sh - ch * 0.48), sh - ch)  # saç və baş üstü boşluq
        out[key] = {"x": round(x / sw, 4), "y": round(y / sh, 4), "w": round(cw / sw, 4), "h": round(ch / sh, 4)}
    return out
