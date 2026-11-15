#!/usr/bin/env python3
"""AYRA Brand Workspace: hər müştəri qovluğunu 11 bölməli iş sahəsinə çevirir və çatışmayanları göstərir.
  workspace.py                 # bütün müştərilər: qovluqları yarat, WORKSPACE.md yenilə, xülasə çap et
  workspace.py <müştəri>       # bir müştərinin vəziyyəti
Mövcud fayllar SİLİNMİR və KÖÇÜRÜLMÜR; yalnız alt qovluqlar və WORKSPACE.md (avtomatik bölmə) yaradılır.
editing-dna.md yoxdursa şablondan yaradılır (sonra əl ilə doldurulur)."""
import json, sys, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; CL = ROOT / "instagram-clients"; AG = CL / "_agency"
DIRS = {"references/approved": "Approved References", "scripts": "Scripts & Storyboards", "raw": "Raw Assets",
        "assets": "Design & Motion Assets", "final": "Final Deliverables", "analytics": "Analytics & Growth"}
def j(p, d=None):
    try: return json.loads(Path(p).read_text())
    except Exception: return d
def clients(): return sorted(p.name for p in CL.iterdir() if p.is_dir() and not p.name.startswith("_"))
DNA = """# Editing DNA — {name}
_Hər yeni videoda əsas götürülür. Bilinməyən = [çatışmır]; uydurma yox. Təsdiqlənmiş nümunədən sonra yenilə._

## Montaj üslubu
{style}
## Rəng palitrası və rəng korreksiyası
Brend: {palette}. Korreksiya: color_auto (təbii dəri tonu).
## Subtitr dizaynı
[çatışmır]
## Şriftlər
{fonts}
## Motion üslubu
[çatışmır]
## B-roll seçimi
[çatışmır]
## Musiqi və sound design
[çatışmır]
## Keçidlər
[çatışmır]
## Hook dizaynı
[çatışmır]
## Cover dizaynı
[çatışmır] — ayra-professional-cover-designer; təsdiqdən sonra prinsiplər buraya.
## Təsdiqlənmiş video nümunələri
[çatışmır]
## İstifadə edilməməli effektlər
{dont}
## Son istifadə (təkrar olmasın)
—
"""
def build(c):
    d = CL / c; bk = j(d / "brand_kit.json", {}) or {}; pr = bk.get("profile", {}) or {}
    for sub in DIRS: (d / sub).mkdir(parents=True, exist_ok=True)
    rules = (j(AG / "qaydalar.json", {}) or {}).get("client", {}).get(c, [])
    q = [r for r in (j(AG / "istehsal.json", []) or []) if r.get("musteri") == c]
    pal = bk.get("palette") or {}
    if not (d / "editing-dna.md").exists():
        (d / "editing-dna.md").write_text(DNA.format(name=bk.get("name", c), style="[çatışmır]",
            palette=", ".join(f"{k} {v}" for k, v in pal.items()) or "[çatışmır]",
            fonts=", ".join(f"{k}: {v}" for k, v in (pr.get("fonts") or {}).items() if v) or "[çatışmır]",
            dont="\n".join("- " + r for r in rules) or "[çatışmır]"))
    has = lambda *n: [x for x in n if (d / x).exists()]
    miss = []
    if not pal: miss.append("brend palitrası (brand_kit.json → palette boşdur)")
    elif not pr.get("paletteApproved"): miss.append("palitra təsdiqi")
    if not has("strategiya.md", "context.md", "master_context.md", "brand.md"): miss.append("brend strategiyası / mövqe sənədi")
    if not has("voice.md"): miss.append("tone of voice (voice.md)")
    if not pr.get("audience"): miss.append("auditoriya təsviri")
    if "[çatışmır]" in (d / "editing-dna.md").read_text(): miss.append("Editing DNA-nın boş bölmələri")
    if not any((d / "references/approved").iterdir()): miss.append("təsdiqlənmiş referans/dizayn nümunələri")
    if not any((d / "analytics").iterdir()): miss.append("analitika (real rəqəmlər)")
    sec = f"""<!-- AVTO: workspace.py {datetime.date.today()} — bu blok yenilənir, aşağıya əl ilə yaz -->
# Brand Workspace — {bk.get('name', c)}

| # | Bölmə | Mənbə | Vəziyyət |
|---|---|---|---|
| 1 | Brand Strategy | {', '.join(has('strategiya.md','context.md','master_context.md','launch_strategy_v3.md')) or '—'} | {'var' if has('strategiya.md','context.md','master_context.md') else 'çatışmır'} |
| 2 | Brand Identity | brand_kit.json{', brand.md' if has('brand.md') else ''}{', brandbook.json' if has('brandbook.json') else ''} | {'təsdiqli' if pr.get('paletteApproved') else ('qaralama' if pal else 'çatışmır')} |
| 3 | Content Strategy | {', '.join(has('strategiya.md','plan_status.md','master_karusel_v1.md','metnler.txt')) or '—'} | {'var' if has('strategiya.md','plan_status.md') else 'qismən/çatışmır'} |
| 4 | Approved References | references/approved/ | {len(list((d/'references/approved').iterdir()))} fayl |
| 5 | Client Preferences | _agency/qaydalar.json → client | {len(rules)} qayda |
| 6 | Scripts & Storyboards | scripts/{', transkript/' if has('transkript') else ''} | {len(list((d/'scripts').iterdir()))} fayl |
| 7 | Raw Assets | raw/ (+ Drive) | {len(list((d/'raw').iterdir()))} fayl |
| 8 | Design & Motion Assets | assets/, editing-dna.md | {'DNA var' if has('editing-dna.md') else '—'} |
| 9 | Final Deliverables | final/ | {len(list((d/'final').iterdir()))} fayl |
| 10 | Analytics & Growth | analytics/ | {len(list((d/'analytics').iterdir()))} fayl |
| 11 | Task Tracker | _agency/istehsal.json | {len(q)} iş: {', '.join(f"{r['video']}={r['merhele']}" for r in q) or '—'} |

**Profil:** {pr.get('field') or '[çatışmır]'} · **Auditoriya:** {pr.get('audience') or '[çatışmır]'}

**Çatışmayan məlumat:** {'; '.join(miss) or 'yoxdur'}
<!-- /AVTO -->
"""
    p = d / "WORKSPACE.md"; old = p.read_text() if p.exists() else ""
    manual = old.split("<!-- /AVTO -->", 1)[1] if "<!-- /AVTO -->" in old else "\n## Qeydlər (əl ilə)\n"
    p.write_text(sec + manual)
    return {"musteri": c, "ad": bk.get("name", c), "approved": bool(pr.get("paletteApproved")), "palette": bool(pal),
            "jobs": q, "missing": miss, "rules": len(rules)}

if __name__ == "__main__":
    cs = sys.argv[1:] or clients(); out = [build(c) for c in cs]
    for o in out: print(f"{o['musteri']:20} işlər {len(o['jobs']):2}  çatışmır: {'; '.join(o['missing']) or '—'}")
    (AG / "workspaces.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
