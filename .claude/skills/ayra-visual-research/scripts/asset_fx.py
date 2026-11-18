#!/usr/bin/env python3
"""AYRA asset keyfiyyət alətləri (Pillow + numpy). Dizayna qoymazdan ƏVVƏL işlət.

  python3 asset_fx.py qc cut.png                      # maska keyfiyyəti: PASS / WARN / FAIL + səbəb
  python3 asset_fx.py tone cut.png out.png --to "#F5B8D0" [--amount 0.12] [--sat 0.9] [--contrast 1.05]
  python3 asset_fx.py shadow cut.png out.png [--spread 0.9] [--opacity 0.35] [--color "#8A1F4A"]   # kontakt kölgəsi (obyektin altına)
  python3 asset_fx.py grain in.png out.png [--amount 6]                                         # yalnız konsept tələb edəndə
  python3 asset_fx.py subject photo.jpg cut.png [--model birefnet-portrait]                     # «mətn subyektin arxasında» üçün ön qat
"""
import argparse, sys
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance


def qc(path):
    im = Image.open(path).convert("RGBA"); a = np.asarray(im.getchannel("A")).astype(float) / 255
    rgb = np.asarray(im.convert("RGB")).astype(float)
    solid, semi = a > 0.95, (a > 0.05) & (a <= 0.95)
    cover = solid.mean(); semi_ratio = semi.sum() / max(1, solid.sum())
    issues = []
    if min(im.size) < 500: issues.append(("WARN", f"kiçik ölçü {im.size} — 1080 kadrda ≤45% enində istifadə et"))
    if cover < 0.12: issues.append(("FAIL", f"obyekt kadrın {cover:.0%}-ni tutur — kəsim boşdur/uğursuzdur"))
    if semi_ratio > 0.18: issues.append(("FAIL", f"yarımşəffaf piksel {semi_ratio:.0%} — bulanıq/qeyri-müəyyən kənar (fon qalığı və ya fokusdan kənar obyekt)"))
    elif semi_ratio > 0.09: issues.append(("WARN", f"yarımşəffaf piksel {semi_ratio:.0%} — kənarlara yaxından bax"))
    # kənara dirənən kəsim (obyekt kadrdan kəsilib)
    edge = max(solid[0].mean(), solid[-1].mean(), solid[:, 0].mean(), solid[:, -1].mean())
    if edge > 0.25: issues.append(("WARN", f"obyekt kadr kənarında kəsilib ({edge:.0%}) — yalnız kadrdan çıxan kompozisiyada istifadə et"))
    # halo: kənar halqasının rəngi daxili rəngdən çox açıqdırsa (ağ fon qalığı)
    er = np.asarray(Image.fromarray((solid * 255).astype("uint8")).filter(ImageFilter.MinFilter(9))) > 127
    ring = solid & ~er
    if ring.sum() > 50 and er.sum() > 50:
        d = rgb[ring].mean() - rgb[er].mean()
        if d > 38: issues.append(("WARN", f"kənar halqası daxildən {d:.0f} vahid açıqdır — ağ halo ehtimalı (kənarı 1–2px sıx)"))
    # kəskinlik
    g = np.asarray(im.convert("L").filter(ImageFilter.FIND_EDGES)).astype(float)
    sharp = g[er].std() if er.sum() else 0
    if sharp < 9: issues.append(("WARN", f"aşağı kəskinlik ({sharp:.1f}) — bulanıq foto"))
    level = "FAIL" if any(l == "FAIL" for l, _ in issues) else ("WARN" if issues else "PASS")
    print(f"{level}  {path}  ölçü={im.size} örtük={cover:.0%} yarımşəffaf={semi_ratio:.0%} kəskinlik={sharp:.1f}")
    for l, t in issues: print(f"   [{l}] {t}")
    return level


def hexrgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def tone(src, dst, to, amount=0.12, sat=1.0, contrast=1.0, bright=1.0):
    im = Image.open(src).convert("RGBA"); a = im.getchannel("A"); rgb = im.convert("RGB")
    rgb = ImageEnhance.Color(rgb).enhance(sat); rgb = ImageEnhance.Contrast(rgb).enhance(contrast); rgb = ImageEnhance.Brightness(rgb).enhance(bright)
    if to and amount:   # brend rənginə yumşaq «soft light» uyğunlaşdırma — forma dəyişmir
        tint = Image.new("RGB", rgb.size, hexrgb(to)); rgb = Image.blend(rgb, Image.composite(tint, rgb, rgb.convert("L").point(lambda v: 255 - abs(v - 128))), amount)
    rgb.putalpha(a); rgb.save(dst); print(dst)


def shadow(src, dst, spread=0.9, opacity=0.35, color="#8A1F4A", pad=80):
    """Obyektin alt kənarına yapışan yumşaq kontakt kölgəsi + geniş mühit kölgəsi (üstdən/öndən işıq)."""
    im = Image.open(src).convert("RGBA"); w, h = im.size
    out = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0)); a = im.getchannel("A")
    c = hexrgb(color)
    amb = Image.new("L", out.size, 0); amb.paste(a, (pad, pad + int(h * 0.035)))
    amb = amb.filter(ImageFilter.GaussianBlur(max(8, w * 0.035 * spread))).point(lambda v: int(v * opacity * 0.55))
    con = Image.new("L", out.size, 0); sq = a.resize((w, max(2, int(h * 0.10)))); con.paste(sq, (pad, pad + h - int(h * 0.07)))
    con = con.filter(ImageFilter.GaussianBlur(max(5, w * 0.018 * spread))).point(lambda v: int(v * opacity))
    for m in (amb, con): out.alpha_composite(Image.merge("RGBA", (*[Image.new("L", out.size, x) for x in c], m)))
    out.alpha_composite(im, (pad, pad)); out.save(dst); print(dst, "pad", pad)


def grain(src, dst, amount=6):
    im = Image.open(src).convert("RGB"); n = np.random.default_rng(7).normal(0, amount, (im.height, im.width, 1))
    Image.fromarray(np.clip(np.asarray(im).astype(float) + n, 0, 255).astype("uint8")).save(dst); print(dst)


def subject(src, dst, model="birefnet-portrait", maxside=1400):
    from rembg import new_session, remove
    im = Image.open(src).convert("RGB"); im.thumbnail((maxside, maxside))
    cut = remove(im, session=new_session(model)); cut.save(dst); print(dst, cut.size)   # KƏSİLMİR: orijinalla eyni ölçü, üst-üstə qoymaq üçün


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("qc"); p.add_argument("src", nargs="+")
    p = sub.add_parser("tone"); p.add_argument("src"); p.add_argument("dst"); p.add_argument("--to", default=None); p.add_argument("--amount", type=float, default=0.12); p.add_argument("--sat", type=float, default=1.0); p.add_argument("--contrast", type=float, default=1.0); p.add_argument("--bright", type=float, default=1.0)
    p = sub.add_parser("shadow"); p.add_argument("src"); p.add_argument("dst"); p.add_argument("--spread", type=float, default=0.9); p.add_argument("--opacity", type=float, default=0.35); p.add_argument("--color", default="#8A1F4A")
    p = sub.add_parser("grain"); p.add_argument("src"); p.add_argument("dst"); p.add_argument("--amount", type=float, default=6)
    p = sub.add_parser("subject"); p.add_argument("src"); p.add_argument("dst"); p.add_argument("--model", default="birefnet-portrait")
    a = ap.parse_args()
    if a.cmd == "qc": sys.exit(1 if "FAIL" in [qc(s) for s in a.src] else 0)
    if a.cmd == "tone": tone(a.src, a.dst, a.to, a.amount, a.sat, a.contrast, a.bright)
    if a.cmd == "shadow": shadow(a.src, a.dst, a.spread, a.opacity, a.color)
    if a.cmd == "grain": grain(a.src, a.dst, a.amount)
    if a.cmd == "subject": subject(a.src, a.dst, a.model)
