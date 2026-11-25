"""Rejissor köməkçisi: mənbənin mətnini oxuyub KONSEPT QƏRARINA lazım olan qısa brifi çıxarır (ucuz: tokensiz analiz).

Yaradıcı qərarı (hansı edit növü, niyə) agent verir — bu modul yalnız siqnalları ölçür, müştəri profilini və uyğun B-roll/musiqini toplayır,
və "düz danışıq" avtomatizminə qarşı qoruyur: düz edit yalnız əsaslandırılıb seçilə bilər. Qayda: `skills/meta/edit-director.md`.

  python -m montaj.director brief --pid <layihə> [--client xeyyam-huseynov] [--goal reklam|maarif|...]
  python -m montaj.director brief --text mətn.txt [--dur 55] [--client ...]
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SIG = {  # siqnal → kök sözlər (kiçik hərflə, AZ)
    "reklam": ["bizə yaz", "yazın", "qeydiyyat", "zəng", "endirim", "təlim", "proqram", "müraciət", "sifariş", "bio", "kurs", "təklif edir", "təklif etdi", "qoşul", "əlaqə"],
    "elm": ["araşdırma", "tədqiqat", "elm", "alim", "faiz", "%", "statistik", "təcrübə", "nəticə", "neyron", "hüceyr", "beyin", "yaddaş"],
    "mif": ["mif", "həqiqət", "yanlış", "doğru deyil", "inanc", "yayılmış", "əfsanə"],
    "hekayə": ["keçən dəfə", "bir gün", "dostum", "demişdi", "dedi ki", "soruşdum", "getmişdi", "olmuşdu", "xatırlayıram"],
    "praktik": ["necə", "addım", "metod", "üsul", "məsləhət", "etməlisiniz", "edin", "başlayın", "plan", "qayda"],
    "düşündürücü": ["görəsən", "fikirləşin", "düşünün", "bəlkə", "yoxsa", "nə olardı"],
}
FAMILIES = {  # edit ailəsi → nə vaxt, necə, alətlər
    "reklam": "Hook → ehtiyac → həll → təklif → CTA. Dinamik ritm, strateji vurğular, kinetik tipoqrafiya; CTA düyməsi yalnız danışıqda çağırış varsa.",
    "elmi-izah": "Fakt → araşdırma → izah → nəticə. İnfo kartları (rəqəm/termin), izahedici qrafik, mövzuya bağlı B-roll; balanslı ritm.",
    "mif-həqiqət": "İnanc → ziddiyyət → elmi izah. İkili kart (MİF/FAKT), ziddiyyət vurğusu; ritm orta.",
    "hekayə": "Hadisə → inkişaf → dönüş → nəticə. Real/atmosfer B-roll, minimal mətn, təbii mimika və pauzalar qorunur; sakit ritm.",
    "praktik": "Problem → metod → tətbiq. Addım siyahısı/nömrələr, ekran qrafiki, qısa nümunə B-roll.",
    "düşündürücü": "Sual → fərqli perspektiv → açıq final. Yavaş ritm, uzun pauzalar, sadə tipoqrafiya, final açıq qalır.",
    "sual-cavab": "Sual → cavab → əsaslandırma. Sual kartı (səsdə qalır), sakit təmiz edit, cavabda açar söz vurğusu.",
}


def _text(a: argparse.Namespace) -> tuple[str, float, list[float]]:
    if a.pid:
        pd = Path(os.environ.get("MONTAJ_DATA_DIR", Path.home() / "montaj-data")) / "projects" / a.pid / "analysis"
        f = sorted(glob.glob(str(pd / "*.json")))
        if not f: raise SystemExit(f"analiz yoxdur: {pd} (əvvəl `session new` + `storyboard`)")
        d = json.load(open(f[0], encoding="utf-8")); w = d.get("words", [])
        gaps = [b["s"] - a_["e"] for a_, b in zip(w, w[1:]) if b["s"] - a_["e"] > 0.05]
        return d.get("text") or " ".join(x["w"] for x in w), float(d.get("duration") or (w[-1]["e"] if w else 0)), gaps
    t = Path(a.text).read_text(encoding="utf-8"); return t, float(a.dur or 0), []


def signals(text: str) -> dict[str, int]:
    low = text.lower(); out = {k: sum(low.count(r) for r in roots) for k, roots in SIG.items()}
    out["sual"] = text.count("?"); out["rəqəm"] = len(re.findall(r"\d+", text))
    return out


def recommend(sg: dict[str, int], text: str, dur: float) -> list[tuple[str, int, str]]:
    first = re.split(r"(?<=[.?!])\s", text.strip(), maxsplit=1)[0]
    sc = {"reklam": sg["reklam"] * 3 + (2 if re.search(r"bizə yaz|yazın|qeydiyyat|təlim", text.lower()) else 0), "elmi-izah": sg["elm"] + sg["rəqəm"],
          "mif-həqiqət": sg["mif"] * 3, "hekayə": sg["hekayə"] * 3, "praktik": sg["praktik"] + sg["rəqəm"] // 2,
          "düşündürücü": sg["düşündürücü"] * 2, "sual-cavab": (3 if first.strip().endswith("?") else 0) + sg["sual"]}
    why = {"reklam": f"çağırış/təklif siqnalı {sg['reklam']}", "elmi-izah": f"elm/rəqəm siqnalı {sg['elm'] + sg['rəqəm']}", "mif-həqiqət": f"mif/həqiqət {sg['mif']}",
           "hekayə": f"hekayə markerləri {sg['hekayə']}", "praktik": f"praktik/addım {sg['praktik']}", "düşündürücü": f"düşündürücü {sg['düşündürücü']}",
           "sual-cavab": f"sual {sg['sual']}" + (", sual ilə açılır" if first.strip().endswith("?") else "")}
    return sorted(((k, v, why[k]) for k, v in sc.items() if v > 0), key=lambda x: -x[1])[:3] or [("maarifləndirici", 0, "güclü siqnal yoxdur")]


def broll_hints(text: str, n: int = 2) -> list[str]:
    from montaj import library
    out, seen = [], set()
    for w in dict.fromkeys(re.findall(r"[\wəıöüçşğ]+", text.lower())):
        if w in library.SYN and w not in seen:
            seen.add(w); hits = library.search(w, "broll", n)
            if hits: out.append(f"{w}: " + ", ".join(h["id"] for h in hits))
    return out[:8]


def client_info(slug: str | None) -> list[str]:
    if not slug: return ["müştəri göstərilməyib"]
    f = ROOT / "templates" / "expert-reels" / "experts" / f"{slug}.json"
    if not f.exists(): return [f"profil tapılmadı: {slug}"]
    p = json.load(open(f, encoding="utf-8")); lines = []
    pal = (p.get("visual") or {}).get("palette") or (p.get("theme") or {})
    lines.append(f"palitra: {pal}; şrift: {(p.get('visual') or {}).get('font', 'Montserrat')}")
    mp = p.get("music_policy")
    lines.append("musiqi: " + ("var (profil)" if mp and mp.get("use") else "YOX (profildə 'use': true yoxdur — soruşma, musiqisiz)" if True else ""))
    wf = p.get("workflow", {}); lines.append(f"storyboard: {wf.get('storyboard', 'profildə qayda yoxdur → ümumi axın')[:70]}")
    if p.get("structures"): lines.append("strukturlar: " + "; ".join(f"{k}: {v}" for k, v in p["structures"].items() if not k.startswith("_"))[:260])
    lines.append("sərbəstlik: konsept, animasiya, kart, ara kadr, ritm, imza elementləri; təsdiq lazım: rəng/şrift/mövqeləndirmə/daimi qaydalar")
    return lines


def brief(a: argparse.Namespace) -> str:
    text, dur, gaps = _text(a); sg = signals(text); rec = recommend(sg, text, dur)
    words = len(text.split()); wpm = words / dur * 60 if dur else 0
    L = [f"# Rejissor brifi", f"mətn: {words} söz" + (f", {dur:.0f} s, {wpm:.0f} söz/dəq" if dur else "") + (f", mənalı pauza (≥0.7 s): {sum(1 for g in gaps if g >= 0.7)}" if gaps else ""),
         "siqnallar: " + ", ".join(f"{k} {v}" for k, v in sg.items() if v)]
    if a.goal: L.append(f"məqsəd (istifadəçi): {a.goal}")
    L.append("## Edit ailəsi təklifi (siqnala görə; qərar sənindir, 1–2 cümləlik əsaslandırma yaz)")
    for k, v, w in rec: L.append(f"- {k} ({w}): {FAMILIES.get(k, '')}")
    L.append("## Müştəri"); L += [f"- {x}" for x in client_info(a.client)]
    bh = broll_hints(text)
    L.append("## B-roll kataloqundan uyğunlar (`python -m montaj.library get <id>`)"); L += [f"- {x}" for x in bh] or ["- açar söz uyğunluğu yoxdur (yalnız tipoqrafiya/qrafik məntiqlidir)"]
    L.append("## Qayda: düz edit avtomatik DEYİL. 'Onsuz da danışıqdır' səbəb sayılmır; düz edit seçsən niyə daha güclü olduğunu yaz. Hər video üçün konsepti 5–8 sətirdə yaz, uzun hesabat yox.")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m montaj.director"); sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("brief"); b.add_argument("--pid"); b.add_argument("--text"); b.add_argument("--dur", type=float); b.add_argument("--client"); b.add_argument("--goal")
    a = ap.parse_args()
    if not (a.pid or a.text): ap.error("--pid və ya --text lazımdır")
    print(brief(a))


if __name__ == "__main__":
    main()
