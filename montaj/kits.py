"""Üslub dəstləri (style kits): bir məzmundan TAMAMILƏ fərqli vizual sistemlər.

Hər dəst ayrı dizayn dilidir: yazı forması, yer, altyazı, hərəkət, kart olub-olmaması, musiqi/SFX paletası. Dəst məzmunu
(hook mətni, nümunələr, vurğular, əsas fikir — HAMISI danışıqdan) öz qrafika növlərinə çevirir və plan parçası qaytarır.
`variants` üçün hər variantı fərqli dəstdən qur; `difference.py` fərqi yoxlayır, `memory.py` təkrarın qarşısını alır.

  python -m montaj.kits list
  python -m montaj.kits build editorial content.json [--theme theme.json]   # plan parçası JSON
content.json:
  {"hook": {"text": "...", "short": "...", "kicker": "...", "start": 0.15, "dur": 4.5},
   "list": {"heading": "...", "items": ["..."], "times": [0.2, 1.0], "start": 18.3, "dur": 4.2},
   "emphasis": [{"text": "...", "start": 28.4, "dur": 2.8}],
   "claim": {"text": "...", "kicker": "...", "start": 47.5, "dur": 4.0},
   "words": [{"w": "CƏZA", "s": 0.0}], "duration": 56.4}
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

KITS: dict[str, dict[str, Any]] = {
    "classic": {
        "name": "Klassik kartlar",
        "about": "Brend rəngli yuvarlaq kartlar, qutulu altyazı. Etibarlı, tanış; digərlərindən fərqləndirmək üçün yox, təhlükəsiz baza.",
        "suits": ["maarifləndirmə", "reklam", "təlim"],
        "axes": {"layout": "top-card", "form": "sans-card", "caption": "box", "motion": "pop", "card": "card", "density": "mid"},
        "music": "uplifting acoustic", "sfx": ["pop"],
    },
    "editorial": {
        "name": "Redaksiya tipoqrafiyası",
        "about": "Kartsız: böyük serif yazı birbaşa kadrda, sola düzlənmiş; sakit, ekspert mövqeyini önə çəkir.",
        "suits": ["maarifləndirmə", "psixologiya", "ekspert fikri", "hekayə"],
        "axes": {"layout": "overlay-left", "form": "serif-free", "caption": "plain-left", "motion": "fade", "card": "none", "density": "low"},
        "music": "calm cinematic acoustic", "sfx": ["soft"],
    },
    "colorblock": {
        "name": "Rəng bloku",
        "about": "Yuxarıda tam enli rəngli panel (hər anda rəngi dəyişir), altda ekspert; bədən örtülmür, bloklar ritm verir.",
        "suits": ["reklam", "təlim", "siyahı və addımlar", "məlumat"],
        "axes": {"layout": "top-block", "form": "sans-block", "caption": "strip", "motion": "slide", "card": "block", "density": "mid"},
        "music": "upbeat corporate", "sfx": ["pop", "whoosh"],
    },
    "handnote": {
        "name": "Əl yazısı qeydlər",
        "about": "Əl yazısı sözlər, altından xətt, dairə, ox, ✓ — insani, 'jurnal' hissi; qutu yoxdur.",
        "suits": ["ana-körpə", "uşaq", "şəxsi hekayə", "məsləhət"],
        "axes": {"layout": "margin-notes", "form": "handwritten", "caption": "mono-bar", "motion": "draw", "card": "none", "density": "mid"},
        "music": "warm ukulele playful", "sfx": ["soft", "pop"],
    },
    "kinetic": {
        "name": "Kinetik söz-söz",
        "about": "Sinema zolaqları: yazı qara zolaqda bir böyük söz kimi gəlir, yuxarıda irəliləyiş xətti. Ən dinamik.",
        "suits": ["reklam", "motivasiya", "qısa və sürətli", "hook-güclü"],
        "axes": {"layout": "letterbox", "form": "kinetic-word", "caption": "small-in-bar", "motion": "word-by-word", "card": "none", "density": "high"},
        "music": "energetic upbeat modern", "sfx": ["whoosh", "pop"],
    },
}

SMOOTH = {"scale": 1.1}


def list_kits() -> list[dict[str, Any]]:
    return [{"id": k, **{x: v[x] for x in ("name", "about", "suits", "axes")}} for k, v in KITS.items()]


def _el(c: dict[str, Any], key: str) -> dict[str, Any] | None:
    return c.get(key) if isinstance(c.get(key), dict) else None


def _theme(theme: dict[str, Any] | None) -> dict[str, str]:
    t = theme or {}
    return {"primary": t.get("primary") or "#C9577D", "deep": t.get("primaryDeep") or "#9E3D5E", "soft": t.get("accentSoft") or "#F2E4D6",
            "accent": t.get("accent") or "#C9577D"}


def build(kit: str, content: dict[str, Any], theme: dict[str, Any] | None = None) -> dict[str, Any]:
    """Plan parçası: {kit, axes, graphics, captions, sfx, zooms, music_query, hook_method}. Mətnlər YALNIZ content-dən."""
    if kit not in KITS:
        raise ValueError(f"naməlum dəst: {kit} ({', '.join(KITS)})")
    th = _theme(theme)
    hook, lst, claim = _el(content, "hook"), _el(content, "list"), _el(content, "claim")
    emph = [e for e in content.get("emphasis") or [] if isinstance(e, dict)]
    g: list[dict[str, Any]] = []
    cap: dict[str, Any] = {"enabled": True}
    hs = float(hook.get("start", 0.15)) if hook else 0.15
    hd = float(hook.get("dur", 4.5)) if hook else 4.5
    items = lambda L: [{"text": t, "at": float((L.get("times") or [])[i]) if i < len(L.get("times") or []) else 0.3 * i} for i, t in enumerate(L["items"])]  # noqa: E731

    if kit == "classic":
        if hook:
            g.append({"type": "title", "text": hook["text"], "start": hs, "dur": hd, "y": 0.19, "anim": {"in": "fade", "out": "fade"}})
        if lst:
            g.append({"type": "list", "heading": lst.get("heading"), "items": items(lst), "start": lst["start"], "dur": lst["dur"], "y": 0.175})
        g += [{"type": "emphasis", "text": e["text"], "start": e["start"], "dur": e["dur"], "y": 0.60} for e in emph]
        if claim:
            g.append({"type": "emphasis", "text": claim["text"], "start": claim["start"], "dur": claim["dur"], "y": 0.60})
        hook_method = "typography-card"
    elif kit == "editorial":
        cap.update(style={"bg": "none", "align": "left", "x": 0.06, "weight": 600, "size": 0.04, "color": "#FFFFFF"})
        if hook:
            g.append({"type": "type", "font": "serif", "kicker": hook.get("kicker"), "text": hook.get("short") or hook["text"], "size": 0.075, "x": 0.5, "y": 0.2,
                      "start": hs, "dur": hd, "anim": {"in": "fade", "d": 0.6, "out": "fade"}})
        if lst:
            g.append({"type": "type", "font": "serif", "kicker": lst.get("heading"), "items": items(lst), "size": 0.045, "y": 0.18, "start": lst["start"], "dur": lst["dur"],
                      "anim": {"in": "fade", "d": 0.5}})
        g += [{"type": "type", "font": "serif", "text": e["text"], "size": 0.05, "y": 0.2, "start": e["start"], "dur": e["dur"], "anim": {"in": "fade", "d": 0.5}} for e in emph]
        if claim:
            g.append({"type": "type", "font": "serif", "kicker": claim.get("kicker"), "text": claim["text"], "size": 0.07, "y": 0.2, "start": claim["start"], "dur": claim["dur"],
                      "anim": {"in": "fade", "d": 0.6}})
        hook_method = "typography-free"
    elif kit == "colorblock":
        cap.update(style={"bg": f"{th['deep']}@0.96", "color": "#FFFFFF", "weight": 700, "size": 0.04, "y": 0.955, "radius": 0})
        if hook:
            g.append({"type": "block", "chip": "SUAL" if str(hook["text"]).strip().endswith("?") else hook.get("kicker"), "text": hook["text"], "bg": th["primary"], "h": 0.3,
                      "y": 0.15, "bleed": True, "start": hs, "dur": hd, "anim": {"in": "slide-up", "out": "fade"}})
        if lst:
            g.append({"type": "block", "items": items(lst), "bg": th["soft"], "color": th["deep"], "chipBg": th["primary"], "h": 0.3, "y": 0.15, "bleed": True,
                      "start": lst["start"], "dur": lst["dur"], "anim": {"in": "slide-up", "out": "fade"}})
        g += [{"type": "block", "text": e["text"], "bg": th["deep"], "h": 0.22, "y": 0.11, "bleed": True, "start": e["start"], "dur": e["dur"],
               "anim": {"in": "slide-up", "out": "fade"}} for e in emph]
        if claim:
            g.append({"type": "block", "chip": claim.get("kicker"), "text": claim["text"], "bg": th["deep"], "h": 0.3, "y": 0.15, "bleed": True,
                      "start": claim["start"], "dur": claim["dur"], "anim": {"in": "slide-up", "out": "fade"}})
        hook_method = "color-panel"
    elif kit == "handnote":
        cap.update(style={"font": "DejaVu Sans Mono", "bg": "#000000@0.62", "color": "#FFFFFF", "weight": 400, "size": 0.032, "align": "left", "x": 0.04, "radius": 0.1})
        if hook:
            g.append({"type": "note", "text": hook.get("short") or hook["text"], "size": 0.13, "rot": 4, "mark": "underline", "y": 0.18, "start": hs, "dur": min(hd, 3.5),
                      "anim": {"in": "pop", "out": "fade"}})
        if lst:
            g.append({"type": "note", "items": items(lst), "size": 0.05, "rot": -2, "x": 0.68, "y": 0.17, "start": lst["start"], "dur": lst["dur"], "anim": {"in": "fade"}})
        g += [{"type": "note", "text": e["text"], "size": 0.07, "rot": -3, "mark": "circle", "y": 0.2, "start": e["start"], "dur": e["dur"], "anim": {"in": "pop"}} for e in emph]
        if claim:
            g.append({"type": "note", "text": claim["text"], "size": 0.075, "rot": -3, "mark": "arrow", "y": 0.19, "start": claim["start"], "dur": claim["dur"], "anim": {"in": "pop"}})
        hook_method = "handwritten-note"
    else:  # kinetic
        cap.update(style={"bg": "#000000@0.55", "color": "#FFFFFF", "weight": 600, "size": 0.03, "y": 0.9})
        total = float(content.get("duration") or 60)
        words = content.get("words") or []

        def bars(text=None, wlist=None, start=0.0, dur=3.0, sub=None, size=0.1):
            c = {"type": "bars", "bleed": True, "y": 0.5, "x": 0.5, "start": start, "dur": dur, "size": size, "progress": round(min(1, start / total), 3),
                 "accent": th["accent"], "top": 0.05, "bottom": 0.24, "anim": {"in": "fade", "d": 0.3, "out": "fade", "dOut": 0.3}}
            if wlist:
                c["seq"] = wlist
            else:
                c["text"] = text
            if sub:
                c["sub"] = sub
            return c
        if hook:
            hw = [{"w": w["w"], "s": float(w["s"]) - hs} for w in words if hs - 0.01 <= float(w["s"]) < hs + hd] or [{"w": hook.get("short") or hook["text"], "s": 0}]
            g.append(bars(wlist=hw, start=hs, dur=hd, sub=hook["text"] if hook.get("short") else None, size=0.085))
        if lst:
            its = items(lst)
            g.append(bars(wlist=[{"w": i["text"].upper(), "s": i["at"]} for i in its], start=lst["start"], dur=lst["dur"], sub=lst.get("heading"), size=0.06))
        g += [bars(text=e["text"].upper(), start=e["start"], dur=e["dur"], size=0.06) for e in emph]
        if claim:
            g.append(bars(text=claim["text"].upper(), start=claim["start"], dur=claim["dur"], sub=claim.get("kicker"), size=0.065))
        hook_method = "kinetic-word"

    n_hard = len([x for x in g if x["type"] in ("block", "bars")])
    sfx = []
    for x in g:
        kind = {"classic": "pop", "editorial": None, "colorblock": "whoosh", "handnote": "pop", "kinetic": "whoosh"}[kit]
        if kind:
            sfx.append({"kind": kind, "t": round(float(x["start"]) + 0.05, 2)})
    zooms = []
    if claim:
        zooms.append({"from": float(claim["start"]) - 0.4, "to": float(claim["start"]) + float(claim["dur"]) * 0.8, **SMOOTH})
    meta = KITS[kit]
    return {"kit": kit, "axes": dict(meta["axes"], hook=hook_method), "graphics": g, "captions": cap, "sfx": sfx[:6], "zooms": zooms,
            "music_query": meta["music"], "heavy_elements": n_hard}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m montaj.kits")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    b = sub.add_parser("build")
    b.add_argument("kit")
    b.add_argument("content")
    b.add_argument("--theme")
    a = ap.parse_args(argv)
    if a.cmd == "list":
        for k in list_kits():
            print(f"{k['id']:11s} {k['name']} — {k['about']}  [{', '.join(k['suits'])}]")
        return 0
    content = json.load(open(a.content, encoding="utf-8"))
    theme = json.load(open(a.theme, encoding="utf-8")) if a.theme else None
    print(json.dumps(build(a.kit, content, theme), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
