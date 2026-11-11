"""Ortaq yükləyici: video konfiqi + house.json + tema + müştəri brend kiti → CFG (build.py ilə eyni sıra)."""
import json, os
from pathlib import Path

A = Path(__file__).resolve().parent
HOUSE = json.load(open(A / "house.json"))
DATA = Path(os.environ.get("MONTAJ_DATA_DIR", "/root/montaj-data"))
WORK = Path(os.environ.get("PRO_WORK", str(DATA / "plans" / "pro")))
OUT = Path(os.environ.get("PRO_OUT", str(DATA / "out" / "pro")))
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
FONT_R = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"

# kart rəngləri (build.py PALS-dan qısa nüsxə — üz qabığı və işarə üçün kifayətdir)
PALS = {"forest": {"acc": "#6CC57E", "ink": "#0F3B2C", "paper": "#FFFFFF", "txt": "#F4F8F5"},
        "adgreen": {"acc": "#6CC57E", "ink": "#0F3B2C", "paper": "#FFFFFF", "txt": "#FFFFFF"},
        "editorial": {"acc": "#7A1E3A", "ink": "#2B1D1A", "paper": "#F3ECDF", "txt": "#F4EDE4"}}


def brand(name):
    if not name: return {}
    for d in (os.environ.get("PRO_BRANDS"), str(A.parent.parent.parent / "instagram-clients")):
        f = Path(d or "", name, "brand_kit.json")
        if d and f.exists(): return json.load(open(f))
    raise SystemExit(f"Brend kiti tapılmadı: {name}")


def load(cfg_path):
    raw = json.load(open(cfg_path)); B = brand(raw.get("brand")); theme = raw.get("theme") or B.get("theme")
    cfg = {**HOUSE["common"], **HOUSE["ad" if raw.get("ad") or raw.get("type") == "ad" else "talk"],
           **HOUSE.get("themes", {}).get(theme, {}), **B.get("cfg", {}), **raw}
    pal = {**PALS.get(cfg.get("pal"), PALS["forest"]), **B.get("palette", {})}
    return cfg, B, pal


def scenes(cfg):
    f = WORK / f"v{cfg['n']}" / "scenes.json"
    return json.load(open(f))["scenes"] if f.exists() else []


OVER = {"lower", "top", "topchips", "equote", "esticker", "ename"}


def on_acc(pal):
    """Vurğu rənginin üstündəki yazı: tünd vurğuda ağ, açıqda tünd (oxunaqlılıq)."""
    a = pal.get("acc", "#6CC57E"); l = int(a[1:3], 16) * .299 + int(a[3:5], 16) * .587 + int(a[5:7], 16) * .114
    return "#FFFFFF" if l < 150 else pal.get("ink", "#111111")
