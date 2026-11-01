"""Davamlılıq + müxtəliflik: müştərinin videoları "bir-birinin davamı kimi, oxşar, amma kopyası yox" (istifadəçi qaydası).

Sabit qalan: müştərinin rəng AİLƏSİ, şrift, ümumi ruh. Video-video dəyişən: ton (ailə daxilində), altyazı üslubu
(qutu / kontur), yazı animasiyası, kartların yeri. Tamamilə fərqli üslub təklif edilmir.
Təklif son videolara (profil `history`) baxır və onlardan fərqli birləşmə seçir; planda `"variation"` ilə tətbiq olunur.
"""

from __future__ import annotations

import colorsys
from typing import Any

CAPTIONS = ("box", "stroke")          # altyazı: rəngli qutu / qutusuz kontur
ANIMS = ("pop", "slide-up", "fade")   # yazıların girişi


def _hex(c: str) -> tuple[float, float, float]:
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def _to_hex(rgb: tuple[float, float, float]) -> str:
    return "#" + "".join(f"{max(0, min(255, round(x * 255))):02X}" for x in rgb)


def tones(theme: dict[str, Any], family: str = "") -> list[dict[str, str]]:
    """Eyni rəng ailəsində tonlar: əsas, açıq (gül), tünd, solğun (pudra); ailədə krem varsa — krem (açıq kart, tünd yazı)."""
    base = theme.get("primary") or "#555555"
    h, l, s = colorsys.rgb_to_hls(*_hex(base))
    out = []
    for name, dh, dl, ds in (("əsas", 0, 0, 0), ("açıq", -0.015, 0.07, 0.0), ("tünd", 0.0, -0.08, 0.02), ("solğun", 0.01, 0.05, -0.22)):
        nh, nl, ns = (h + dh) % 1, min(0.85, max(0.15, l + dl)), min(1, max(0.05, s + ds))
        p = _to_hex(colorsys.hls_to_rgb(nh, nl, ns))
        deep = _to_hex(colorsys.hls_to_rgb(nh, max(0.1, nl - 0.14), ns))
        out.append({"name": name, "primary": p, "primaryDeep": deep})
    fam = (family or "").lower()
    if any(w in fam for w in ("krem", "cream", "bej", "beige")):
        # krem: açıq kart, tünd yazı; vurğu (başlıq, nömrə, etiket) doymuş əsas rəngdə, onun üstündə ağ yazı
        out.append({"name": "krem", "primary": "#F2E4D6", "primaryDeep": base, "text": theme.get("primaryDeep") or base,
                    "accent": base, "onAccent": "#FFFFFF"})
    return out


def _dist(a: str, b: str) -> float:
    return sum((x - y) ** 2 for x, y in zip(_hex(a), _hex(b))) ** 0.5


def suggest(profile: dict[str, Any] | None, theme: dict[str, Any]) -> dict[str, Any]:
    """Son videolardan fərqli, amma ailə daxilində birləşmə: {"tone", "primary", "primaryDeep", "captions", "anim", "why"}."""
    hist = [h for h in ((profile or {}).get("history") or []) if isinstance(h, dict)][-3:]
    last = hist[-1] if hist else {}
    used_tones = [h.get("tone") or h.get("theme_primary") for h in hist if h.get("tone") or h.get("theme_primary")]
    ts = tones(theme, ((profile or {}).get("palette") or {}).get("family", "") if isinstance((profile or {}).get("palette"), dict) else "")
    if used_tones:  # ən son işlənən tonlardan ən uzaq olan
        pick = max(ts, key=lambda t: min(_dist(t["primary"], u) for u in used_tones))
    else:
        pick = ts[0]
    last_cap = last.get("captions") or ((last.get("style") or {}).get("captions"))
    cap = "stroke" if last_cap in ("box", "chip") else "box"
    used_anims = [h.get("anim") for h in hist if h.get("anim")]
    anim = next((a for a in ANIMS if a not in used_anims[-2:]), ANIMS[0])
    why = (f"son video: ton {used_tones[-1] if used_tones else '—'}, altyazı {last_cap or '—'}" if hist else "ilk video — əsas ton")
    res = {"tone": pick["name"], "primary": pick["primary"], "primaryDeep": pick["primaryDeep"], "captions": cap, "anim": anim, "why": why}
    if pick.get("text"):
        res["text"], res["onAccent"], res["accent"] = pick["text"], pick["onAccent"], pick["accent"]
        res["captions"] = "stroke" if cap == "stroke" else "box"
    return res


def apply(q: dict[str, Any], var: dict[str, Any], theme: dict[str, Any]) -> dict[str, Any]:
    """Planın "variation" açarını layihəyə tətbiq edir: brend temasının tonu, altyazı üslubu (qutu/kontur)."""
    if var.get("primary"):
        br = dict(q.get("brand") or {})
        br["theme"] = {**theme, "primary": var["primary"], "primaryDeep": var.get("primaryDeep") or theme.get("primaryDeep"),
                       **{k: var[k] for k in ("text", "onAccent", "accent") if var.get(k)}}
        q["brand"] = br
    if var.get("captions") and q.get("subtitles"):
        st = dict(q["subtitles"].get("style") or {})
        if var["captions"] == "stroke":
            st["bg"] = "none"
        else:
            st["bg"] = f"{var.get('primary') or theme.get('primary', '#333333')}@0.85"
        if var.get("text"):  # açıq (krem) tonda tünd yazı və doymuş aktiv söz — oxunaqlı qalsın
            st["color"] = var["text"] if var["captions"] != "stroke" else st.get("color", "#FFFFFF")
            if var["captions"] != "stroke":
                st["activeColor"] = var.get("primaryDeep") or theme.get("primary")
        q["subtitles"]["style"] = st
    return q
