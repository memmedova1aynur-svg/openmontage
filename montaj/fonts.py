"""Şriftlər: render (ffmpeg drawtext TTF tələb edir) və redaktor önizləməsi (woff2) eyni mənbədən.

Mənbə: templates/expert-reels/public/fonts (SIL OFL). Hər çəki üçün latin + latin-ext
alt-dəstləri birləşdirilir ki, bütün Azərbaycan hərfləri (ə ğ ı ö ü ş ç) olsun.
"""

from __future__ import annotations

from pathlib import Path

from montaj.config import REPO_ROOT, data_dir

SRC = REPO_ROOT / "templates" / "expert-reels" / "public" / "fonts"
FAMILIES = {
    "Montserrat": {"slug": "montserrat", "weights": [400, 600, 700, 800]},
    "Caveat": {"slug": "caveat", "weights": [400, 700]},
}
SYSTEM = {"DejaVu Sans": {400: "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                          700: "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"}}
# fontsource alt-dəst diapazonları (brauzer önizləməsi üçün)
RANGES = {
    "latin": "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, "
             "U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
    "latin-ext": "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, "
                 "U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF",
}


def nearest_weight(family: str, weight: int) -> int:
    ws = FAMILIES[family]["weights"] if family in FAMILIES else sorted(SYSTEM.get(family, {}))
    return min(ws, key=lambda w: abs(w - int(weight or 400))) if ws else 400


def woff2_files(family: str, weight: int) -> dict[str, Path]:
    f = FAMILIES[family]
    w = nearest_weight(family, weight)
    return {sub: SRC / f"{f['slug']}-{sub}-{w}-normal.woff2" for sub in ("latin", "latin-ext")}


def ttf_path(family: str | None, weight: int | None) -> str | None:
    """Render üçün TTF (keşlənir). Naməlum şrift -> DejaVu Sans."""
    family = family or "DejaVu Sans"
    weight = int(weight or 700)
    if family in SYSTEM or family not in FAMILIES:
        opts = SYSTEM["DejaVu Sans"] if family not in SYSTEM else SYSTEM[family]
        p = opts[min(opts, key=lambda w: abs(w - weight))]
        return p if Path(p).is_file() else None
    w = nearest_weight(family, weight)
    out = data_dir() / "fonts" / f"{FAMILIES[family]['slug']}-{w}.ttf"
    if not out.is_file():
        from fontTools.merge import Merger
        from fontTools.ttLib import TTFont

        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = []
        for sub, src in woff2_files(family, w).items():
            t = TTFont(str(src))
            t.flavor = None
            dst = out.with_name(f"{out.stem}-{sub}.ttf")
            t.save(str(dst))
            tmp.append(str(dst))
        Merger().merge(tmp).save(str(out))
        for x in tmp:
            Path(x).unlink(missing_ok=True)
    return str(out)


def editor_font_files() -> list[tuple[str, int, str, Path]]:
    """(ailə, çəki, alt-dəst, woff2 faylı) — redaktora asset kimi yüklənir."""
    res = []
    for fam, f in FAMILIES.items():
        for w in f["weights"]:
            for sub, p in woff2_files(fam, w).items():
                res.append((fam, w, sub, p))
    return res
