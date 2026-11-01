"""Claude Code sessiyasında montaj (əlavə xərcsiz yol).

Bu modul panel serverinin EYNİ kodunu (Drive yükləmə, analiz, kadraj, storyboard,
render) komanda sətrindən işlədir. İstifadəçi iPhone-dakı Claude tətbiqindən
sessiyanı özü başladır; nəticələr (storyboard şəkli, MP4, layihə faylı) fayl kimi
telefona göndərilir.

Bu, DAİMİ və ya AVTOMATİK AI bağlantısı deyil: sessiya istifadəçi başladanda
işləyir, konteyner müvəqqətidir. Layihə faylı (montaj.json) panelin öz formatıdır
və panel harada işləyirsə orada açıla bilər.

İstifadə:
  python -m montaj.session new --title "Ad" --link <drive-linki> [--file yol] [--client "Ad"]
                               [--aspect 9:16] [--cut suggest|keep|auto] [--duration 30]
                               [--format talking_head] [--goal sales] [--style clean] [--extras subtitle]
  python -m montaj.session storyboard <pid>
  python -m montaj.session edit <pid> [--exclude 2,3] [--include 4] [--text 1="Mətn"] [--alt 2]
  python -m montaj.session apply <pid>
  python -m montaj.session render <pid>
  python -m montaj.session export <pid>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

import numpy as np

os.environ.setdefault("MONTAJ_SYNC_DERIVE", "1")

from montaj import analysis, clients, drive, store, types  # noqa: E402
from montaj.config import data_dir  # noqa: E402
from montaj.errors import UserError  # noqa: E402

UI = Path(__file__).resolve().parent / "ui" / "timeline.js"


def node_tl(fn: str, *args: Any) -> Any:
    """timeline.js funksiyasını Node ilə çağırır (brauzerdəki panel ilə eyni məntiq)."""
    js = ("import(" + json.dumps(UI.as_uri()) + ").then(TL=>{const a=JSON.parse(require('fs').readFileSync(0,'utf8'));"
          f"const r=TL.{fn}(...a);process.stdout.write(JSON.stringify(r));}}).catch(e=>{{console.error(e.message);process.exit(1);}})")
    out = subprocess.run(["node", "-e", js], input=json.dumps(list(args)), capture_output=True, text=True)
    if out.returncode != 0:
        raise UserError(f"Model xətası: {out.stderr.strip()[:300]}", "Parametrləri yoxlayın.")
    return json.loads(out.stdout)


def out_dir(pid: str) -> Path:
    d = Path(os.environ.get("MONTAJ_OUT_DIR", data_dir() / "out")) / pid
    d.mkdir(parents=True, exist_ok=True)
    return d


def fmt(t: float) -> str:
    m = int(t // 60)
    return f"{m}:{t - m * 60:05.2f}"


# ---------------------------------------------------------------------------

def cmd_new(a: argparse.Namespace) -> None:
    from montaj import server  # _register, output-size və s. üçün

    vt = _type_record(a) if a.type else None
    if vt and vt["type"] in (5, 7) and "event" not in (a.format or []):
        a.format = [*(a.format or []), "event"]  # tədbir kadrajı (storyboard) — M09
    if not a.aspect:
        a.aspect = (vt and types.get(vt["type"]).get("aspect")) or "9:16"
    base = node_tl("migrate", node_tl("newProject", {"id": "tmp", "title": a.title}))
    p = store.create(a.title, base)
    pid = p["id"]
    for link in a.link or []:
        tmp, name = drive.download(link, store.originals_dir(pid), lambda x: None)
        r = server._register(pid, tmp, name, {"type": "drive", "id": drive.parse_link(link)["id"]})
        print(f"media: {r['media']['name']}  {r['media'].get('width')}x{r['media'].get('height')}  "
              f"{r['media']['duration']} san  kodek={r['media'].get('videoCodec')}  hdr={r['media'].get('hdr')}")
    for f in a.file or []:
        tmp = store.originals_dir(pid) / f".cli_{Path(f).name}.part"
        shutil.copyfile(f, tmp)
        r = server._register(pid, tmp, Path(f).name)
        print(f"media: {r['media']['name']}  {r['media']['duration']} san")
    brand = None
    if a.client:
        c = next((x for x in clients.load_all() if x["name"].lower() == a.client.lower()), None)
        if not c:
            raise UserError(f"Müştəri tapılmadı: {a.client}", "Adı siyahıdakı kimi yazın və ya --client vermədən birdəfəlik layihə edin.")
        brand = {k: c.get(k) for k in ("id", "name", "field", "colors", "font", "logo", "preferences")}
    options = {"format": a.format or [], "goal": a.goal or [], "style": a.style or [], "extras": a.extras or [],
               "duration": a.duration, "cutMode": a.cut, "aspect": a.aspect, "language": "az", "useAi": False}
    prof = expert_profile(a.client) if a.client else None
    if prof and glossary_terms(prof):
        options["hotwords"] = " ".join(glossary_terms(prof))  # Whisper-ə müştərinin terminləri
    proj = store.load(pid)
    proj = node_tl("migrate", proj)
    from montaj import reframe
    w, h = reframe.output_size(reframe.primary_video(proj["media"]), a.aspect if a.aspect in reframe.ASPECTS else "source")
    if a.size:  # məs. 16:9 seminar → 9:16: kəsim kiçik olur; istəyə görə 1080x1920-yə böyüdülür (yumşalma açıq bildirilir)
        w, h = (int(x) // 2 * 2 for x in a.size.lower().split("x"))
    proj.update(options=options, aspect=a.aspect, width=w, height=h, brand=brand, clientId=brand and brand["id"])
    if vt:
        proj["videoType"] = vt
    store.save(pid, proj, proj["revision"])
    print(f"layihə: {pid}  çıxış: {w}x{h}")
    if vt:
        print(f"növ: {vt['type']} — {vt['name']}" + (f" + {', '.join(map(str, vt['extra']))}" if vt["extra"] else "")
              + f"; yanaşma: {'+'.join(vt['approaches'])}  (ətraflı: types {vt['type']})")


# ---------------------------------------------------------------------------
# Video növləri (montaj/types.py reyestri)
# ---------------------------------------------------------------------------

def _type_record(a: argparse.Namespace) -> dict[str, Any]:
    try:
        return types.record(a.type, [int(x) for x in (a.extra or [])], ", ".join(a.goal or []) if isinstance(a.goal, list) else (a.goal or ""),
                            types.parse_approaches(a.approach) if a.approach else None, a.subtype or "", a.uncertain or "")
    except (KeyError, ValueError) as e:
        raise UserError(str(e).strip("'\""), "Növlərin siyahısı: `python -m montaj.session types`.") from None


def _type_lines(n: int) -> list[str]:
    t = types.get(n)
    out = [f"{n}. {t['name']} — {types.STATUS_LABEL[t['status']]}"]
    if t.get("gaps"):
        out.append(f"   çatışmır: {t['gaps']}")
    if t.get("subtypes"):
        out.append(f"   alt növlər: {', '.join(t['subtypes'])}")
    if t["approaches"]:
        out.append("   yanaşmalar: " + ", ".join(f"{k} {types.APPROACHES[k]['name']}" for k in t["approaches"]))
    for letter, (ap, desc) in zip("ABC", t["variants"]):
        out.append(f"   storyboard {letter}: {ap} — {desc}")
    if t["commands"]:
        out.append(f"   əmrlər: {' → '.join(t['commands'])}")
    rules = [r for r in t.get("rules", [])]
    if rules:
        out.append(f"   avtomatik yoxlama (verify): {', '.join(rules)}")
    for x in t.get("notes", []):
        out.append(f"   qayda: {x}")
    return out


def cmd_types(a: argparse.Namespace) -> None:
    """Video növləri / yanaşmalar / sorğu sualları — reyestrdən."""
    if a.survey:
        print(json.dumps(types.survey(), ensure_ascii=False, indent=1))
        return
    if a.approaches:
        for k, ap in types.APPROACHES.items():
            print(f"{k} {ap['name']} — {types.STATUS_LABEL[ap['status']]}: {ap['what']}" + (f" | çatışmır: {ap['gaps']}" if ap.get("gaps") else ""))
        return
    if a.n:
        try:
            print("\n".join(_type_lines(a.n)))
        except KeyError as e:
            raise UserError(str(e).strip("'\""), "Növlərin siyahısı: `python -m montaj.session types`.") from None
        return
    for k, f in types.FAMILIES.items():
        print(f"{f['label']}:")
        for n in f["types"]:
            t = types.TYPES[n]
            print(f"  {n:>2}. {t['name']} [{types.STATUS_LABEL[t['status']]}] — {'+'.join(t['approaches']) or '—'}")


def cmd_set_type(a: argparse.Namespace) -> None:
    """Mövcud layihəyə növ qeydi (analizdən sonra növ dəqiqləşəndə)."""
    p = store.load(a.pid)
    vt = _type_record(a)
    p["videoType"] = vt
    if not (p.get("options") or {}).get("goal") and vt["goal"]:
        p["options"] = {**(p.get("options") or {}), "goal": [vt["goal"]]}
    store.save(a.pid, p, p["revision"])
    print("\n".join(_type_lines(vt["type"])))


def _type_hints(project: dict[str, Any]) -> list[str]:
    """storyboard-dan sonra: növ, 3 variant, qaydalar, müştərinin son seçimləri (təkrarın qarşısını almaq üçün)."""
    vt = project.get("videoType")
    out = []
    if not vt:
        out.append("növ qeyd olunmayıb — transkripti oxu, `set-type <pid> <N>` (siyahı: `types`)")
    else:
        out += _type_lines(vt["type"])
        for e in vt.get("extra") or []:
            out.append(f"   + əlavə növ {e}: {types.get(e)['name']}")
    name = (project.get("brand") or {}).get("name")
    prof = expert_profile(name) if name else None
    hist = [h for h in (prof or {}).get("history") or [] if isinstance(h, dict)][-3:]
    if hist:
        out.append("müştərinin son seçimləri (eyni giriş/qutu/effekt ardıcıllığını təkrarlama):")
        for h in hist:
            bits = [str(h.get(k)) for k in ("date", "type", "approach", "variant", "look") if h.get(k)]
            st = h.get("style")
            if isinstance(st, dict):
                bits.append(", ".join(f"{k}={v}" for k, v in st.items()))
            out.append(f"   - {h.get('video', '')}: {'; '.join(bits)}")
    return out


def _remember_choice(pid: str, plan: dict[str, Any], plan_name: str) -> None:
    """Seçilən variant: layihənin növ qeydinə yanaşma, müştəri profilinin tarixçəsinə qısa qeyd."""
    import datetime

    p = store.load(pid)
    aps = re.findall(r"M\d\d", str(plan.get("approach") or "").upper())
    vt = p.get("videoType")
    if vt and aps:
        vt["approaches"] = aps
        store.save(pid, p, p["revision"])
    name = (p.get("brand") or {}).get("name")
    f = profile_path(name) if name else None
    if not f:
        return
    prof = json.loads(f.read_text(encoding="utf-8"))
    entry = {"video": p.get("title"), "date": datetime.date.today().isoformat(), "engine": "montaj",
             "type": vt and vt["type"], "approach": "+".join(aps) or None, "variant": plan.get("title") or plan_name,
             "look": plan.get("look"), "captions": ((plan.get("captions") or {}).get("style") or {}).get("type")}
    prof.setdefault("history", []).append({k: v for k, v in entry.items() if v})
    f.write_text(json.dumps(prof, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"müştəri tarixçəsinə yazıldı: {f.name} → history")



def contact_sheet(pid: str, sb: dict[str, Any], dst: Path) -> Path:
    """Telefonda baxmaq üçün storyboard şəkli (real kadrlar + vaxt + transkript)."""
    from PIL import Image, ImageDraw, ImageFont

    project = store.load(pid)
    media = {m["id"]: m for m in project["media"]}
    font_p = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    fb = ImageFont.truetype(font_p.replace(".ttf", "-Bold.ttf"), 22)
    fr_ = ImageFont.truetype(font_p, 18)
    vertical = (sb.get("options") or {}).get("aspect") in ("9:16", "4:5")
    tw, th = (270, 480) if vertical else (480, 270)
    cols = 3 if vertical else 2
    cell_h = th + 190
    cards = sb["cards"]
    rows = (len(cards) + cols - 1) // cols
    W = cols * (tw + 24) + 24
    img = Image.new("RGB", (W, rows * (cell_h + 24) + 24 + 70), (20, 22, 26))
    d = ImageDraw.Draw(img)
    gen = "Qaydalara əsaslanan təklif (səssizlik + söz sərhədi)" if sb.get("generator") == "rules" else f"Plan: {sb.get('generator')}"
    d.text((24, 22), f"{project['title']} — {gen}", font=fb, fill=(232, 234, 238))
    tmpd = out_dir(pid) / "_frames"
    tmpd.mkdir(exist_ok=True)
    for i, c in enumerate(cards):
        m = media[c["mediaId"]]
        x = 24 + (i % cols) * (tw + 24)
        y = 24 + 70 + (i // cols) * (cell_h + 24)
        t = (c["srcIn"] + c["srcOut"]) / 2
        fr = (sb.get("frames") or {}).get(c["mediaId"])
        vf = f"scale={tw}:{th}:force_original_aspect_ratio=decrease,pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2"
        if fr and fr.get("mode") in ("auto", "manual") and m.get("hasVideo"):
            k = fr["keys"][0]
            cw, ch = fr.get("baseW", 1) * fr.get("s", 1), fr.get("baseH", 1) * fr.get("s", 1)
            vf = (f"crop=iw*{cw:.4f}:ih*{ch:.4f}:max(0\\,min(iw-ow\\,iw*{k['cx']:.4f}-ow/2)):"
                  f"max(0\\,min(ih-oh\\,ih*{k['cy']:.4f}-oh/2)),scale={tw}:{th}")
        if m.get("hdr"):
            vf = "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p," + vf
        fpath = tmpd / f"{i}.jpg"
        if m.get("hasVideo"):
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{0 if m.get('isImage') else t:.2f}", "-i",
                            str(store.project_dir(pid) / m["file"]), "-frames:v", "1", "-vf", vf, str(fpath)], capture_output=True)
        if fpath.is_file():
            img.paste(Image.open(fpath).convert("RGB"), (x, y))
        else:
            d.rectangle([x, y, x + tw, y + th], fill=(0, 0, 0))
        if not c.get("include"):
            d.rectangle([x, y, x + tw, y + th], outline=(255, 95, 95), width=6)
        status = "✓ qalır" if c.get("include") else "✕ çıxarılır"
        d.text((x, y + th + 8), f"#{i + 1}  {status}", font=fb, fill=(232, 234, 238) if c.get("include") else (255, 140, 140))
        d.text((x, y + th + 38), f"{fmt(c['srcIn'])}–{fmt(c['srcOut'])} ({c['srcOut'] - c['srcIn']:.1f} s)",
               font=fr_, fill=(154, 161, 173))
        d.text((x, y + th + 60), m["name"][:24 if vertical else 44], font=fr_, fill=(154, 161, 173))
        txt = (f"Mətn: {c['onScreenText']} · " if c.get("onScreenText") else "") + (c.get("transcript") or "")
        for j, line in enumerate(textwrap.wrap(txt, 24 if vertical else 44)[:4]):
            d.text((x, y + th + 88 + j * 24), line, font=fr_, fill=(207, 211, 218))
    img.save(dst, quality=88)
    return dst


def _load_draft(pid: str) -> dict[str, Any]:
    f = store.project_dir(pid) / "storyboard_draft.json"
    if not f.is_file():
        raise UserError("Storyboard yoxdur.", "Əvvəl `storyboard` əmrini işlədin.")
    return json.loads(f.read_text(encoding="utf-8"))


def _save_draft(pid: str, sb: dict[str, Any]) -> None:
    (store.project_dir(pid) / "storyboard_draft.json").write_text(json.dumps(sb, ensure_ascii=False), encoding="utf-8")


def summary(pid: str, sb: dict[str, Any]) -> str:
    project = store.load(pid)
    media = {m["id"]: m for m in project["media"]}
    lines = [f"# Storyboard — {project['title']}", "",
             "Plan: qaydalara əsaslanan bölmə (uzun səssizlik + söz sərhədi)." if sb["generator"] == "rules" else f"Plan: {sb['generator']}"]
    inc = [c for c in sb["cards"] if c.get("include")]
    lines.append(f"Qalan: {len(inc)} hissə, {sum(c['srcOut'] - c['srcIn'] for c in inc):.1f} san")
    for mid, fr in (sb.get("frames") or {}).items():
        for w in fr.get("warnings") or []:
            lines.append(f"- Kadraj ({media[mid]['name']}): {w}")
    lines.append("")
    for i, c in enumerate(sb["cards"]):
        lines.append(f"{i + 1}. {'✓' if c.get('include') else '✕'} {fmt(c['srcIn'])}–{fmt(c['srcOut'])} "
                     f"({c['srcOut'] - c['srcIn']:.1f} s) {media[c['mediaId']]['name']}"
                     + (f" | mətn: {c['onScreenText']}" if c.get("onScreenText") else ""))
        if c.get("transcript"):
            lines.append(f"   “{c['transcript']}”")
    return "\n".join(lines)


def cmd_storyboard(a: argparse.Namespace) -> None:
    from montaj import server

    project = store.load(a.pid)
    sb = server.build_storyboard(a.pid, project.get("options") or {})
    o = out_dir(a.pid)
    print(contact_sheet(a.pid, sb, o / "storyboard.jpg"))
    (o / "storyboard.md").write_text(summary(a.pid, sb), encoding="utf-8")
    print(o / "storyboard.md")
    for mid in sb.get("candidates", {}):
        an = analysis.analysis_path(store.project_dir(a.pid), mid)
        if an.is_file():
            d = json.loads(an.read_text())
            print(f"transkript {mid}: dil={d.get('language')} sözlər={len(d.get('words', []))} "
                  f"{'(XƏTA: ' + d['transcribeError'] + ')' if d.get('transcribeError') else ''}")
    for line in _type_hints(project):
        print(line)


def _parse_nums(s: str | None) -> list[int]:
    return [int(x) for x in (s or "").replace(" ", "").split(",") if x]


def cmd_edit(a: argparse.Namespace) -> None:
    sb = _load_draft(a.pid)
    cards = sb["cards"]
    for n in _parse_nums(a.exclude):
        cards[n - 1]["include"] = False
    for n in _parse_nums(a.include):
        cards[n - 1]["include"] = True
    for t in a.text or []:
        n, _, val = t.partition("=")
        cards[int(n) - 1]["onScreenText"] = val.strip().strip('"')
    if a.order:
        order = _parse_nums(a.order)
        sb["cards"] = [cards[n - 1] for n in order] + [c for i, c in enumerate(cards) if i + 1 not in order]
    if a.subtitles is not None:
        sb["subtitles"] = a.subtitles == "on"
    _save_draft(a.pid, sb)
    o = out_dir(a.pid)
    contact_sheet(a.pid, sb, o / "storyboard.jpg")
    (o / "storyboard.md").write_text(summary(a.pid, sb), encoding="utf-8")
    print(summary(a.pid, sb))


def cmd_apply(a: argparse.Namespace) -> None:
    """Təsdiqlənmiş storyboard-u montaja tətbiq edir (panelin applyStoryboard funksiyası ilə)."""
    sb = _load_draft(a.pid)
    p = store.load(a.pid)
    r = node_tl("applyStoryboard", node_tl("migrate", p), sb, {"frames": sb.get("frames") or {}, "brand": p.get("brand")})
    proj = r["project"]
    proj["storyboardDraft"] = None
    saved = store.save(a.pid, proj, p["revision"])
    print(f"tətbiq olundu: {r['applied']} hissə; atlanan: {r['skipped']}; versiya {saved['revision']}")


def cmd_render(a: argparse.Namespace) -> None:
    from montaj import media as mediautil
    from montaj.render import conversions, render
    from montaj.server import _project_logo

    p = store.load(a.pid)
    for mid, b in (p.get("background") or {}).items():  # bərpadan sonra törəmə fon videosu yoxdursa yenidən hazırlanır
        if b.get("file") and not (store.project_dir(a.pid) / b["file"]).is_file():
            from montaj import background

            m = next((x for x in p["media"] if x["id"] == mid), None)
            if m:
                print(f"{m['name']}: arxa fon yenidən hazırlanır…")
                background.process(store.project_dir(a.pid) / m["file"], store.project_dir(a.pid) / b["file"], b["spec"],
                                   _bg_scene_file(a.pid, p, b["spec"]))
    out = out_dir(a.pid) / f"{a.pid}_r{p['revision']}.mp4"
    render(p, store.project_dir(a.pid), out, lambda x: None, logo_path=_project_logo(p, a.pid))
    info = mediautil.probe(out)
    print(out)
    print(f"çıxış: {info['width']}x{info['height']} {info['fps']} fps {info['duration']} san "
          f"{out.stat().st_size / 1e6:.1f} MB")
    for c in conversions(p):
        print("-", c)
    from montaj.render import delivery_copy, measure_loudness
    lo = measure_loudness(out)
    if lo:
        print(f"- səs: {lo['input_i']:.1f} LUFS, pik {lo['input_tp']:.1f} dBTP")
    ig = delivery_copy(out, out.with_name(out.stem + "_ig.mp4"))
    if ig:
        print(f"telefon/Instagram nüsxəsi: {ig}  {ig.stat().st_size / 1e6:.1f} MB (eyni ölçü və kadr tezliyi)")


EDITOR_TEMPLATE = Path(__file__).resolve().parent / "editor" / "editor.html"
EDITOR_KEYS = ("id", "title", "revision", "width", "height", "fps", "fpsRate", "tracks", "clips", "subtitles", "mirrorAll")


def inline_timeline() -> str:
    """timeline.js-i (ES modul) adi skriptə çevirir: window.TL = {...}. Kod təkrarlanmır."""
    import re

    src = UI.read_text(encoding="utf-8")
    names = re.findall(r"^export (?:async )?(?:function|const|class|let) (\w+)", src, flags=re.M)
    body = re.sub(r"^export (?=(?:async )?(?:function|const|class|let) )", "", src, flags=re.M)
    return "(() => {\n" + body + "\nwindow.TL = { " + ", ".join(names) + " };\n})();"


def editor_data(pid: str, assets: dict[str, str]) -> dict[str, Any]:
    """Redaktor üçün minimal layihə: Drive linki, fayl yolları, storyboard, brend və caption DAXİL DEYİL."""
    import hashlib

    p = store.load(pid)
    proj = {k: p.get(k) for k in EDITOR_KEYS}
    proj["media"] = [{k: m.get(k) for k in ("id", "name", "duration", "width", "height", "hasAudio", "hasVideo", "isImage")}
                     for m in p["media"]]
    media = {m["id"]: {"url": assets.get(m["id"]), "name": m["name"], "duration": m["duration"],
                       "width": m.get("width"), "height": m.get("height")} for m in p["media"]}
    build = hashlib.sha1((EDITOR_TEMPLATE.read_text() + UI.read_text()).encode()).hexdigest()[:10]
    from montaj import fonts

    fl = [{"family": fam, "weight": w, "sub": sub, "range": fonts.RANGES[sub], "url": assets.get(f"font:{f.name}")}
          for fam, w, sub, f in fonts.editor_font_files()]
    brand = p.get("brand") or {}
    th = brand.get("theme") or {}
    colors = [c for c in [th.get("primary"), th.get("accent"), th.get("accentSoft"), th.get("primaryDeep")] if c] or (brand.get("colors") or [])
    proj["media"] = proj["media"]
    return {"project": proj, "media": media, "build": build, "fonts": fl, "brandColors": colors, "theme": th,
            "brandName": brand.get("name")}


def make_preview(src: Path, dst: Path, hdr: bool) -> None:
    """Telefonda baxış üçün yüngül nüsxə (qısa tərəf 540 px). Render bundan HAZIRLANMIR."""
    tm = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
          "zscale=t=bt709:m=bt709:r=tv,") if hdr else ""
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-map", "0:v:0", "-map", "0:a:0?",
                    "-vf", tm + "scale='if(gt(iw,ih),-2,540)':'if(gt(iw,ih),540,-2)',format=yuv420p",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "30", "-g", "15", "-c:a", "aac", "-b:a", "96k",
                    "-movflags", "+faststart", str(dst)], check=True, capture_output=True)


def cmd_editor(a: argparse.Namespace) -> None:
    p = store.load(a.pid)
    d = out_dir(a.pid) / "editor"
    d.mkdir(exist_ok=True)
    assets = json.loads(Path(a.assets).read_text()) if a.assets else {}
    if a.local:
        from montaj import fonts

        assets = {m["id"]: f"preview_{m['id']}.mp4" for m in p["media"]}
        for _fam, _w, _sub, f in fonts.editor_font_files():
            shutil.copyfile(f, d / f.name)
            assets[f"font:{f.name}"] = f.name
    if True:
        for m in p["media"]:
            if m.get("hasVideo") and not m.get("isImage"):
                dst = d / f"preview_{m['id']}.mp4"
                if not dst.is_file():
                    make_preview(store.project_dir(a.pid) / m["file"], dst, bool(m.get("hdr")))
                print(f"önizləmə: {dst}  {dst.stat().st_size / 1e6:.1f} MB")
    data = json.dumps(editor_data(a.pid, assets), ensure_ascii=False).replace("</", "<\\/")
    html = EDITOR_TEMPLATE.read_text(encoding="utf-8")
    html = (html.replace("/*__DATA__*/", data, 1).replace("/*__TIMELINE__*/", inline_timeline(), 1)
            .replace("/*__GRAPHICS__*/", (EDITOR_TEMPLATE.parent / "graphics.js").read_text(encoding="utf-8"), 1))
    (d / "index.html").write_text(html, encoding="utf-8")
    print(d / "index.html")


def cmd_apply_edits(a: argparse.Namespace) -> None:
    """Telefondakı redaktordan gələn düzəlişləri tətbiq edir (yalnız həmin elementlər dəyişir)."""
    edits = json.loads(Path(a.edits).read_text(encoding="utf-8"))
    edits = edits.get("data", edits)  # ArtifactData sənədi və ya xam fayl
    p = store.load(a.pid)
    if edits.get("schema") == 2:
        from montaj import media as mediautil

        adir = Path(a.assets_dir) if a.assets_dir else out_dir(a.pid) / "assets"
        missing = []
        for m in edits.get("newMedia") or []:
            if not m.get("asset") or any(x["id"] == m["id"] for x in p["media"]):
                continue
            found = sorted(adir.glob(f"{m['asset']}*")) if adir.is_dir() else []
            if not found:
                missing.append(m["asset"])
                continue
            ext = Path(m.get("name") or "").suffix.lower()[:8] or found[0].suffix or ".bin"
            dst = store.originals_dir(a.pid) / f"{m['id']}{ext}"
            if not dst.exists():
                shutil.copyfile(found[0], dst)
                os.chmod(dst, 0o444)
            info = mediautil.probe(dst)
            m.update(info, file=f"media/originals/{dst.name}", size=dst.stat().st_size, source={"type": "artifact-asset", "id": m["asset"]})
        if missing:
            raise UserError("Redaktorda əlavə olunmuş fayllar hələ endirilməyib.",
                            f"Artifact read path=<id> out_dir={adir} ilə endirin: " + ", ".join(missing))
        r = node_tl("applyEditorState", p, edits)
        durs = {m["id"]: float(m["duration"]) for m in r["project"]["media"]}
        for c in r["project"]["clips"]:  # brauzerin ölçdüyü müddət probe-dan bir az fərqli ola bilər
            if c.get("media") in durs and c["srcOut"] > durs[c["media"]]:
                c["srcOut"] = round(durs[c["media"]], 3)
        cur_rev = p["revision"]
        for m in edits.get("newMedia") or []:  # media qeydləri yalnız serverin probe nəticəsi ilə əlavə olunur
            if m.get("file") and not any(x["id"] == m["id"] for x in p["media"]):
                cur_rev = store.add_media_record(a.pid, {k: v for k, v in m.items() if k != "asset"})["revision"]
        saved = store.save(a.pid, r["project"], cur_rev)
        print(f"tətbiq olundu: {len(r['changed'])} dəyişən, {len(r['removed'])} silinən element; versiya {p['revision']} -> {saved['revision']}")
        if r["changed"] or r["removed"]:
            print("dəyişən:", ", ".join(r["changed"][:20]), "| silinən:", ", ".join(r["removed"][:20]))
        return
    r = node_tl("applyEdits", p, edits)
    if not r["applied"] and not r["rejected"]:
        print(f"dəyişiklik yoxdur: {len(r['already'])} element artıq tətbiq olunub; versiya {p['revision']}")
        return
    if not r["applied"] and r["rejected"]:
        raise UserError("Heç bir düzəliş tətbiq olunmadı.", "; ".join(f"{x['id']}: {x['reason']}" for x in r["rejected"]))
    saved = store.save(a.pid, r["project"], p["revision"])
    print(f"tətbiq olundu: {len(r['applied'])} element; rədd: {r['rejected']}; versiya {p['revision']} -> {saved['revision']}"
          + ("" if r["sameBase"] else " (redaktor köhnə versiyadan idi — yalnız dəyişməmiş elementlər tətbiq olundu)"))


def glossary_terms(prof: dict[str, Any]) -> list[str]:
    """Profilin söz lüğəti: "glossary": {"terms": [...], "fixes": [{"from", "to"}]} — düzgün yazılışlar."""
    g = prof.get("glossary") or {}
    terms = list(g.get("terms") or []) + [f["to"] for f in g.get("fixes") or []]
    return list(dict.fromkeys(t for t in terms if t))


def profile_path(name: str) -> Path | None:
    import unicodedata

    def norm(x: str) -> str:
        x = x.lower().translate(str.maketrans("əöüğışç", "eougisc"))
        return "".join(ch for ch in unicodedata.normalize("NFKD", x) if ch.isalnum())
    d = Path(__file__).resolve().parent.parent / "templates" / "expert-reels" / "experts"
    for f in sorted(d.glob("*.json")):
        if not f.name.startswith("_") and norm(json.loads(f.read_text(encoding="utf-8")).get("name", "")) == norm(name):
            return f
    return None


def expert_profile(name: str) -> dict[str, Any] | None:
    """templates/expert-reels/experts/ içində YALNIZ adı uyğun gələn profili oxuyur."""
    import unicodedata

    def norm(x: str) -> str:
        x = x.lower().translate(str.maketrans("əöüğışç", "eougisc"))
        return "".join(ch for ch in unicodedata.normalize("NFKD", x) if ch.isalnum())
    d = Path(__file__).resolve().parent.parent / "templates" / "expert-reels" / "experts"
    want = norm(name)
    for f in sorted(d.glob("*.json")):
        if f.name.startswith("_"):
            continue
        prof = json.loads(f.read_text(encoding="utf-8"))
        if norm(prof.get("name", "")) == want:
            return prof
    return None


def cmd_set_client(a: argparse.Namespace) -> None:
    prof = expert_profile(a.client)
    if not prof:
        raise UserError(f"Profil tapılmadı: {a.client}", "Adı profildəki kimi yazın.")
    p = store.load(a.pid)
    p["brand"] = {"name": prof["name"], "field": prof.get("activity", ""), "theme": prof.get("theme"),
                  "colors": [v for k, v in (prof.get("theme") or {}).items() if isinstance(v, str) and v.startswith("#")],
                  "colorsConfirmed": not any(w in (prof.get("theme_source") or "").lower() for w in ("derived", "chosen by us", "colour family")), "palette": prof.get("palette"),
                  "fonts": prof.get("fonts"), "cautions": prof.get("cautions") or [], "source": "expert-reels profil"}
    saved = store.save(a.pid, p, p["revision"])
    kind = "müştərinin kodları" if p["brand"]["colorsConfirmed"] else "rəng ailəsi (yaxın çalarlar olar)"
    print(f"müştəri: {prof['name']}; rəng: {kind}; versiya {saved['revision']}")


def _sfx_media(pid: str, kind: str) -> dict[str, Any]:
    """expert-reels-in sintez edilmiş (müəllif hüququ olmayan) səs effektini layihəyə media kimi əlavə edir."""
    import importlib.util

    from montaj import media as mediautil

    mid = f"sfx_{kind}"
    p = store.load(pid)
    have = next((m for m in p["media"] if m["id"] == mid), None)
    if have:
        return have
    lib = data_dir() / "sfx"
    if not (lib / f"{kind}.wav").is_file():
        spec = importlib.util.spec_from_file_location(
            "build_edit", Path(__file__).resolve().parent.parent / "templates" / "expert-reels" / "scripts" / "build_edit.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.synth_sfx(lib)
    dst = store.originals_dir(pid) / f"{mid}.wav"
    shutil.copyfile(lib / f"{kind}.wav", dst)
    rec = {"id": mid, "name": f"{kind}.wav (sintez)", "file": f"media/originals/{dst.name}", "size": dst.stat().st_size,
           "source": {"type": "synth", "kind": kind}, **mediautil.probe(dst)}
    store.add_media_record(pid, rec)
    return rec


# Rəng korreksiyası şablonları — hamısı yüngül; dəri rəngi və detal qorunur; süni kəskinlik/"4K effekti" yoxdur.
# Hər video üçün `looks` əmri orijinal + A/B/C müqayisə şəklini bir neçə təmsilçi kadrda hazırlayır,
# istifadəçi seçir, seçim plan.json-da "look" ilə verilir ("look": null — rəng düzəlişi yoxdur).
LOOKS: dict[str, dict[str, float]] = {
    "A": {"contrast": 1.03, "saturation": 1.03, "vibrance": 0.04},
    "B": {"brightness": 0.012, "contrast": 0.98, "saturation": 1.04, "vibrance": 0.03, "temperature": 6100},
    "C": {"contrast": 1.04, "saturation": 0.98, "depth": 0.6, "temperature": 6700},
    "D": {"denoise": 1.0, "shadows": 1.0, "gamma": 1.35, "saturation": 1.05, "vibrance": 0.03},  # zəif işıq (kafe və s.)
}
LOOK_LABELS = {"A": "orijinala yaxın, təbii", "B": "yumşaq və isti", "C": "təmiz və neytral", "D": "zəif işıq: dən azalır, kölgə açılır"}
LOOK_KEYS = ("brightness", "contrast", "saturation", "vibrance", "depth", "sharpen", "temperature", "denoise", "shadows", "gamma")
DARK_LUMA = 85  # 8-bit orta parlaqlıq bundan aşağıdırsa — zəif işıq (D variantı təklif olunur)
DEFAULT_LOOK = "A"


def _rep_frames(p: dict[str, Any], n: int = 3) -> list[tuple[dict[str, Any], float]]:
    """Təmsilçi kadrlar: fərqli kliplərdən / videonun fərqli hissələrindən (mənbə vaxtı ilə)."""
    media = {m["id"]: m for m in p["media"]}
    vids = [c for c in p["clips"] if c["track"] == "v1" and media.get(c.get("media"), {}).get("hasVideo")
            and not media[c["media"]].get("isImage")]
    if vids:
        vids = sorted(vids, key=lambda c: -(c["srcOut"] - c["srcIn"]))[:n]
        if len(vids) < n:  # az klip — ən uzun klipin içindən əlavə kadr
            c = vids[0]
            extra = [(c, c["srcIn"] + (c["srcOut"] - c["srcIn"]) * k / (n + 1)) for k in range(1, n + 1)]
            return [(media[c["media"]], t) for c, t in extra][:n]
        return [(media[c["media"]], (c["srcIn"] + c["srcOut"]) / 2) for c in vids]
    m = next((x for x in p["media"] if x.get("hasVideo") and not x.get("isImage")), None)
    if not m:
        raise UserError("Layihədə video yoxdur.", "Əvvəlcə `new` ilə video əlavə edin.")
    d = float(m.get("duration") or 3)
    return [(m, d * k / (n + 1)) for k in range(1, n + 1)]


def cmd_looks(a: argparse.Namespace) -> None:
    """Rəng variantları: sətirlər — təmsilçi kadrlar, sütunlar — Orijinal, A, B, C (render ilə eyni filtrlər)."""
    from montaj import render

    p = store.load(a.pid)
    frames = _rep_frames(p, a.frames)
    if a.t:
        m0 = frames[0][0]
        frames = [(m0, float(t)) for t in a.t]
    font = render._font()
    o = out_dir(a.pid)
    from montaj import quality
    lum = [quality.mean_luma(store.project_dir(a.pid) / m["file"], t) for m, t in frames]
    lum = [x for x in lum if x is not None]
    dark = bool(lum) and sum(lum) / len(lum) < DARK_LUMA
    cols = ["orijinal", *[k for k in LOOKS if k != "D" or dark or a.all]]
    tiles: list[Path] = []
    for r, (m, t) in enumerate(frames):
        src = store.project_dir(a.pid) / m["file"]
        for name in cols:
            label = "Orijinal" if name == "orijinal" else f"{name}: {LOOK_LABELS[name]}"
            adj = {} if name == "orijinal" else LOOKS[name]
            f = ([render.HDR_TO_SDR] if m.get("hdr") else []) + render.color_filters(adj) + render.sharpen_filter(adj)
            f.append("scale=360:-2:flags=lanczos")
            if font and r == 0:
                esc = label.replace("\\", "").replace(":", "\\:").replace("'", "")
                f.append(f"drawbox=y=0:w=iw:h=34:color=black@0.65:t=fill,drawtext=fontfile={font}:text='{esc}':x=8:y=8:fontsize=17:fontcolor=white")
            tile = o / f"reng_{r}_{name}.png"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", str(src), "-frames:v", "1",
                            "-vf", ",".join(f), str(tile)], check=True)
            tiles.append(tile)
    k = len(cols)
    ins = sum((["-i", str(x)] for x in tiles), [])
    rows = "".join(f"{''.join(f'[{r * k + i}]' for i in range(k))}hstack={k}[r{r}];" for r in range(len(frames)))
    fc = rows + ("".join(f"[r{r}]" for r in range(len(frames))) + f"vstack={len(frames)}" if len(frames) > 1 else "").rstrip(";")
    if len(frames) == 1:
        fc = rows.rstrip(";").replace("[r0]", "")
    sheet = o / "reng_variantlari.jpg"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", fc, "-q:v", "3", str(sheet)], check=True)
    for x in tiles:
        x.unlink()
    print("kadrlar:", ", ".join(f"{m.get('name')} {t:.1f} s" for m, t in frames))
    if lum:
        print(f"orta parlaqlıq: {sum(lum) / len(lum):.0f}/255" + (" — zəif işıq: D variantı təklif olunur" if dark else ""))
    print(sheet)


def _music_media(pid: str, src: Path) -> dict[str, Any]:
    """İstifadəçinin verdiyi musiqi faylını layihəyə media kimi əlavə edir (orijinal dəyişmir)."""
    import hashlib

    from montaj import media as mediautil

    src = Path(src)
    if not src.is_file():
        raise UserError(f"Musiqi faylı tapılmadı: {src}", "Faylı söhbətə əlavə edin və ya linkini verin.")
    h = hashlib.sha1(src.read_bytes()).hexdigest()[:10]
    mid = f"music_{h}"
    have = next((m for m in store.load(pid)["media"] if m["id"] == mid), None)
    if have:
        return have
    dst = store.originals_dir(pid) / f"{mid}{src.suffix.lower() or '.m4a'}"
    shutil.copyfile(src, dst)
    os.chmod(dst, 0o444)
    rec = {"id": mid, "name": src.name, "file": f"media/originals/{dst.name}", "size": dst.stat().st_size,
           "source": {"type": "music", "name": src.name}, **mediautil.probe(dst)}
    rec.update(hasVideo=False, isImage=False)  # üz qabığı şəkli olan fayllar da yalnız səs kimi
    if not rec.get("hasAudio"):
        raise UserError("Musiqi faylında səs yoxdur.", "Başqa fayl verin.")
    store.add_media_record(pid, rec)
    return rec


def _cover_frame(m: dict[str, Any], W: int, H: int) -> dict[str, Any] | None:
    """B-roll-un çıxış kadrını doldurması üçün mərkəzdən kəsim (boş/qara zolaq qalmır)."""
    sw, sh = float(m.get("width") or W), float(m.get("height") or H)
    ar, src_ar = W / H, sw / sh
    if abs(src_ar - ar) < 0.02:
        return None
    bw, bh = (ar * sh / sw, 1.0) if src_ar > ar else (1.0, (sw / ar) / sh)
    return {"aspect": "out", "mode": "auto", "s": 1.0, "baseW": round(bw, 5), "baseH": round(bh, 5),
            "keys": [{"t": 0, "cx": 0.5, "cy": 0.5}], "rotate": 0, "warnings": []}


def _find_media(q: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    key = b.get("media") or b.get("name")
    m = next((x for x in q["media"] if x["id"] == key or x.get("name") == key), None)
    if not m:
        raise UserError(f"B-roll materialı tapılmadı: {key}", "Əvvəlcə `add-broll` ilə əlavə edin; id və ya fayl adını yazın.")
    if not m.get("hasVideo"):
        raise UserError(f"{m.get('name')}: B-roll üçün video və ya şəkil lazımdır.", "Səs faylı üçün plan-da `music`/`sfx` işlədin.")
    return m


def _insert_point(pid: str, q: dict[str, Any], t: float) -> tuple[dict[str, Any], float]:
    """Araya kadr üçün yer: t-yə ən yaxın təbii pauza (söz arası), söz kəsilmir."""
    from montaj import media as mediautil
    from montaj import quality

    pos = 0.0
    for c in node_tl("videoClips", q):
        d = c["srcOut"] - c["srcIn"]
        if pos <= t <= pos + d:
            break
        pos += d
    else:
        raise UserError(f"Araya kadr vaxtı ({t:.1f} s) montajdan kənardadır.", "Vaxtı yekun montajın müddəti daxilində verin.")
    if abs(t - pos) < 0.12 or abs(pos + d - t) < 0.12:  # klip sərhədi — artıq kəsimdir
        return c, (pos if abs(t - pos) < 0.12 else pos + d)
    m = next(x for x in q["media"] if x["id"] == c["media"])
    words = (json.loads(analysis.analysis_path(store.project_dir(pid), m["id"]).read_text(encoding="utf-8")).get("words")
             if analysis.analysis_path(store.project_dir(pid), m["id"]).is_file() else []) or []
    # altyazının söz vaxtları da nəzərə alınır (altyazı sözü bölünməsin)
    sub_words = ((q.get("subtitles") or {}).get("words") or {}).get(m["id"]) or []
    words = sorted({(w["s"], w["e"], w["w"]) for w in [*words, *sub_words]})
    words = [{"s": a, "e": b, "w": w} for a, b, w in words]
    merged: list[dict[str, Any]] = []
    for w in words:  # üst-üstə düşən sözlər bir aralıq sayılır
        if merged and w["s"] < merged[-1]["e"]:
            merged[-1]["e"] = max(merged[-1]["e"], w["e"])
        else:
            merged.append(dict(w))
    words = merged
    src_t = c["srcIn"] + (t - pos)
    gaps = [((a["e"] + b["s"]) / 2, b["s"] - a["e"]) for a, b in zip(words, words[1:])
            if c["srcIn"] + 0.15 < (a["e"] + b["s"]) / 2 < c["srcOut"] - 0.15]
    if gaps:
        mid, _gap = min(gaps, key=lambda g: abs(g[0] - src_t) - 0.3 * min(g[1], 0.6))
        if abs(mid - src_t) <= 1.5:
            src_t = mid
    if m.get("hasAudio"):
        rms = quality.frame_rms(mediautil.read_mono(store.project_dir(pid) / m["file"], quality.SR))
        src_t, _ok = quality.safe_boundary(rms, src_t, "out", words, quality.speech_level(rms), window=0.08)
    return c, round(pos + (src_t - c["srcIn"]), 3)


def _pip_place(pid: str, q: dict[str, Any], at: float, dur: float, m: dict[str, Any], scale: float) -> tuple[float, float, str]:
    """PIP üçün yer: üzü (və altyazı zonasını) örtməyən ilk namizəd. Üz əsas videonun həmin anından tapılır."""
    from montaj import reframe

    W, H = float(q["width"]), float(q["height"])
    pw = scale
    ph = scale * W / H * float(m.get("height") or 9) / float(m.get("width") or 16)  # H vahidində
    pos, face = 0.0, None
    for c in node_tl("videoClips", q):
        d = c["srcOut"] - c["srcIn"]
        if pos <= at < pos + d and not c.get("broll"):
            mm = next(x for x in q["media"] if x["id"] == c["media"])
            s0 = c["srcIn"] + (at - pos)
            smp = reframe.detect_faces(store.project_dir(pid) / mm["file"], s0, min(c["srcOut"], s0 + dur), step=0.5)
            fs = [f for x in smp for f in x["faces"][:1]]
            if fs:
                face = (min(f["x"] for f in fs), min(f["y"] for f in fs),
                        max(f["x"] + f["w"] for f in fs), max(f["y"] + f["h"] for f in fs))
            break
        pos += d
    cands = [("yuxarı-orta", 0.5, 0.12), ("yuxarı-sol", 0.27, 0.12), ("yuxarı-sağ", 0.73, 0.12),
             ("orta-sol", 0.25, 0.45), ("orta-sağ", 0.75, 0.45)]
    best = None
    for name, cx, cy in cands:
        box = (cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2)
        ov = 0.0
        if face:  # üz qutusu 15% genişləndirilir (saç, çənə)
            fx0, fy0, fx1, fy1 = face
            ex, ey = (fx1 - fx0) * 0.15, (fy1 - fy0) * 0.25
            ix = max(0.0, min(box[2], fx1 + ex) - max(box[0], fx0 - ex))
            iy = max(0.0, min(box[3], fy1 + ey) - max(box[1], fy0 - ey))
            ov = ix * iy
        ov += max(0.0, box[3] - 0.66) * pw  # altyazı zonası
        if best is None or ov < best[0] - 1e-6:
            best = (ov, name, cx, cy)
        if ov == 0:
            break
    note = best[1] + ("" if face else " (üz tapılmadı)") + ("" if best[0] == 0 else " — üzə qismən toxunur, yoxlayın")
    return best[2], best[3], note


def _apply_broll(pid: str, q: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """Plan-ın bir B-roll elementi.
    mode="cover" (standart): əsas videonun üstündə, danışıq və altyazı davam edir;
    mode="pip": küncdə kiçik pəncərə (pip: {scale, x, y});
    mode="insert": araya kadr — əsas video ən yaxın təbii pauzada dayanır, kadr öz səsi ilə oynayır, sonra davam edir."""
    import uuid as _uuid

    if b.get("make"):  # Claude-un hazırladığı səhnə (render keşlənir)
        rec = _make_broll_media(pid, q, b["make"], float(b.get("dur", 2.5)))
        if not any(x["id"] == rec["id"] for x in q["media"]):
            q["media"].append(rec)
        b = {**b, "media": rec["id"]}
    m = _find_media(q, b)
    W, H = int(q["width"]), int(q["height"])
    dur = float(b.get("dur", 2.5))
    src_in = float(b.get("from", 0))
    if not m.get("isImage"):
        src_in = min(src_in, max(0.0, float(m["duration"]) - 0.2))
        dur = min(dur, float(m["duration"]) - src_in)
    if dur < 0.3:
        raise UserError(f"{m.get('name')}: B-roll çox qısadır.", "dur və from dəyərlərini yoxlayın.")
    mode = b.get("mode", "cover")
    frame = _cover_frame(m, W, H) if mode not in ("pip", "sticker") else None
    if mode in ("cover", "pip", "cover_pip", "sticker"):
        clip = {"id": "b_" + _uuid.uuid4().hex[:10], "track": "v2", "media": m["id"], "srcIn": round(src_in, 3),
                "srcOut": round(src_in + dur, 3), "start": round(float(b["at"]), 3), "mode": mode,
                "origin": "plan", "manual": False}
        if frame:
            clip["frame"] = frame
        if mode == "cover_pip":  # danışan küncdə dairədə qalır
            clip["pip"] = {"size": float(b.get("size", 0.3)), "x": float(b.get("x", 0.07)), "y": float(b.get("y", 0.6))}
        if mode == "pip":
            sc = float(b.get("scale", 0.42))
            if b.get("x") is not None and b.get("y") is not None:
                x, y, why = float(b["x"]), float(b["y"]), "plan"
            else:
                x, y, why = _pip_place(pid, q, float(b["at"]), dur, m, sc)
            clip["pip"] = {"scale": sc, "x": x, "y": y, "placed": why}
        q["clips"].append(clip)
        return q
    if mode != "insert":
        raise UserError(f"Naməlum B-roll rejimi: {mode}", "cover, cover_pip, pip, sticker və ya insert yazın.")
    c, cut = _insert_point(pid, q, float(b["at"]))
    lay = {x["id"]: s for x, s in zip(node_tl("videoClips", q), np.cumsum([0] + [y["srcOut"] - y["srcIn"] for y in node_tl("videoClips", q)])[:-1])}
    if lay[c["id"]] + 0.12 < cut < lay[c["id"]] + (c["srcOut"] - c["srcIn"]) - 0.12:
        q = node_tl("split", q, c["id"], cut)
    seq = node_tl("videoClips", q)
    bounds = [sum(y["srcOut"] - y["srcIn"] for y in seq[:i]) for i in range(len(seq) + 1)]
    idx = min(range(len(bounds)), key=lambda i: abs(bounds[i] - cut))  # sərhədə yaxın nöqtə (bölünmədisə) — həmin sərhəd
    if abs(bounds[idx] - cut) > 0.15:
        raise UserError(f"Araya kadr üçün yer tapılmadı ({cut:.2f} s).", "Başqa vaxt verin.")
    vid = "v_" + _uuid.uuid4().hex[:10]
    clip = {"id": vid, "track": "v1", "media": m["id"], "srcIn": round(src_in, 3), "srcOut": round(src_in + dur, 3),
            "order": 10_000, "origin": "plan", "manual": False, "broll": True}
    if frame:
        clip["frame"] = frame
    q["clips"].append(clip)
    if m.get("hasAudio") and float(b.get("volume", 1.0)) > 0:
        q["clips"].append({"id": "a_" + _uuid.uuid4().hex[:10], "track": "a1", "media": m["id"], "srcIn": clip["srcIn"],
                           "srcOut": clip["srcOut"], "linkedTo": vid, "volume": float(b.get("volume", 1.0)),
                           "fadeIn": 0.05, "fadeOut": 0.08, "origin": "plan", "manual": False})
    return node_tl("moveVideo", q, vid, idx)


def apply_plan(pid: str, p: dict[str, Any], plan: dict[str, Any], plan_name: str = "plan.json") -> dict[str, Any]:
    """Planı layihənin SURƏTİNƏ tətbiq edir və nəticəni qaytarır (saxlamır). Storyboard variantlarının
    önizləməsi və `plan` əmri eyni funksiyanı işlədir."""
    from montaj import quality

    for s in plan.get("sfx") or []:
        _sfx_media(pid, s["kind"])
    mus = plan.get("music")
    mus_rec = _music_media(pid, Path(mus["file"])) if mus else None
    q = node_tl("migrate", p)
    was_manual = {c["id"] for c in q["clips"] if c.get("manual")}
    q["clips"] = [c for c in q["clips"] if not (c.get("origin") == "plan" and not c.get("manual"))]
    if plan.get("captions") and q.get("subtitles"):
        q = node_tl("setSubtitleStyle", q, plan["captions"].get("style") or {})
        q["subtitles"]["enabled"] = plan["captions"].get("enabled", True)
        q["clips"] = [c for c in q["clips"] if not (c["track"] == "t1" and c.get("origin") == "ai")] if plan.get("dropStoryboardText") else q["clips"]
    br = q.get("brand") or {}
    prof = expert_profile(br["name"]) if br.get("name") else None
    fixes = ((prof or {}).get("glossary") or {}).get("fixes") or []
    for c in [*fixes, *(plan.get("corrections") or [])]:  # müştəri lüğəti + plan düzəlişləri
        if q.get("subtitles"):
            q = node_tl("replaceEverywhere", q, c["from"], c["to"])["project"]
    for z in plan.get("zooms") or []:  # punch-in: klip zaman xəttində bölünür, ortadakı hissə yaxınlaşdırılır
        for t in (z["to"], z["from"]):
            seg = next((c for c in node_tl("videoClips", q)
                        if _start(q, c["id"]) + 0.15 < t < _start(q, c["id"]) + c["srcOut"] - c["srcIn"] - 0.15), None)
            if seg:
                q = node_tl("split", q, seg["id"], t)
        mid = next(c for c in node_tl("videoClips", q) if abs(_start(q, c["id"]) - z["from"]) < 0.05)
        m = next(x for x in q["media"] if x["id"] == mid["media"])
        cur = mid.get("frame") or {}  # avtomatik kadraj düzəlişi (fırlatma, ortalama) punch-in-də də qalır
        base_s = float(cur.get("s") or 1) if cur.get("mode") in ("auto", "manual") else 1.0
        k0 = (cur.get("keys") or [{}])[0] if cur.get("mode") in ("auto", "manual") else {}
        fr = {"aspect": q.get("aspect") or "source", "mode": "auto", "s": round(base_s / float(z.get("scale", 1.12)), 4),
              "baseW": cur.get("baseW", 1) if k0 else 1, "baseH": cur.get("baseH", 1) if k0 else 1,
              "keys": [{"t": mid["srcIn"], "cx": z.get("cx", k0.get("cx", 0.5)), "cy": z.get("cy", k0.get("cy", 0.45))}],
              "rotate": cur.get("rotate", 0), "warnings": [], "planZoom": True}
        if m.get("width") and q.get("width") and abs(m["width"] / m["height"] - q["width"] / q["height"]) > 0.02:
            raise UserError("Punch-in yalnız eyni ölçülü kadrda avtomatik qurulur.", "Kadrajı redaktorda əl ilə edin.")
        q = node_tl("setFrame", q, mid["id"], fr, {"manual": False})
    if plan.get("multicam"):  # virtual multikamera (plan ölçüləri) — punch-in əvəzinə
        q, rep = _apply_multicam(pid, q, plan["multicam"])
        q["multicamReport"] = {k: v for k, v in rep.items() if k != "plans"}
    from montaj.graphics import DEFAULT_XY
    for g in plan.get("graphics") or []:
        d = DEFAULT_XY.get(g.get("type"), (0.5, 0.5))  # yer verilməyibsə növün standart yeri (addGraphic 0.5 qoyurdu)
        q = node_tl("addGraphic", q, {"x": d[0], "y": d[1], **g, "origin": "plan"})

    for b in plan.get("broll") or []:
        q = _apply_broll(pid, q, b)

    # rəng: plan şablonu ("look" işarəsi olan) yenilənir, əl ilə dəyişdirilmiş rəngə toxunulmur
    look_name = plan.get("look", DEFAULT_LOOK)
    if look_name and look_name not in LOOKS:
        raise UserError(f"Naməlum rəng şablonu: {look_name}", "Mövcud: " + ", ".join(LOOKS))
    vids = [c for c in q["clips"] if c["track"] in ("v1", "v2")]
    owned = [c for c in vids if not any(k in (c.get("adjust") or {}) for k in LOOK_KEYS) or (c.get("adjust") or {}).get("look")]
    expo = quality.exposure_offsets([c for c in owned if c["track"] == "v1"], {m["id"]: m for m in q["media"]}, store.project_dir(pid)) \
        if look_name and plan.get("matchExposure", True) else {}
    for c in owned:
        adj = {k: v for k, v in (c.get("adjust") or {}).items() if k not in LOOK_KEYS and k != "look"}
        if look_name:
            adj.update(LOOKS[look_name], look=look_name)
            if c["id"] in expo:
                adj["brightness"] = round(adj.get("brightness", 0) + expo[c["id"]], 3)
        if adj:
            c["adjust"] = adj
        else:
            c.pop("adjust", None)

    for s in plan.get("sfx") or []:
        med = next(x for x in store.load(pid)["media"] if x["id"] == f"sfx_{s['kind']}")
        if not any(x["id"] == med["id"] for x in q["media"]):
            q["media"].append(med)
        q = node_tl("addMedia", {**q, "media": [x for x in q["media"] if x["id"] != med["id"]]}, med,
                    {"targetTrack": "s1", "at": s["t"]})
        new = q["clips"][-1]
        new["volume"] = s.get("vol", 0.3)
        new["origin"] = "plan"
    if mus_rec:  # musiqi: m1 trekində, yumşaq giriş/çıxış, danışıqda azalır
        q["clips"] = [c for c in q["clips"] if not (c["track"] == "m1" and c.get("origin") == "plan")]
        total = sum(c["srcOut"] - c["srcIn"] for c in node_tl("videoClips", q))
        at = float(mus.get("start", 0))
        q = node_tl("addMedia", {**q, "media": [x for x in q["media"] if x["id"] != mus_rec["id"]]}, mus_rec,
                    {"targetTrack": "m1", "at": at})
        new = q["clips"][-1]
        src_in = float(mus.get("from", 0))
        new.update(srcIn=round(src_in, 3), srcOut=round(min(float(mus_rec["duration"]), src_in + max(0.5, total - at)), 3),
                   volume=float(mus.get("volume", 0.12)), fadeIn=float(mus.get("fadeIn", 1.2)),
                   fadeOut=float(mus.get("fadeOut", 2.0)), origin="plan")
        q.setdefault("mix", {})["duck"] = bool(mus.get("duck", True))
    live = plan.get("liveSound")
    if live is not None:  # M09: görüntünün öz səsi (standart söndürülür), seçilmiş kartlarda (alqış, gülüş) saxlanılır
        card_of = {c["id"]: c.get("cardId") for c in q["clips"] if c["track"] == "v1"}
        keep = {str(k): float(v) for k, v in (live.get("keep") or {}).items()}
        for c in q["clips"]:
            if c["track"] == "a1" and c.get("linkedTo") in card_of and not c.get("manual"):
                c["volume"] = keep.get(str(card_of[c["linkedTo"]]), float(live.get("volume", 0.0)))
    for c in q["clips"]:  # plan qərarları "əl ilə" sayılmır
        if c["id"] not in was_manual and c.get("origin") in ("plan", "ai", "import", "auto", None):
            c["manual"] = False
    q["planApplied"] = {"at": __import__("time").time(), "file": plan_name, "look": look_name}
    return q


def cmd_plan(a: argparse.Namespace) -> None:
    """Təsdiqlənmiş storyboard planını (JSON məlumat) layihəyə tətbiq edir — hər video üçün kod yazılmır."""
    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    p = store.load(a.pid)
    q = apply_plan(a.pid, p, plan, Path(a.plan).name)
    cur = store.load(a.pid)
    saved = store.save(a.pid, q, cur["revision"])
    print(f"plan tətbiq olundu: {len(plan.get('graphics') or [])} qrafika, {len(plan.get('zooms') or [])} yaxınlaşma, "
          f"{len(plan.get('sfx') or [])} səs effekti, {len(plan.get('corrections') or [])} düzəliş, "
          f"rəng: {q['planApplied']['look'] or 'yox'}, musiqi: {'var' if plan.get('music') else 'yox'}; versiya {saved['revision']}")


def _start(q: dict[str, Any], cid: str) -> float:
    t = 0.0
    for c in node_tl("videoClips", q):
        if c["id"] == cid:
            return t
        t += c["srcOut"] - c["srcIn"]
    return t


def _analyses(pid: str, p: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    for m in p["media"]:
        f = analysis.analysis_path(store.project_dir(pid), m["id"])
        if f.is_file():
            out[m["id"]] = json.loads(f.read_text(encoding="utf-8"))
    return out


def _tc(t: float | None) -> str:
    return "—" if t is None else f"{int(t // 60)}:{t % 60:04.1f}"


def _latest_render(pid: str) -> Path:
    mp4s = sorted(out_dir(pid).glob(f"{pid}_r*.mp4"), key=lambda x: int(x.stem.rsplit("_r", 1)[1]))
    if not mp4s:
        raise UserError("Render tapılmadı.", f"Əvvəlcə `render {pid}`.")
    return mp4s[-1]


DEFAULT_SCENE_THEME = {"primary": "#2E3A4F", "primaryDeep": "#1C2433", "accent": "#F2C94C", "accentSoft": "#F4ECE4",
                       "text": "#FFFFFF", "onAccent": "#1C2433", "cardAlpha": 0.94}


def _project_theme(p: dict[str, Any]) -> dict[str, Any]:
    """Layihənin müştəri rəngi: brand.theme, yoxdursa ad ilə expert profili, yoxdursa neytral tema."""
    br = p.get("brand") or {}
    if br.get("theme"):
        return br["theme"]
    prof = expert_profile(br["name"]) if br.get("name") else None
    return (prof or {}).get("theme") or DEFAULT_SCENE_THEME


def _make_broll_media(pid: str, p: dict[str, Any], spec: dict[str, Any], dur: float) -> dict[str, Any]:
    """Claude-un hazırladığı B-roll (şablon səhnəsi) — render (keş) + layihəyə B-roll mediası kimi (təkrarsız)."""
    from montaj import sceneclip, server

    kind = spec["kind"]
    props = spec.get("props") or {}
    d = float(spec.get("dur", dur))
    clip = sceneclip.render(kind, props, d, spec.get("theme") or _project_theme(p), out_dir(pid) / "scenes", spec.get("style"))
    have = next((m for m in store.load(pid)["media"] if (m.get("source") or {}).get("file") == clip.name), None)
    if have:
        return have
    tmp = store.originals_dir(pid) / f".gen_{clip.name}.part"
    shutil.copyfile(clip, tmp)
    rec = server._register(pid, tmp, f"{kind}{clip.suffix}", {"type": "generated", "kind": kind, "file": clip.name})["media"]
    store.update_media_record(pid, rec["id"], {"role": "broll"})
    return {**rec, "role": "broll"}


def cmd_scenes(a: argparse.Namespace) -> None:
    """Claude-un B-roll üçün istifadə edə biləcəyi səhnələr (şablondan, props ilə)."""
    from montaj import sceneclip

    for k, v in sceneclip.catalog().items():
        print(f"{k:16s} [{v['group']}] props: {', '.join(v['props']) or '—'}" + (f"  | {v['doc'][:140]}" if v["doc"] else ""))


def cmd_make_broll(a: argparse.Namespace) -> None:
    """Səhnəni render edib layihəyə B-roll kimi əlavə edir (plan-da "name" və ya "media" ilə işlədilir)."""
    p = store.load(a.pid)
    m = _make_broll_media(a.pid, p, {"kind": a.kind, "props": json.loads(a.props or "{}"), "dur": a.dur}, a.dur)
    print(f"b-roll: {m['id']}  {m['name']}  {m['duration']:.1f} s (Claude-un hazırladığı səhnə: {a.kind})")
    if a.still:
        from montaj import sceneclip
        png = sceneclip.render(a.kind, json.loads(a.props or "{}"), a.dur, _project_theme(p), out_dir(a.pid) / "scenes", still=True)
        print(f"önizləmə: {png}")


def cmd_voice_clean(a: argparse.Namespace) -> None:
    """Arxa səsin təmizlənməsi (danışığı qoruyaraq). auto: arxa səs azdırsa tətbiq edilmir.
    Əvvəl/sonra dinləmə nümunəsi: out/<pid>/ses_evvel_sonra.m4a."""
    from montaj import voiceclean

    st = voiceclean.available()
    if a.mode != "off" and not (st["installed"] and st["model"]):
        raise UserError("Səs təmizləmə modeli quraşdırılmayıb.", "bash scripts/cloud-setup.sh (DeepFilterNet + model).")
    p = store.load(a.pid)
    used = {c["media"] for c in p["clips"] if c["track"] == "a1" and c.get("media")}
    out: dict[str, Any] = {}
    sample = None
    for m in p["media"]:
        if m["id"] not in used or m.get("role") == "broll" or not m.get("hasAudio"):
            continue
        if a.mode == "off":
            print(f"{m.get('name')}: təmizləmə söndürüldü")
            continue
        r = voiceclean.clean_media(store.project_dir(a.pid), m, a.mode, a.atten)
        if r["applied"]:
            out[m["id"]] = {"file": r["file"], "atten": r["atten"], "removedDb": r["removedDb"], "gainDb": r["gainDb"]}
            print(f"{m.get('name')}: arxa səs təmizləndi (çıxarılan {r['removedDb']} dB, danışıq səviyyəsi {r['gainDb']:+} dB bərpa olundu)")
            if sample is None:
                c = next(x for x in p["clips"] if x["track"] == "a1" and x.get("media") == m["id"])
                sample = voiceclean.ab_sample(store.project_dir(a.pid), m, r["file"], out_dir(a.pid) / "ses_evvel_sonra.m4a", c["srcIn"])
        else:
            print(f"{m.get('name')}: {r['why']}")
    cur = store.load(a.pid)
    cur["voiceClean"] = out
    saved = store.save(a.pid, cur, cur["revision"])
    if sample:
        print(f"dinləmə: {sample} (əvvəl → 0.8 s sükut → sonra)")
    print(f"versiya {saved['revision']}")


def cmd_add_broll(a: argparse.Namespace) -> None:
    """B-roll / araya kadr materialı (video, şəkil) əlavə edir: danışıq analizinə və kəsimə düşmür,
    yalnız plan-ın "broll" bölməsi ilə istifadə olunur. Orijinal dəyişmir."""
    from montaj import server

    added = []
    for link in a.link or []:
        tmp, name = drive.download(link, store.originals_dir(a.pid), lambda x: None)
        added.append(server._register(a.pid, tmp, name, {"type": "drive", "id": drive.parse_link(link)["id"]})["media"])
    for f in a.file or []:
        tmp = store.originals_dir(a.pid) / f".cli_{Path(f).name}.part"
        shutil.copyfile(f, tmp)
        added.append(server._register(a.pid, tmp, Path(f).name)["media"])
    for m in added:  # media qeydi serverin məlumatıdır — yalnız rol işarəsi əlavə olunur
        store.update_media_record(a.pid, m["id"], {"role": "broll"})
    for m in added:
        kind = "şəkil" if m.get("isImage") else f"video {m['duration']:.1f} s" + (", səsli" if m.get("hasAudio") else "")
        print(f"b-roll: {m['id']}  {m['name']}  {m.get('width')}x{m.get('height')}  {kind}")


def cmd_framefix(a: argparse.Namespace) -> None:
    """Hər video mənbə üçün kadraj düzəlişi (əyrilik + ortalama) storyboard qaralamasına yazılır;
    `kadraj.jpg`: orijinal / düzəldilmiş. Təsdiqə qədər layihə dəyişmir."""
    from montaj import framefix, render

    p = store.load(a.pid)
    sb = _load_draft(a.pid)
    W, H = int(p["width"]), int(p["height"])
    o = out_dir(a.pid)
    tiles = []
    font = render._font()
    for m in p["media"]:
        if not m.get("hasVideo") or m.get("isImage"):
            continue
        cards = [c for c in sb["cards"] if c["mediaId"] == m["id"] and c.get("include", True)]
        a0 = min((c["srcIn"] for c in cards), default=0.0)
        b0 = max((c["srcOut"] for c in cards), default=float(m["duration"]))
        src = store.project_dir(a.pid) / m["file"]
        r = framefix.suggest_fix(src, m, a0, b0, W, H)
        sb.setdefault("frames", {})[m["id"]] = r["frame"]
        print(f"{m.get('name')}: " + "; ".join(r["notes"]))
        t = (a0 + b0) / 2
        for label, fr in (("Orijinal", None), ("Düzəldilmiş", r["frame"])):
            clip = {"id": "x", "media": m["id"], "srcIn": t, "srcOut": t + 0.1, "frame": fr}
            if fr and fr.get("keys"):
                clip["frame"] = {**fr, "keys": [{**k, "t": t} for k in fr["keys"]]}
            vf = render.video_chain(clip, m, W, H, "30", False, 1) + ",scale=360:-2"
            if font:
                vf += f",drawbox=y=0:w=iw:h=32:color=black@0.65:t=fill,drawtext=fontfile={font}:text='{label}':x=8:y=7:fontsize=17:fontcolor=white"
            if fr is not None:  # köməkçi şəbəkə: üfüq və orta xətt
                vf += ",drawgrid=w=iw/2:h=ih/3:t=1:c=white@0.35"
            tile = o / f"kadraj_{len(tiles)}.png"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", str(src), "-frames:v", "1",
                            "-vf", vf, str(tile)], check=True)
            tiles.append(tile)
    _save_draft(a.pid, sb)
    if tiles:
        sheet = o / "kadraj.jpg"
        ins = sum((["-i", str(x)] for x in tiles), [])
        subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", f"hstack={len(tiles)}", "-q:v", "3", str(sheet)], check=True)
        for x in tiles:
            x.unlink()
        print(sheet)


def cmd_cut(a: argparse.Namespace) -> None:
    """Storyboard qaralamasında mənbə aralığını çıxarır (təkrar/alınmayan cümlə). Sərhədlər orijinal səsin
    ən sakit yerinə çəkilir; söz kəsilmir; şübhəli sərhəddə material saxlanılır. Təsdiqə qədər yalnız qaralamadır."""
    from montaj import media as mediautil
    from montaj import quality

    sb = _load_draft(a.pid)
    p = store.load(a.pid)
    media = {m["id"]: m for m in p["media"]}
    ans = _analyses(a.pid, p)
    for spec in a.ranges:
        mid, _, rng = spec.rpartition(":")
        x, _, y = rng.partition("-")
        x, y = float(x), float(y)
        cands = [c for c in sb["cards"] if (not mid or c["mediaId"] == mid) and c["srcIn"] < y and c["srcOut"] > x]
        if not cands:
            raise UserError(f"{spec}: bu aralıqda hissə yoxdur.", "Mənbə saniyələrini storyboard.md-dən götürün.")
        mid = cands[0]["mediaId"]
        rms = quality.frame_rms(mediautil.read_mono(store.project_dir(a.pid) / media[mid]["file"], quality.SR))
        ref = quality.speech_level(rms)
        words = (ans.get(mid) or {}).get("words") or []
        out_t, ok1 = quality.safe_boundary(rms, x, "out", words, ref)
        in_t, ok2 = quality.safe_boundary(rms, y, "in", words, ref)
        new_cards = []
        for c in sb["cards"]:
            if c not in cands:
                new_cards.append(c)
                continue
            if c["srcIn"] < out_t - 0.3:
                new_cards.append({**c, "srcOut": round(min(c["srcOut"], out_t), 3),
                                  "words": [w for w in c.get("words", []) if w["e"] <= out_t + 1e-6]})
            if c["srcOut"] > in_t + 0.3:
                new_cards.append({**c, "id": c["id"] + "b" if c["srcIn"] < out_t - 0.3 else c["id"], "srcIn": round(max(c["srcIn"], in_t), 3),
                                  "words": [w for w in c.get("words", []) if w["s"] >= in_t - 1e-6]})
        for c in new_cards:
            c["text"] = " ".join(w["w"] for w in c.get("words", [])).strip()
        sb["cards"] = new_cards
        flag = "" if ok1 and ok2 else "  ŞÜBHƏLİ: sakit yer tapılmadı, material saxlanıldı — dinləyib yoxlayın"
        print(f"çıxarıldı {mid} {x:.2f}–{y:.2f} → {out_t:.2f}–{in_t:.2f}{flag}")
    _save_draft(a.pid, sb)
    o = out_dir(a.pid)
    contact_sheet(a.pid, sb, o / "storyboard.jpg")
    (o / "storyboard.md").write_text(summary(a.pid, sb), encoding="utf-8")


def type_checks(pid: str, p: dict[str, Any], rep: dict[str, Any]) -> dict[str, Any]:
    """Növün maşın qaydaları (types.rules_for): uğurlu → checks, pozulan → problems (t=0)."""
    from montaj import ad

    q = node_tl("migrate", p)
    words, _tl, _tot = _timeline_words(pid, q)
    spoken = {int(n["value"]) for s_ in ad.scan_numbers(words) for n in s_["numbers"]}
    for w in words:
        spoken |= types._numbers(w["w"])
    checks, problems = list(rep.get("checks") or []), list(rep.get("problems") or [])
    for rule in types.rules_for(p.get("videoType")):
        ok, why = types.check(rule, q, node_tl("videoClips", q), spoken)
        (checks.append(f"növ qaydası: {why}") if ok else problems.append({"t": 0.0, "what": f"növ qaydası: {why}"}))
    return {"checks": checks, "problems": problems}


def cmd_verify(a: argparse.Namespace) -> None:
    """Yekun render yoxlaması: kəsim sərhədləri, səs/görüntü, kliklər, yekun səsin yenidən tanınması."""
    from montaj import quality

    p = store.load(a.pid)
    mp4 = Path(a.mp4) if a.mp4 else _latest_render(a.pid)
    rep = quality.verify(p, store.project_dir(a.pid), mp4, _analyses(a.pid, p), asr=not a.no_asr)
    rep.update(type_checks(a.pid, p, rep))
    (out_dir(a.pid) / f"{mp4.stem}_yoxlama.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    for c in rep["checks"]:
        print("✓", c)
    for x in rep["problems"]:
        print("!", _tc(x["t"]), x["what"])
    for u in rep["unverified"]:
        print("?", "yoxlanılmayıb:", u)
    print("problem yoxdur" if not rep["problems"] else f"{len(rep['problems'])} yer yoxlanmalıdır")


def cmd_words(a: argparse.Namespace) -> None:
    """Montajda qalan şübhəli tanınmış sözlər (vaxt ilə) — istifadəçiyə qısa siyahı."""
    from montaj import quality

    p = store.load(a.pid)
    ws = quality.suspicious_words(p, _analyses(a.pid, p), a.threshold)
    if not ws:
        print("şübhəli söz yoxdur")
    for w in ws:
        print(f"{_tc(w['t'])}  “{w['word']}”  ({w['context']})")


KEEP_SOURCES = ("generated", "synth", "music", "artifact-asset")  # kiçik/yenidən yaradıla bilməyən media paketə düşür


def _ad_words(pid: str, p: dict[str, Any]) -> list[dict[str, Any]]:
    """Analiz sözləri (bütün danışıq mediaları, mənbə vaxtı ilə), layihə və müştəri lüğəti düzəlişləri tətbiq olunmuş."""
    corr = list(((p.get("subtitles") or {}).get("corrections") or []))
    br = p.get("brand") or {}
    prof = expert_profile(br["name"]) if br.get("name") else None
    corr += ((prof or {}).get("glossary") or {}).get("fixes") or []
    out = []
    for mid, an in _analyses(pid, p).items():
        for w in an.get("words") or []:
            w = dict(w, media=mid)
            for c in corr:
                if transcribe_norm(w["w"]) == transcribe_norm(c["from"]):
                    w["w"] = c["to"]
            out.append(w)
    return out


def cmd_ad_scan(a: argparse.Namespace) -> None:
    """Reklam faktları danışıqdan: təklif növü, qiymət, endirim, tarix, yer sayı, çağırış, faydalar (vaxtla)."""
    from montaj import ad

    p = store.load(a.pid)
    r = ad.scan(_ad_words(a.pid, p))
    print(f"təklif növü: {r['offer'] or 'aydın deyil'}")
    for f in r["facts"]:
        extra = f" | açar söz: {f['keyword']}" if f.get("keyword") else ""
        print(f"{f['t']:6.2f} s  {f['kind']:8s} {f['value'][:70]}{extra}")
    missing = [k for k in ("price", "cta") if not any(f["kind"] == k for f in r["facts"])]
    if missing:
        print("danışıqda tapılmadı (uydurulmayacaq): " + ", ".join({"price": "qiymət", "cta": "çağırış"}[k] for k in missing))


def cmd_ad_plan(a: argparse.Namespace) -> None:
    """Reklam üçün 3 storyboard variantı (A təmiz+vurğu, B qrafik izah, C dinamik) — ardıcıllıq qorunur,
    mətnlər danışıqdan. Faylları yoxla/redaktə et, sonra `variants`."""
    from montaj import ad

    p = store.load(a.pid)
    sb = _load_draft(a.pid)
    tm = ad.timeline_map(sb["cards"])
    total = tm[-1][3] + tm[-1][2] - tm[-1][1] if tm else 0
    res = ad.plans(ad.scan(_ad_words(a.pid, p)), tm, total)
    # kartları üzün altına yerləşdir (mənbə kadrında üz → kadraj pəncərəsi ilə yekun kadra)
    from montaj import quality
    from montaj.graphics import DEFAULT_XY
    media = {m["id"]: m for m in p["media"]}
    placed: dict[tuple[str, float], tuple[float, str]] = {}
    for plan in res.values():
        for g in plan.get("graphics") or []:
            if g["type"] not in ("offer", "cta") or "y" in g:
                continue
            key = (g["type"], g["start"])
            if key not in placed:
                src = next(((mid, a0 + (g["start"] + 0.5 - t0)) for mid, a0, b0, t0 in tm if t0 <= g["start"] + 0.5 < t0 + (b0 - a0)), None)
                m = media.get(src[0]) if src else None
                placed[key] = quality.place_below_face(store.project_dir(a.pid), m, (sb.get("frames") or {}).get(src[0]), src[1],
                                                       g["type"], DEFAULT_XY[g["type"]][1]) if m and m.get("hasVideo") else (DEFAULT_XY[g["type"]][1], 1.0, "")
            g["y"] = placed[key][0]
            if placed[key][1] < 0.999:
                g["size"] = round({"offer": 0.03, "cta": 0.032}[g["type"]] * placed[key][1], 4)
    o = out_dir(a.pid)
    for k, plan in res.items():
        f = o / f"ad_plan_{k}.json"
        f.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{k}: {plan['title']} ({plan['approach']}) — {len(plan.get('graphics') or [])} qrafika, "
              f"{len(plan.get('broll') or [])} B-roll, {len(plan.get('zooms') or [])} zoom → {f}")
    for (kind, t), (y, sc, why) in placed.items():
        print(f"yer: {kind} {t:.1f} s → y={y} ({why})")
    print("YOXLA (mətnlər danışıqdan avtomatik götürülüb):")
    for line in res["A"]["_review"]:
        print(" -", line)


def cmd_mg_scan(a: argparse.Namespace) -> None:
    """Motion graphics üçün: danışıqdakı rəqəmlər (vaxtla) və uyğun qrafik səhnə təklifi (mg_*)."""
    from montaj import ad

    p = store.load(a.pid)
    found = ad.scan_numbers(_ad_words(a.pid, p))
    for f in found:
        nums = ", ".join(f"{n['value']}{(' ' + n['unit']) if n['unit'] and n['unit'] != '%' else n['unit']}" for n in f["numbers"])
        print(f"{f['t']:6.2f} s  {nums:28s} → {f['suggest']}  | “{f['text'][:80]}”")
    if not found:
        print("danışıqda rəqəm yoxdur — rəqəmsiz səhnələr işlət (mg_steps, mg_code, checklist, timeline); rəqəm uydurma")


def cmd_tale_plan(a: argparse.Namespace) -> None:
    """Nağıl: danışıqdakı obraz və məkanlardan cizgi səhnələri (tale_plan.json). Səhnələr danışığın ardıcıllığı ilə,
    mətn danışıqdan, obrazlar video boyu eyni. Yoxla/redaktə et, sonra `variants`."""
    from montaj import ad, tale

    p = store.load(a.pid)
    sb = _load_draft(a.pid)
    tm = ad.timeline_map(sb["cards"])
    total = tm[-1][3] + tm[-1][2] - tm[-1][1] if tm else 0
    res = tale.plan(_ad_words(a.pid, p), lambda t: ad.to_timeline(tm, t), total, a.mode)
    f = out_dir(a.pid) / "tale_plan.json"
    f.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(res['broll'])} nağıl səhnəsi, obrazlar: {', '.join(res['_characters']) or '—'} → {f}")
    for b in res["broll"]:
        pr = b["make"]["props"]
        print(f"  {b['at']:6.2f} s  [{pr['bg']}] {', '.join(c['kind'] + ('/' + c['action'] if c.get('action') else '') for c in pr['chars'])}"
              f"  “{pr['title'][:60]}”")
    for r in res["_review"]:
        print("YOXLA:", r)


def _timeline_words(pid: str, q: dict[str, Any]) -> tuple[list[dict[str, Any]], Any, float]:
    """Əsas montajın (tətbiq olunmuş) zaman xətti: mənbə sözləri + mənbə→zaman xətti çevirməsi + ümumi müddət."""
    from montaj import ad

    tm, acc = [], 0.0
    for c in node_tl("videoClips", q):
        d = c["srcOut"] - c["srcIn"]
        if not c.get("broll"):
            tm.append((c["media"], float(c["srcIn"]), float(c["srcOut"]), acc))
        acc += d
    words = [w for w in _ad_words(pid, q) if any(m == w["media"] and a0 - 0.05 <= w["s"] <= b0 for m, a0, b0, _ in tm)]
    words.sort(key=lambda w: ad.to_timeline(tm, w["s"], w["media"]) or 0)
    return words, (lambda t, mid=None: ad.to_timeline(tm, t, mid)), acc


def cmd_carousel_plan(a: argparse.Namespace) -> None:
    """Video karusel planı (carousel.json): örtük + fikir slaydları + çağırış; əsas montajdan kəsilir. Yoxla/redaktə et."""
    from montaj import ad, carousel

    q = store.load(a.pid)
    words, tl, total = _timeline_words(a.pid, q)
    sc = ad.scan(words)
    cta = next((dict(f, tl=tl(f["t"])) for f in reversed(sc["facts"]) if f["kind"] == "cta"), None)
    res = carousel.plan(words, tl, total, cta)
    f = out_dir(a.pid) / "carousel.json"
    f.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for i, s in enumerate(res["slides"], 1):
        tag = " [örtük]" if s.get("cover") else " [çağırış]" if s.get("cta") else ""
        print(f"{i}. {s['from']:6.2f}–{s['to']:6.2f} s ({s['to'] - s['from']:.1f} s){tag}: “{s['title']}”")
    print(f"→ {f}")
    for r in res.get("_review") or []:
        print("YOXLA:", r)


def cmd_carousel(a: argparse.Namespace) -> None:
    """Video karusel: hər slayd ayrıca 1080x1350 MP4 (≤60 s), eyni dizayn (başlıq, sayğac, altyazı); örtük PNG və ümumi şəkil."""
    from montaj import carousel, quality as _q
    from montaj.render import render as _render

    q = node_tl("migrate", store.load(a.pid))
    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    W, H = 1080, 1350
    o = out_dir(a.pid) / "carousel"
    o.mkdir(parents=True, exist_ok=True)
    media = {m["id"]: m for m in q["media"]}
    slides = plan["slides"]
    n = len(slides)
    outs = []
    for i, s in enumerate(slides, 1):
        if s["to"] - s["from"] > carousel.MAX_SLIDE + 2:
            raise UserError(f"Slayd {i} 60 saniyədən uzundur.", "carousel.json-da həmin slaydı bölün.")
        sp = carousel.slice_project(q, float(s["from"]), float(s["to"]), node_tl)
        sp["width"], sp["height"] = W, H
        sp["clips"] = [c for c in sp["clips"] if c["track"] != "t1"]  # əsas montajın kartları 9:16 üçündür — slayd öz başlığını alır
        for c in sp["clips"]:
            m = media.get(c.get("media"))
            if c["track"] in ("v1", "v2") and m and m.get("hasVideo") and c.get("mode") not in ("pip", "sticker"):
                fr = _cover_frame(m, W, H)
                if fr:
                    old = ((c.get("frame") or {}).get("keys") or [{}])[0]
                    fr["keys"] = [{"t": c["srcIn"], "cx": old.get("cx", 0.5), "cy": 0.42}]
                    fr["rotate"] = (c.get("frame") or {}).get("rotate", 0)
                c["frame"] = fr
        if sp.get("subtitles"):
            sp["subtitles"]["style"] = {**(sp["subtitles"].get("style") or {}), "y": 0.84}
        dur = s["to"] - s["from"]
        gfx = [{"type": "badge", "text": f"{i}/{n}", "x": 0.88, "y": 0.055, "start": 0, "dur": dur, "anim": {"in": "none", "out": "none"}}]
        if s.get("cover"):
            gfx.append({"type": "title", "text": s["title"], "x": 0.5, "y": 0.16, "start": 0, "dur": dur, "size": 0.04, "anim": {"in": "pop", "out": "none"}})
            gfx.append({"type": "section", "text": "Sürüşdürün →", "x": 0.5, "y": 0.93, "start": 0.8, "dur": max(0.5, dur - 0.8), "anim": {"in": "fade", "out": "none"}})
        else:
            gfx.append({"type": "section", "text": s["title"], "x": 0.5, "y": 0.12, "start": 0, "dur": dur, "anim": {"in": "slide-up", "out": "none"}})
        if s.get("cta"):
            gfx.append({"type": "cta", "text": s["cta"].get("text") or "", "keyword": s["cta"].get("keyword") or "", "x": 0.5, "y": 0.6,
                        "start": max(0.0, dur - 3.5), "dur": min(3.5, dur), "anim": {"in": "pop", "out": "none"}})
        for g in gfx:
            sp = node_tl("addGraphic", sp, {**g, "origin": "plan"})
        f = o / f"slide_{i:02d}.mp4"
        _render(sp, store.project_dir(a.pid), f, lambda x: None)
        outs.append(f)
        print(f"slayd {i}/{n}: {f.name} ({dur:.1f} s)")
    cover = o / "ortuk.jpg"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "1.2", "-i", str(outs[0]), "-frames:v", "1", "-q:v", "2", str(cover)], check=True)
    ins = sum((["-ss", "1.2", "-i", str(x)] for x in outs), [])
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex",
                    "".join(f"[{k}:v]scale=270:-2[s{k}];" for k in range(len(outs))) + "".join(f"[s{k}]" for k in range(len(outs))) +
                    f"hstack={len(outs)}" if len(outs) > 1 else "[0:v]scale=270:-2", "-frames:v", "1", "-q:v", "3", str(o / "karusel.jpg")], check=True)
    print(f"örtük: {cover}")
    print(f"ümumi şəkil: {o / 'karusel.jpg'}")
    print("Instagram-da: yeni paylaşım → bir neçə seç → slaydları sıra ilə əlavə et")


def _speech_media(p: dict[str, Any]) -> dict[str, Any]:
    from montaj import reframe

    m = reframe.primary_video([x for x in p["media"] if x.get("hasAudio") and not (x.get("source") or {}).get("type") in ("generated", "music", "sfx")])
    if not m:
        raise UserError("Danışıq videosu yoxdur.", "Səsli video faylı əlavə edin.")
    return m


def cmd_qa_plan(a: argparse.Namespace) -> None:
    """M10: suallar + cavablar + reaksiyalar → qa_A/B/C.json (storyboard.cards) — `variants` / `choose` ilə."""
    from montaj import event, qa, quality, speakers

    p = store.load(a.pid)
    m = _speech_media(p)
    src = store.project_dir(a.pid) / m["file"]
    words = sorted([w for w in _ad_words(a.pid, p) if w["media"] == m["id"]], key=lambda w: w["s"])
    if not words:
        raise UserError("Transkript yoxdur.", "Əvvəl `storyboard <pid>` işlədin.")
    try:
        _load_draft(a.pid)
    except UserError:
        raise UserError("Storyboard qaralaması yoxdur.", "Əvvəl `storyboard <pid>` işlədin.") from None
    rms = quality.frame_rms(event._decode(src, quality.SR))
    motion = None
    if not a.no_faces and m.get("hasVideo"):
        ser = speakers.mouth_tracks(src, 0, float(m["duration"]))
        mt = speakers.main_track(ser)
        if mt is not None:
            motion = [speakers.motion_in(ser, mt, s_["s"], s_["e"]) for s_ in quality.sentences(words, gap=0.5)]
    same = bool(m.get("width") and p.get("width") and abs(m["width"] / m["height"] - p["width"] / p["height"]) < 0.02)
    r = qa.plans(words, m["id"], rms, motion, same_aspect=same)
    print(f"{r['pairs']} sual-cavab, {len(r['reactions'])} reaksiya anı (gülüş/səsli pauza — saxlanılır)")
    for k, plan in r["plans"].items():
        f = out_dir(a.pid) / f"qa_{k}.json"
        plan["_review"] = r["review"] + plan.get("_review", [])
        f.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
        dur = sum(c["srcOut"] - c["srcIn"] for c in plan["storyboard"]["cards"])
        print(f"{k}: {plan['title']} ({plan['approach']}) — {dur:.1f} s, {len(plan['graphics'])} sual yazısı, "
              f"{len(plan['zooms'])} yaxınlaşma → {f}")
    for x in r["review"]:
        print("YOXLA:", x)
    if not same:
        print("QEYD: kadr ölçüsü fərqlidir — reaksiya yaxınlaşması (punch-in) qurulmadı")
    print("növbəti: sual mətnlərində ASR səhvini düzəlt → variants <pid> qa_A.json qa_B.json qa_C.json → choose")


def _apply_multicam(pid: str, q: dict[str, Any], spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Virtual multikamera (multicam.py): cümlə sərhədlərində plan ölçüsü dəyişir; nəticə + hesabat."""
    from montaj import multicam, quality, reframe

    st = multicam.STYLES.get(spec.get("style", "calm"), multicam.STYLES["calm"])
    W = int(q["width"])
    words, tl, total = _timeline_words(pid, q)
    sents = []
    for x in quality.sentences(words, gap=0.5):
        a, b = tl(x["s"], x["words"][0].get("media")), tl(x["e"], x["words"][-1].get("media"))
        if a is not None and b is not None:
            sents.append({"s": a, "e": b, "text": x["text"]})
    segs = multicam.segments(sorted(sents, key=lambda z: z["s"]), total, float(spec.get("min_len") or st["min_len"]))
    media = {m["id"]: m for m in q["media"]}
    main = [c for c in node_tl("videoClips", q) if not c.get("broll") and media.get(c["media"], {}).get("hasVideo")
            and not media[c["media"]].get("isImage") and not c.get("split")]
    if not main:
        return q, {"tiers": {}, "plans": [], "warn": "video klip yoxdur"}
    heads = {c["media"]: multicam.headroom(media[c["media"]], c.get("frame"), W) for c in main}
    ts = multicam.tiers(min(heads.values()))
    names = multicam.assign(segs, ts)
    for g in segs[1:]:  # sərhədlərdə klipi böl
        c = next((x for x in node_tl("videoClips", q) if not x.get("broll")
                  and _start(q, x["id"]) + 0.2 < g["a"] < _start(q, x["id"]) + x["srcOut"] - x["srcIn"] - 0.2), None)
        if c:
            q = node_tl("split", q, c["id"], g["a"])
    for c in node_tl("videoClips", q):
        m = media.get(c["media"]) or {}
        if c.get("broll") or not m.get("hasVideo") or m.get("isImage") or c.get("split"):
            continue
        t0 = _start(q, c["id"]) + (c["srcOut"] - c["srcIn"]) / 2
        gi = next((i for i, g in enumerate(segs) if g["a"] <= t0 < g["b"]), len(segs) - 1)
        z = ts[names[gi]]
        cur = dict(c.get("frame") or {})
        if not (cur.get("mode") in ("auto", "manual") and cur.get("keys")):
            cur = {"aspect": q.get("aspect") or "source", "mode": "auto", "s": 1.0, "baseW": 1.0, "baseH": 1.0,
                   "keys": [{"t": c["srcIn"], "cx": 0.5, "cy": 0.5}], "rotate": cur.get("rotate", 0), "warnings": []}
        base = cur.get("mcBase") or {"s": float(cur.get("s") or 1), "keys": cur["keys"]}
        fr = {**cur, "mcBase": base, "s": round(base["s"] / z, 4), "keys": [dict(k) for k in base["keys"]]}
        fr.pop("push", None)
        if z > 1.001:  # yaxın planda üz kəsim pəncərəsinin yuxarı ~38%-də
            src = store.project_dir(pid) / m["file"]
            mid = (c["srcIn"] + c["srcOut"]) / 2
            det = reframe.detect_faces(src, mid, mid + 0.1, step=1.0)
            f = max((x for d in det for x in d["faces"]), key=lambda x: x["w"], default=None)
            if f:
                chf = float(fr.get("baseH") or 1) * fr["s"]
                fr["keys"] = [{"t": c["srcIn"], "cx": round(f["x"] + f["w"] / 2, 4),
                               "cy": round(min(1 - chf / 2, max(chf / 2, f["y"] + f["h"] / 2 + 0.12 * chf)), 4)}]
        if st["push"] and segs[gi]["emph"] and names[gi] != "close":  # sakit üslub: vurğuda yavaş yaxınlaşma
            room = ts.get("close", 1.0) / z
            if room > 1.03:
                fr["push"] = round(min(1.1, room), 3)
        q = node_tl("setFrame", q, c["id"], fr, {"manual": False})
    head = min(heads.values())
    warn = ""
    if head < 1.0:
        warn = f"kəsim artıq {1 / head:.2f}x böyüdülür (məs. 16:9 → 9:16) — plan ölçüsü dəyişmədi; 4K çəkiliş lazımdır"
    elif len(ts) < 3:
        warn = f"keyfiyyət ehtiyatı {head:.2f}x — yaxın plan yalnız {ts.get('close', 1):.2f}x, fərq zəif olacaq; növbəti çəkilişi 4K çəkin"
    return q, {"tiers": ts, "headroom": round(head, 2), "plans": [(g["a"], g["b"], n) for g, n in zip(segs, names)], "warn": warn}


def cmd_multicam(a: argparse.Namespace) -> None:
    """Virtual multikamera tətbiq olunmuş montaja: ümumi/orta/yaxın plan cümlə sərhədlərində, vurğuda yaxınlaşma."""
    q = node_tl("migrate", store.load(a.pid))
    q, rep = _apply_multicam(a.pid, q, {"style": a.style})
    print(f"keyfiyyət ehtiyatı {rep.get('headroom')}x → planlar: " + ", ".join(f"{k} {v}x" for k, v in rep["tiers"].items()))
    for x, y, n in rep["plans"]:
        print(f"  {x:6.2f}–{y:6.2f} s  {n}")
    if rep["warn"]:
        print("XƏBƏRDARLIQ:", rep["warn"])
    cur = store.load(a.pid)
    saved = store.save(a.pid, q, cur["revision"])
    print(f"saxlandı: versiya {saved['revision']} — render <pid>")


def _bg_targets(p: dict[str, Any], only: str | None = None) -> list[dict[str, Any]]:
    used = {c["media"] for c in p["clips"] if c["track"] == "v1" and not c.get("broll")}
    out = [m for m in p["media"] if m["id"] in used and m.get("hasVideo") and not m.get("isImage")
           and not (m.get("source") or {}).get("type") in ("generated", "music", "sfx")]
    if only:
        out = [m for m in out if m["id"] == only or m.get("name") == only]
    return out


def _bg_spec(a: argparse.Namespace, p: dict[str, Any]) -> list[dict[str, Any]]:
    from montaj import background

    raw = [json.loads(x) for x in (a.spec or [])]
    if not raw and a.mode:
        raw = [{"mode": a.mode, "color": a.color, "color2": a.color2, "direction": a.direction, "file": a.file, "kind": a.kind,
                "props": json.loads(a.props) if a.props else None, "strength": a.strength, "dim": a.dim,
                "keepBelow": a.keep_below, "feather": a.feather, "smooth": a.smooth, "model": "fast" if a.fast else None}]
    th = _project_theme(p)
    out = []
    for r in raw:
        r = {k: v for k, v in r.items() if v is not None}
        if r.get("mode") == "color" and not r.get("color"):  # rəng verilməyibsə — müştərinin brend rəng ailəsi
            r["color"] = th.get("primary") or "#333333"
            r.setdefault("color2", th.get("primaryDeep") or r["color"])
        try:
            out.append(background.normalize(r))
        except ValueError as e:
            raise UserError(str(e), "Nümunə: --mode color --color '#C9577D' --color2 '#5A1E3C' və ya --mode blur") from None
    return out


def _bg_scene_file(pid: str, p: dict[str, Any], spec: dict[str, Any]) -> Path | None:
    if spec["mode"] != "scene":
        return None
    from montaj import sceneclip

    if not spec.get("kind"):
        raise UserError("Səhnə fonu üçün kind lazımdır.", "Kataloq: `python -m montaj.session scenes`.")
    return sceneclip.render(spec["kind"], spec.get("props") or {}, 6.0, _project_theme(p), store.derived_dir(pid) / "bg_scenes")


def cmd_bg(a: argparse.Namespace) -> None:
    """Arxa fon: --preview — bir neçə variant yan-yana (arxafon.jpg, layihə dəyişmir); əks halda tətbiq (törəmə video)."""
    from PIL import Image, ImageDraw, ImageFont

    from montaj import background

    p = store.load(a.pid)
    if a.off:
        p["background"] = {}
        saved = store.save(a.pid, p, p["revision"])
        print(f"arxa fon orijinala qaytarıldı; versiya {saved['revision']}")
        return
    targets = _bg_targets(p, a.media)
    if not targets:
        raise UserError("Montajda danışıq videosu yoxdur.", "Əvvəl storyboard-u tətbiq edin (choose/apply).")
    specs = _bg_spec(a, p)
    if not specs:
        raise UserError("Fon seçilməyib.", "--mode blur|color|image|video|scene və ya --spec '{...}' verin.")
    root = store.project_dir(a.pid)
    if a.preview:
        m = targets[0]
        src = root / m["file"]
        cs = [c for c in p["clips"] if c["track"] == "v1" and c.get("media") == m["id"]]
        a0, b0 = min(c["srcIn"] for c in cs), max(c["srcOut"] for c in cs)
        ts = [a0 + (b0 - a0) * k for k in (0.2, 0.5, 0.8)]
        rows = [("Orijinal", None)] + [(_bg_label(sp), sp) for sp in specs]
        tiles = [[background.still(src, t, sp, 300, _bg_scene_file(a.pid, p, sp) if sp else None) for t in ts] for _, sp in rows]
        th, tw = tiles[0][0].shape[:2]
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        sheet = Image.new("RGB", (len(ts) * (tw + 6) + 6, len(rows) * (th + 36) + 6), (20, 22, 26))
        d = ImageDraw.Draw(sheet)
        for r, (label, _) in enumerate(rows):
            y = 6 + r * (th + 36)
            d.text((8, y), f"{chr(65 + r - 1) + ': ' if r else ''}{label}", font=font, fill=(235, 236, 240))
            for k, im in enumerate(tiles[r]):
                sheet.paste(Image.fromarray(im), (6 + k * (tw + 6), y + 28))
        f = out_dir(a.pid) / "arxafon.jpg"
        sheet.save(f, quality=88)
        print(f)
        return
    spec = specs[0]
    p.setdefault("background", {})
    for m in targets:
        src = root / m["file"]
        key = background.spec_key(spec, src)
        rel = f"media/derived/bg_{m['id']}_{key}.mp4"
        dst = root / rel
        info = {"flicker": (p["background"].get(m["id"]) or {}).get("flicker")}
        if not dst.is_file():
            print(f"{m['name']}: emal olunur ({_bg_label(spec)})…")
            info = background.process(src, dst, spec, _bg_scene_file(a.pid, p, spec))
        p["background"][m["id"]] = {"file": rel, "spec": spec, "flicker": info.get("flicker")}
        fl = info.get("flicker")
        if fl is not None:
            verdict = "sabit" if fl < 0.03 else "normal" if fl < 0.06 else "kənar titrəyir — smooth-u artır və ya blur seç"
            print(f"{m['name']}: hazır — kənar titrəməsi {fl} ({verdict})")
    cur = store.load(a.pid)
    cur["background"] = p["background"]
    saved = store.save(a.pid, cur, cur["revision"])
    print(f"saxlandı: versiya {saved['revision']} — render <pid> (orijinal dəyişmir; `bg <pid> --off` geri qaytarır)")


def _bg_label(sp: dict[str, Any]) -> str:
    mode = sp["mode"]
    txt = {"blur": f"bulanıq fon ({sp.get('strength')})", "color": f"rəng {sp.get('color')}" + (f"→{sp['color2']}" if sp.get("color2") and sp.get("color2") != sp.get("color") else ""),
           "image": f"şəkil {Path(sp.get('file', '')).name}", "video": f"video {Path(sp.get('file', '')).name}",
           "scene": f"səhnə {sp.get('kind')}"}[mode]
    if sp.get("dim"):
        txt += f", qaraltma {sp['dim']}"
    if sp.get("keepBelow") is not None:
        txt += f", masa qalır (y≥{sp['keepBelow']})"
    return txt


def cmd_duo(a: argparse.Namespace) -> None:
    """Növ 11 (iki nəfər bir kadrda): `switch` — kadraj danışana keçir; `split` — bölünmüş ekran. Tətbiq olunmuş montaja."""
    from montaj import duo, quality, speakers

    q = node_tl("migrate", store.load(a.pid))
    m = _speech_media(q)
    src = store.project_dir(a.pid) / m["file"]
    vids = [c for c in node_tl("videoClips", q) if c["media"] == m["id"] and not c.get("broll")]
    if not vids:
        raise UserError("Montajda bu videonun klipi yoxdur.", "Əvvəl storyboard-u tətbiq edin (`choose` və ya `apply`).")
    a0, b0 = min(c["srcIn"] for c in vids), max(c["srcOut"] for c in vids)
    ser = speakers.mouth_tracks(src, a0, b0)
    if len(ser["tracks"]) < 2:
        raise UserError(f"Kadrda iki nəfər tapılmadı ({len(ser['tracks'])}).",
                        "Bu rejim bir kadrda iki danışan üçündür; iki ayrı kamera sinxronu hələ yoxdur.")
    tr = sorted(ser["tracks"], key=lambda t: -t["n"])[:2]
    idx = [ser["tracks"].index(t) for t in sorted(tr, key=lambda t: t["cx"])]
    W, H = int(q["width"]), int(q["height"])
    if a.mode == "split":
        spec = duo.split_spec([ser["tracks"][i] for i in idx], float(m["width"]), float(m["height"]), W, H)
        for c in q["clips"]:
            if c["track"] == "v1" and c.get("media") == m["id"] and not c.get("broll"):
                c["split"] = spec
        if q.get("subtitles"):
            q["subtitles"]["style"] = {**(q["subtitles"].get("style") or {}), "y": 0.5}
        print("bölünmüş ekran: yuxarıda soldakı, aşağıda sağdakı şəxs; altyazı ortada (y 0.5)")
    else:
        words = sorted([w for w in _ad_words(a.pid, q) if w["media"] == m["id"]], key=lambda w: w["s"])
        ss = duo.chunks(words, [x for x in quality.sentences(words, gap=0.5) if a0 - 0.05 <= x["s"] <= b0])
        who = speakers.turns({**ser, "tracks": [ser["tracks"][i] for i in idx]}, ss)
        rs = duo.runs(ss, who, a.min_len)
        cuts = duo.cut_points(rs)
        for t in cuts:  # mənbə vaxtı → klip bölünməsi
            c = next((x for x in node_tl("videoClips", q) if x["media"] == m["id"] and x["srcIn"] + 0.2 < t < x["srcOut"] - 0.2), None)
            if c:
                q = node_tl("split", q, c["id"], _start(q, c["id"]) + (t - c["srcIn"]))
        for c in node_tl("videoClips", q):
            if c["media"] != m["id"] or c.get("broll"):
                continue
            mid = (c["srcIn"] + c["srcOut"]) / 2
            r = next((x for x in rs if x["s"] - 0.3 <= mid <= x["e"] + 0.3), None)
            if not r or r["speaker"] is None:
                continue
            t_ = ser["tracks"][idx[r["speaker"]]]
            fr = dict(c.get("frame") or {})
            if not fr.get("keys"):
                continue
            fr["keys"] = [{"t": c["srcIn"], "cx": round(t_["cx"], 4), "cy": round(min(0.6, max(0.35, t_["cy"])), 4)}]
            fr.pop("planZoom", None)
            q = node_tl("setFrame", q, c["id"], fr, {"manual": False})
        share = {}
        for r in rs:
            share[r["speaker"]] = share.get(r["speaker"], 0) + r["e"] - r["s"]
        print(f"{len(rs)} növbə, {len(cuts)} kəsim; danışma payı: " +
              ", ".join(f"{'sol' if k == 0 else 'sağ' if k == 1 else '?'} {v:.0f} s" for k, v in share.items()))
    for c in q["clips"]:  # avtomatik qərardır — sonrakı storyboard tətbiqi bu klipləri "əl ilə" saymasın
        if c.get("media") == m["id"] and (c["track"] == "v1" or c.get("linkedTo")):
            c["manual"] = False
    cur = store.load(a.pid)
    saved = store.save(a.pid, q, cur["revision"])
    print(f"saxlandı: versiya {saved['revision']} — render <pid>")


def cmd_event_scan(a: argparse.Namespace) -> None:
    """M09: bütün görüntülərin kadrları (xronoloji) və keyfiyyəti → shots.json + kadrlar.jpg (zəif kadr qırmızı)."""
    from PIL import Image, ImageDraw, ImageFont

    from montaj import event

    p = store.load(a.pid)
    root = store.project_dir(a.pid)
    shots = event.scan_shots(p["media"], root, faces=not a.no_faces)
    if not shots:
        raise UserError("Görüntü materialı yoxdur.", "Tədbir/proses videolarını və şəkillərini layihəyə əlavə edin.")
    o = out_dir(a.pid)
    (o / "shots.json").write_text(json.dumps(shots, ensure_ascii=False), encoding="utf-8")
    media = {m["id"]: m for m in p["media"]}
    tw, th, cols = 240, 135, 5
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    rows = (len(shots) + cols - 1) // cols
    img = Image.new("RGB", (cols * (tw + 8) + 8, rows * (th + 44) + 8), (20, 22, 26))
    d = ImageDraw.Draw(img)
    tmp = o / "_shot.jpg"
    for i, sh in enumerate(shots):
        x, y = 8 + (i % cols) * (tw + 8), 8 + (i // cols) * (th + 44)
        t = 0 if sh.get("image") else (sh["s"] + sh["e"]) / 2
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(root / media[sh["media"]]["file"]), "-frames:v", "1",
                        "-vf", f"scale={tw}:{th}:force_original_aspect_ratio=decrease,pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2", str(tmp)],
                       capture_output=True)
        if tmp.is_file():
            img.paste(Image.open(tmp).convert("RGB"), (x, y))
        if sh["weak"]:
            d.rectangle([x, y, x + tw, y + th], outline=(255, 90, 90), width=4)
        d.text((x, y + th + 4), f"#{i + 1} {sh['name'][:14]} {sh['s']:.1f}–{sh['e']:.1f}s", font=font, fill=(220, 222, 228))
        d.text((x, y + th + 22), f"bal {sh['score']:.2f}" + (" · ümumi plan" if sh["wide"] else "") +
               (" · " + ", ".join(sh["weak"]) if sh["weak"] else ""), font=font, fill=(255, 140, 140) if sh["weak"] else (154, 161, 173))
    tmp.unlink(missing_ok=True)
    img.save(o / "kadrlar.jpg", quality=85)
    weak = sum(1 for x in shots if x["weak"])
    print(f"{len(shots)} kadr ({weak} zəif), {len({x['media'] for x in shots})} fayl → {o / 'shots.json'}")
    print(o / "kadrlar.jpg")


def cmd_event_plan(a: argparse.Namespace) -> None:
    """M09: musiqi vuruşlarına düzülmüş 3 variant planı (event_A/B/C.json) — `variants` və `choose` ilə işləyir."""
    from montaj import event

    f = out_dir(a.pid) / "shots.json"
    if not f.is_file():
        raise UserError("Kadr analizi yoxdur.", "Əvvəl `event-scan <pid>` işlədin.")
    shots = json.loads(f.read_text(encoding="utf-8"))
    music = Path(a.music)
    if not music.is_file():
        raise UserError(f"Musiqi faylı tapılmadı: {music}", "Freesound-dan (CC0) musiqi yükləyin və yolunu verin.")
    bt = event.beats(music)
    print(f"musiqi: temp {bt['tempo']} BPM, {len(bt['beats'])} vuruş, {bt['duration']:.1f} s")
    try:
        _load_draft(a.pid)
    except UserError:
        raise UserError("Storyboard qaralaması yoxdur.", "Əvvəl `storyboard <pid>` işlədin (kadraj və analiz üçün).") from None
    for k in a.variants:
        r = event.assemble(shots, bt, k, a.target if a.target and k != "C" else None)
        plan = {"title": event.VARIANTS[k]["title"], "approach": "M09",
                "storyboard": {"cards": r["cards"]}, "captions": {"enabled": False}, "dropStoryboardText": True,
                "music": {"file": str(music.resolve()), "from": r["music_from"], "volume": a.volume, "duck": False,
                          "fadeIn": 0.0, "fadeOut": 2.0},
                "liveSound": {"volume": 0.0, "keep": {}}, "look": None, "_review": r["review"]}
        out = out_dir(a.pid) / f"event_{k}.json"
        out.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
        roles = " · ".join(f"{c['role'][0]}:{c['srcOut'] - c['srcIn']:.1f}" for c in r["cards"])
        print(f"{k}: {plan['title']} — {len(r['cards'])} kadr, {r['dur']:.1f} s ({roles}) → {out}")
        for x in r["review"]:
            print("   YOXLA:", x)
    print("növbəti: variants <pid> event_A.json event_B.json event_C.json → seçim → choose (rəng: look əlavə et)")


def cmd_highlights(a: argparse.Namespace) -> None:
    """Uzun videodan (seminar, çıxış) müstəqil qısa Reels hissələri: bal, səbəb, hazır `extract` əmri.
    Təklifdir — transkripti oxu, kontekstsiz anlaşılmayan hissəni seçmə."""
    from montaj import seminar

    p = store.load(a.pid)
    words = _ad_words(a.pid, p)
    by_media: dict[str, list[dict[str, Any]]] = {}
    for w in words:
        by_media.setdefault(w["media"], []).append(w)
    n = 0
    for mid, ws in by_media.items():
        for c in seminar.highlights(ws, a.min, a.max, a.top):
            n += 1
            print(f"{n}. {c['s'] // 60:.0f}:{c['s'] % 60:04.1f}–{c['e'] // 60:.0f}:{c['e'] % 60:04.1f} ({c['dur']} s, bal {c['score']}): "
                  f"“{c['start_text'][:70]}” … “{c['end_text'][-60:]}”")
            if c["why"]:
                print("   " + "; ".join(c["why"]))
            print(f"   extract {a.pid} {mid}:{c['s']:.2f}-{c['e']:.2f} --title '<ad>'")
    if not n:
        print("uyğun hissə tapılmadı (müddət həddlərini --min/--max ilə dəyiş)")


def cmd_extract(a: argparse.Namespace) -> None:
    """Hissəni ayrıca layihəyə çıxarır: eyni orijinal (hard link — surət yox), eyni analiz (təkrar transkripsiya yox),
    müştəri/rəng/format ana layihədən. Sonra adi iş axını: retakes/cut, framefix, voice-clean, plan..."""
    import os as _os

    parent = store.load(a.pid)
    mid, _, rng = a.range.rpartition(":")
    s, _, e = rng.partition("-")
    s, e = float(s), float(e)
    m = next((x for x in parent["media"] if x["id"] == mid), None) if mid else next(
        (x for x in parent["media"] if x.get("hasVideo") and x.get("role") != "broll"), None)
    if not m:
        raise UserError("Media tapılmadı.", "highlights çıxışındakı əmri olduğu kimi işlədin.")
    base = node_tl("migrate", node_tl("newProject", {"id": "tmp", "title": a.title}))
    child = store.create(a.title, base)
    cid = child["id"]
    src = store.project_dir(a.pid) / m["file"]
    dst = store.project_dir(cid) / m["file"]
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        _os.link(src, dst)  # eyni fayl, əlavə disk yoxdur
    except OSError:
        shutil.copyfile(src, dst)
    store.add_media_record(cid, dict(m))
    an = analysis.analysis_path(store.project_dir(a.pid), m["id"])
    words: list[dict[str, Any]] = []
    if an.is_file():
        dst_an = analysis.analysis_path(store.project_dir(cid), m["id"])
        dst_an.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(an, dst_an)
        words = [w for w in json.loads(an.read_text(encoding="utf-8")).get("words") or [] if w["s"] >= s - 0.02 and w["e"] <= e + 0.05]
    proj = store.load(cid)
    for k in ("brand", "clientId", "options", "aspect", "width", "height", "fps", "fpsRate"):
        if parent.get(k) is not None:
            proj[k] = parent[k]
    proj["parent"] = {"id": a.pid, "media": m["id"], "range": [s, e]}
    store.save(cid, proj, proj["revision"])
    try:
        psb = _load_draft(a.pid)
    except Exception:  # noqa: BLE001
        psb = {}
    card = {"id": "c1", "mediaId": m["id"], "srcIn": round(s, 3), "srcOut": round(e, 3), "include": True,
            "words": [{"w": w["w"], "s": w["s"], "e": w["e"]} for w in words], "text": " ".join(w["w"] for w in words)}
    _save_draft(cid, {"generator": "rules", "musicMood": "", "musicNote": "", "overallNote": "", "removed": {},
                      "subtitles": True, "candidates": {m["id"]: [{"words": words}]}, "cards": [card],
                      "frames": {k: v for k, v in (psb.get("frames") or {}).items() if k == m["id"]},
                      "status": "draft", "options": proj.get("options") or {}})
    print(f"layihə: {cid}  ({e - s:.1f} s, ana layihə {a.pid}) — sonra: retakes/cut, framefix, voice-clean, looks, variants")


def cmd_save(a: argparse.Namespace) -> None:
    """Layihə paketi (orijinal videolar OLMADAN): montaj qərarları, analiz, tarixçə, qaralama, Claude-un B-rollu,
    musiqi, yoxlama hesabatları. Orijinal Drive linkindən bərpa olunur. Şəxsi saxlama üçündür — public repoya qoyma."""
    import tarfile

    pdir = store.project_dir(a.pid)
    p = store.load(a.pid)
    keep_media = {m["file"] for m in p["media"] if (m.get("source") or {}).get("type") in KEEP_SOURCES}
    dst = Path(a.out) if a.out else out_dir(a.pid) / f"{a.pid}_layihe.tar.gz"
    with tarfile.open(dst, "w:gz") as tar:
        for f in sorted(pdir.rglob("*")):
            rel = f.relative_to(pdir).as_posix()
            if f.is_dir() or rel.startswith("media/derived/") or (rel.startswith("media/originals/") and rel not in keep_media):
                continue
            tar.add(f, arcname=f"{a.pid}/{rel}")
        for f in sorted(out_dir(a.pid).glob("*.json")) + sorted(out_dir(a.pid).glob("*.md")):
            tar.add(f, arcname=f"{a.pid}/_out/{f.name}")
    missing = [m for m in p["media"] if m["file"] not in keep_media]
    print(dst, f"{dst.stat().st_size / 1e6:.1f} MB")
    for m in missing:
        src = m.get("source") or {}
        how = f"Drive {src['id']}" if src.get("type") == "drive" else "fayl yenidən verilməlidir"
        print(f"- paketdə deyil: {m['name']} ({how})")


def cmd_restore(a: argparse.Namespace) -> None:
    """Paketdən bərpa: layihə fayllarını qaytarır, orijinal videoları Drive-dan yenidən endirir (və ya --file mid=yol)."""
    import tarfile

    files = dict(x.split("=", 1) for x in (a.file or []))
    with tarfile.open(a.pack) as tar:
        names = tar.getnames()
        pid = names[0].split("/")[0]
        for mem in tar.getmembers():
            if mem.name.startswith("/") or ".." in Path(mem.name).parts or not mem.name.startswith(pid + "/"):
                raise UserError("Paket etibarsızdır.", "Yalnız `session save` ilə hazırlanmış paket işlədin.")
        if store.project_dir(pid).exists() and not a.force:
            raise UserError(f"Layihə artıq var: {pid}", "Üzərinə yazmaq üçün --force.")
        dest = store.project_dir(pid).parent
        for mem in tar.getmembers():
            rel = mem.name.split("/", 1)[1] if "/" in mem.name else ""
            if rel.startswith("_out/"):
                target = out_dir(pid) / rel[5:]
            else:
                target = dest / mem.name
            if mem.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(mem) as fsrc:
                    target.write_bytes(fsrc.read())
    p = store.load(pid)
    for m in p["media"]:
        f = store.project_dir(pid) / m["file"]
        if f.is_file():
            continue
        src = m.get("source") or {}
        f.parent.mkdir(parents=True, exist_ok=True)
        if m["id"] in files:
            shutil.copyfile(files[m["id"]], f)
        elif src.get("type") == "drive" and src.get("id"):
            tmp, _name = drive.download(f"https://drive.google.com/file/d/{src['id']}/view", store.originals_dir(pid), lambda x: None)
            tmp.replace(f)
        else:
            print(f"! çatışmır: {m['name']} — `restore ... --file {m['id']}=<yol>` ilə verin")
            continue
        if m.get("size") and f.stat().st_size != m["size"]:
            print(f"! {m['name']}: ölçü fərqlidir ({f.stat().st_size} ≠ {m['size']}) — başqa fayl ola bilər, yoxlayın")
        print(f"bərpa: {m['name']}")
    print(f"layihə: {pid}, versiya {p['revision']}")


def cmd_retakes(a: argparse.Namespace) -> None:
    """Təkrar və yarımçıq cümlələr: hər biri üçün hazır `cut` təklifi (sonrakı, tam cəhd saxlanılır)."""
    from montaj import quality

    p = store.load(a.pid)
    corr = ((p.get("subtitles") or {}).get("corrections") or [])
    found = 0
    for mid, an in _analyses(a.pid, p).items():
        words = [dict(w) for w in an.get("words") or []]
        for w in words:
            for c in corr:
                if transcribe_norm(w["w"]) == transcribe_norm(c["from"]):
                    w["w"] = c["to"]
        for r in quality.find_retakes(words):
            found += 1
            d, k = r["drop"], r["keep"]
            print(f"{'yarımçıq' if r['kind'] == 'restart' else 'təkrar'} ({r['ratio']}): {d['s']:.2f}–{d['e']:.2f} “{d['text'][:70]}”")
            print(f"   saxlanılan: {k['s']:.2f}–{k['e']:.2f} “{k['text'][:70]}”")
            print(f"   təklif: cut {a.pid} {mid}:{d['s']:.2f}-{d['e'] - 0.02:.2f}")
    if not found:
        print("təkrar/yarımçıq cümlə tapılmadı")


def transcribe_norm(w: str) -> str:
    from montaj import transcribe
    return transcribe.norm_word(w)


def cmd_fix_word(a: argparse.Namespace) -> None:
    """Sözü layihənin hər yerində düzəldir və yadda saxlayır (təkrar analiz/render onu geri qaytarmır)."""
    p = store.load(a.pid)
    r = node_tl("replaceEverywhere", node_tl("migrate", p), a.wrong, a.right)
    saved = store.save(a.pid, r["project"], p["revision"])
    print(f"“{a.wrong}” → “{a.right}”: {r.get('count', '?')} yer; versiya {saved['revision']}")
    if a.remember:
        name = (p.get("brand") or {}).get("name")
        f = profile_path(name) if name else None
        if not f:
            raise UserError("Müştəri profili tapılmadı — söz yalnız bu layihədə düzəldi.", "set-client ilə müştərini təyin edin.")
        prof = json.loads(f.read_text(encoding="utf-8"))
        g = prof.setdefault("glossary", {"terms": [], "fixes": []})
        g.setdefault("fixes", [])
        g["fixes"] = [x for x in g["fixes"] if x["from"].lower() != a.wrong.lower()] + [{"from": a.wrong, "to": a.right}]
        f.write_text(json.dumps(prof, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        root = Path(__file__).resolve().parent.parent
        shown = f.relative_to(root) if f.resolve().is_relative_to(root) else f
        print(f"müştəri lüğətinə yazıldı: {shown} (növbəti videolarda avtomatik)")


def _sb_override(sb: dict[str, Any], ov: dict[str, Any]) -> dict[str, Any]:
    """Planın storyboard düzəlişləri qaralamaya: "cards" (tam kart siyahısı — M09 kimi yığılan montaj), exclude/include/text/order."""
    if ov.get("cards"):
        sb["cards"] = [dict(c) for c in ov["cards"]]
    for n in ov.get("exclude", []):
        sb["cards"][n - 1]["include"] = False
    for n in ov.get("include", []):
        sb["cards"][n - 1]["include"] = True
    for n, txt in (ov.get("text") or {}).items():
        sb["cards"][int(n) - 1]["onScreenText"] = txt
    if ov.get("order"):
        cards = sb["cards"]
        sb["cards"] = [cards[n - 1] for n in ov["order"]] + [c for i, c in enumerate(cards) if i + 1 not in ov["order"]]
    return sb


def cmd_variants(a: argparse.Namespace) -> None:
    """3 storyboard variantının önizləməsi: hər plan qaralamanın SURƏTİNƏ tətbiq olunur, yüngül (540p)
    önizləmə render edilir, əsas anlardan kadrlar götürülür. Layihə dəyişmir."""
    import copy
    import tempfile

    from montaj import render
    from montaj.server import _project_logo

    base = store.load(a.pid)
    sb = _load_draft(a.pid)
    font = render._font()
    o = out_dir(a.pid)
    rows = []
    for k, plan_file in enumerate(a.plans):
        letter = "ABCDEF"[k]
        plan = json.loads(Path(plan_file).read_text(encoding="utf-8"))
        sbv = _sb_override(copy.deepcopy(sb), plan.get("storyboard") or {})
        r = node_tl("applyStoryboard", node_tl("migrate", copy.deepcopy(base)), sbv,
                    {"frames": sbv.get("frames") or {}, "brand": base.get("brand")})
        q = apply_plan(a.pid, r["project"], plan, Path(plan_file).name)
        q["width"], q["height"] = 540, int(round(540 * base["height"] / base["width"] / 2) * 2)
        mp4 = o / f"variant_{letter}.mp4"
        render.render(q, store.project_dir(a.pid), mp4, lambda x: None, logo_path=_project_logo(q, a.pid))
        total = sum(c["srcOut"] - c["srcIn"] for c in node_tl("videoClips", q))
        lay_t = sorted({round(float(g.get("start", 0)) + min(1.0, (g["srcOut"] - g["srcIn"]) / 2), 2)
                        for g in q["clips"] if g["track"] == "t1"})
        seq_t, acc = [], 0.0
        for c in node_tl("videoClips", q):
            if c.get("broll"):
                seq_t.append(round(acc + (c["srcOut"] - c["srcIn"]) / 2, 2))
            acc += c["srcOut"] - c["srcIn"]
        br_t = sorted([round(float(c["start"]) + (c["srcOut"] - c["srcIn"]) / 2, 2) for c in q["clips"] if c["track"] == "v2"] + seq_t)
        times = sorted({0.8, *br_t[:2], *lay_t[:3], max(0.5, total - 1.0)})[:6]
        if len(times) < 4:  # qrafikasız montaj (məs. M09): kadrların ortası
            mids, acc2 = [], 0.0
            for c in node_tl("videoClips", q):
                mids.append(round(acc2 + (c["srcOut"] - c["srcIn"]) / 2, 2))
                acc2 += c["srcOut"] - c["srcIn"]
            step_ = max(1, len(mids) // 6 + (len(mids) % 6 > 0))
            times = sorted(set(mids[::step_]))[:6]
        tiles = []
        for i, t in enumerate(times):
            tile = Path(tempfile.mkstemp(suffix=".png")[1])
            vf = "scale=270:-2"
            if font and i == 0:
                title = f"{letter}: {plan.get('title', '')}"[:38].replace(":", "\\:").replace("'", "")
                vf += f",drawbox=y=0:w=iw:h=30:color=black@0.7:t=fill,drawtext=fontfile={font}:text='{title}':x=6:y=7:fontsize=15:fontcolor=white"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(mp4), "-frames:v", "1", "-vf", vf, str(tile)], check=True)
            tiles.append(tile)
        row = o / f"variant_{letter}.jpg"
        ins = sum((["-i", str(x)] for x in tiles), [])
        subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", f"hstack={len(tiles)}" if len(tiles) > 1 else "null",
                        "-q:v", "3", str(row)], check=True)
        for x in tiles:
            x.unlink()
        rows.append(row)
        print(f"{letter}: {plan.get('title', '')} — {total:.1f} s, kadrlar {', '.join(f'{t:.1f}' for t in times)} s; önizləmə {mp4}")
    sheet = o / "storyboard_variantlari.jpg"
    ins = sum((["-i", str(x)] for x in rows), [])
    w = max(int(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width", "-of", "csv=p=0", str(x)],
                               capture_output=True, text=True).stdout.strip() or 0) for x in rows)
    pads = "".join(f"[{i}]pad={w}:ih:0:0:color=white[p{i}];" for i in range(len(rows)))
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex",
                    pads + "".join(f"[p{i}]" for i in range(len(rows))) + f"vstack={len(rows)}" if len(rows) > 1 else "null",
                    "-q:v", "3", str(sheet)], check=True)
    print(sheet)


def cmd_choose(a: argparse.Namespace) -> None:
    """İstifadəçinin seçdiyi storyboard variantını tətbiq edir: qaralama düzəlişləri → apply → plan."""
    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    sb = _sb_override(_load_draft(a.pid), plan.get("storyboard") or {})
    _save_draft(a.pid, sb)
    cmd_apply(argparse.Namespace(pid=a.pid))
    cmd_plan(argparse.Namespace(pid=a.pid, plan=a.plan))
    _remember_choice(a.pid, plan, Path(a.plan).stem)


def cmd_music_preview(a: argparse.Namespace) -> None:
    """Hər musiqi faylı üçün qısa dinləmə nümunəsi: danışığın başlanğıcı + musiqi (danışıqda azalır)."""
    from montaj import quality

    p = store.load(a.pid)
    try:
        speech = _latest_render(a.pid)
    except UserError:
        m = next(x for x in p["media"] if x.get("hasAudio") and x.get("hasVideo"))
        speech = store.project_dir(a.pid) / m["file"]
    for i, f in enumerate(a.files, 1):
        out = out_dir(a.pid) / f"musiqi_{i}.m4a"
        quality.music_preview(speech, Path(f), out, a.seconds, a.volume)
        print(f"{i}: {Path(f).name} → {out}")


def cmd_export(a: argparse.Namespace) -> None:
    p = store.load(a.pid)
    dst = out_dir(a.pid) / f"{a.pid}.montaj.json"
    dst.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
    print(dst)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m montaj.session")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("--title", required=True)
    n.add_argument("--link", action="append")
    n.add_argument("--file", action="append")
    n.add_argument("--client")
    n.add_argument("--aspect", help="standart 9:16; növün öz formatı varsa (məs. 15 → 16:9) o")
    n.add_argument("--type", type=int, help="video növü (types)")
    n.add_argument("--extra", action="append", help="əlavə növ (qarışıq video, məs. 1 + 13)")
    n.add_argument("--approach", help="yanaşma, məs. M01+M02")
    n.add_argument("--subtype")
    n.add_argument("--uncertain", help="növ aydın deyilsə — nə və niyə")
    n.add_argument("--cut", default="suggest", choices=["keep", "suggest", "auto"])
    n.add_argument("--duration", type=float)
    n.add_argument("--size", help="çıxış ölçüsü, məs. 1080x1920 (kiçik kəsim böyüdülür — standart: böyütmə yoxdur)")
    for k in ("format", "goal", "style", "extras"):
        n.add_argument(f"--{k}", action="append")
    for name in ("storyboard", "apply", "render", "export"):
        sub.add_parser(name).add_argument("pid")
    lk = sub.add_parser("looks", help="rəng variantları (orijinal + A/B/C) bir neçə kadrda")
    lk.add_argument("pid")
    lk.add_argument("--frames", type=int, default=3)
    lk.add_argument("--t", type=float, action="append", help="mənbə videoda kadrın saniyəsi (təkrarlana bilər)")
    lk.add_argument("--all", action="store_true", help="D (zəif işıq) variantını həmişə göstər")
    sub.add_parser("scenes", help="Claude-un B-roll səhnələri (kataloq)")
    mb = sub.add_parser("make-broll", help="səhnəni render edib B-roll kimi əlavə et")
    mb.add_argument("pid")
    mb.add_argument("--kind", required=True)
    mb.add_argument("--props", help="JSON")
    mb.add_argument("--dur", type=float, default=3.0)
    mb.add_argument("--still", action="store_true", help="önizləmə kadrı da (PNG)")
    vc = sub.add_parser("voice-clean", help="arxa səsin təmizlənməsi (danışığı qoruyaraq)")
    vc.add_argument("pid")
    vc.add_argument("--mode", choices=["auto", "on", "off"], default="auto")
    vc.add_argument("--atten", type=float, default=20.0, help="maksimum zəiflətmə, dB (danışığı qorumaq üçün)")
    br = sub.add_parser("add-broll", help="B-roll / araya kadr materialı (video, şəkil)")
    br.add_argument("pid")
    br.add_argument("--link", action="append")
    br.add_argument("--file", action="append")
    ff = sub.add_parser("framefix", help="kadraj düzəlişi (əyrilik + ortalama) qaralamaya")
    ff.add_argument("pid")
    ct = sub.add_parser("cut", help="qaralamadan mənbə aralığını çıxar: [media:]başla-son")
    ct.add_argument("pid")
    ct.add_argument("ranges", nargs="+")
    vf = sub.add_parser("verify", help="yekun render yoxlaması")
    vf.add_argument("pid")
    vf.add_argument("--mp4")
    vf.add_argument("--no-asr", action="store_true")
    es = sub.add_parser("event-scan", help="M09: tədbir/proses kadrlarının analizi")
    es.add_argument("pid")
    es.add_argument("--no-faces", action="store_true")
    ep = sub.add_parser("event-plan", help="M09: musiqi ritminə düzülmüş 3 variant")
    ep.add_argument("pid")
    ep.add_argument("--music", required=True)
    ep.add_argument("--target", type=float, help="müddət, s (standart: A/B 30, C 17)")
    ep.add_argument("--volume", type=float, default=0.9)
    ep.add_argument("--variants", default="ABC")
    bg = sub.add_parser("bg", help="arxa fon: blur | color | image | video | scene (--preview — müqayisə)")
    bg.add_argument("pid")
    bg.add_argument("--mode", choices=["blur", "color", "image", "video", "scene"])
    bg.add_argument("--color")
    bg.add_argument("--color2")
    bg.add_argument("--direction", choices=["vertical", "horizontal", "radial"])
    bg.add_argument("--file")
    bg.add_argument("--kind")
    bg.add_argument("--props")
    bg.add_argument("--strength", type=float)
    bg.add_argument("--dim", type=float)
    bg.add_argument("--keep-below", type=float, help="bu hündürlükdən (0..1) aşağı orijinal qalır — masa")
    bg.add_argument("--feather", type=float)
    bg.add_argument("--smooth", type=float)
    bg.add_argument("--fast", action="store_true")
    bg.add_argument("--spec", action="append", help="JSON; bir neçə dəfə — önizləmədə müqayisə")
    bg.add_argument("--preview", action="store_true")
    bg.add_argument("--media")
    bg.add_argument("--off", action="store_true")
    mc = sub.add_parser("multicam", help="virtual multikamera: plan ölçüləri (ümumi/orta/yaxın) bir rakursdan")
    mc.add_argument("pid")
    mc.add_argument("--style", choices=["calm", "dynamic"], default="calm")
    du = sub.add_parser("duo", help="növ 11: iki nəfər — kadraj danışana keçir (switch) və ya bölünmüş ekran (split)")
    du.add_argument("pid")
    du.add_argument("--mode", choices=["switch", "split"], default="switch")
    du.add_argument("--min-len", type=float, default=1.5)
    qp = sub.add_parser("qa-plan", help="M10: sürətli sual-cavab — 3 variant")
    qp.add_argument("pid")
    qp.add_argument("--no-faces", action="store_true")
    ty = sub.add_parser("types", help="video növləri, yanaşmalar, sorğu sualları (reyestr)")
    ty.add_argument("n", nargs="?", type=int)
    ty.add_argument("--survey", action="store_true")
    ty.add_argument("--approaches", action="store_true")
    st = sub.add_parser("set-type", help="layihəyə video növü qeydi")
    st.add_argument("pid")
    st.add_argument("type", type=int)
    st.add_argument("--extra", action="append")
    st.add_argument("--goal")
    st.add_argument("--approach")
    st.add_argument("--subtype")
    st.add_argument("--uncertain")
    cp = sub.add_parser("carousel-plan", help="video karusel planı (örtük + fikirlər + çağırış)")
    cp.add_argument("pid")
    cr = sub.add_parser("carousel", help="video karusel slaydları (1080x1350 MP4)")
    cr.add_argument("pid")
    cr.add_argument("plan")
    tp = sub.add_parser("tale-plan", help="nağıl: obraz/məkanlardan cizgi səhnələri")
    tp.add_argument("pid")
    tp.add_argument("--mode", default="cover_pip", choices=["cover_pip", "cover"])
    mgs = sub.add_parser("mg-scan", help="danışıqdakı rəqəmlər və qrafik səhnə təklifi (motion graphics)")
    mgs.add_argument("pid")
    hl = sub.add_parser("highlights", help="uzun videodan müstəqil qısa hissələr (seminar)")
    hl.add_argument("pid")
    hl.add_argument("--min", type=float, default=20)
    hl.add_argument("--max", type=float, default=75)
    hl.add_argument("--top", type=int, default=8)
    ex = sub.add_parser("extract", help="hissəni ayrıca layihəyə çıxar ([media:]başla-son)")
    ex.add_argument("pid")
    ex.add_argument("range")
    ex.add_argument("--title", required=True)
    asn = sub.add_parser("ad-scan", help="reklam faktları (qiymət, tarix, çağırış, faydalar)")
    asn.add_argument("pid")
    apl = sub.add_parser("ad-plan", help="reklam üçün 3 storyboard variantı (plan faylları)")
    apl.add_argument("pid")
    sv = sub.add_parser("save", help="layihə paketi (orijinal videolar olmadan)")
    sv.add_argument("pid")
    sv.add_argument("--out")
    rs = sub.add_parser("restore", help="paketdən bərpa (orijinal Drive-dan)")
    rs.add_argument("pack")
    rs.add_argument("--file", action="append", help="mid=yol (Drive mənbəyi olmayan media üçün)")
    rs.add_argument("--force", action="store_true")
    rt = sub.add_parser("retakes", help="təkrar/yarımçıq cümlələr və cut təklifi")
    rt.add_argument("pid")
    wd = sub.add_parser("words", help="şübhəli tanınmış sözlər")
    wd.add_argument("pid")
    wd.add_argument("--threshold", type=float, default=0.6)
    fw = sub.add_parser("fix-word", help="sözü hər yerdə düzəlt və yadda saxla")
    fw.add_argument("pid")
    fw.add_argument("wrong")
    fw.add_argument("right")
    fw.add_argument("--remember", action="store_true", help="müştərinin profil lüğətinə də yaz (növbəti videolar üçün)")
    vr = sub.add_parser("variants", help="2–3 storyboard variantının önizləməsi (layihə dəyişmir)")
    vr.add_argument("pid")
    vr.add_argument("plans", nargs="+")
    ch = sub.add_parser("choose", help="seçilmiş variantı tətbiq et (qaralama → apply → plan)")
    ch.add_argument("pid")
    ch.add_argument("plan")
    mp = sub.add_parser("music-preview", help="musiqi dinləmə nümunələri")
    mp.add_argument("pid")
    mp.add_argument("files", nargs="+")
    mp.add_argument("--seconds", type=float, default=20)
    mp.add_argument("--volume", type=float, default=0.12)
    e = sub.add_parser("edit")
    e.add_argument("pid")
    e.add_argument("--exclude")
    e.add_argument("--include")
    e.add_argument("--text", action="append")
    e.add_argument("--order")
    e.add_argument("--subtitles", choices=["on", "off"])
    ed = sub.add_parser("editor")
    ed.add_argument("pid")
    ed.add_argument("--assets", help="JSON: media id -> artifact asset url")
    ed.add_argument("--local", action="store_true", help="önizləmələrə nisbi yol (yerli sınaq)")
    pl = sub.add_parser("plan")
    pl.add_argument("pid")
    pl.add_argument("plan")
    sc = sub.add_parser("set-client")
    sc.add_argument("pid")
    sc.add_argument("--client", required=True)
    ae = sub.add_parser("apply-edits")
    ae.add_argument("pid")
    ae.add_argument("edits")
    ae.add_argument("--assets-dir", help="redaktorun yüklədiyi faylların endirildiyi qovluq")
    a = ap.parse_args(argv)
    try:
        {"new": cmd_new, "storyboard": cmd_storyboard, "edit": cmd_edit, "apply": cmd_apply,
         "render": cmd_render, "export": cmd_export, "editor": cmd_editor,
         "apply-edits": cmd_apply_edits, "set-client": cmd_set_client, "plan": cmd_plan, "looks": cmd_looks,
         "cut": cmd_cut, "framefix": cmd_framefix, "add-broll": cmd_add_broll, "voice-clean": cmd_voice_clean, "scenes": cmd_scenes, "make-broll": cmd_make_broll, "verify": cmd_verify, "words": cmd_words, "retakes": cmd_retakes, "save": cmd_save, "restore": cmd_restore, "ad-scan": cmd_ad_scan, "ad-plan": cmd_ad_plan, "highlights": cmd_highlights, "extract": cmd_extract, "mg-scan": cmd_mg_scan, "tale-plan": cmd_tale_plan, "carousel-plan": cmd_carousel_plan, "types": cmd_types, "event-scan": cmd_event_scan, "event-plan": cmd_event_plan, "qa-plan": cmd_qa_plan, "duo": cmd_duo, "multicam": cmd_multicam, "bg": cmd_bg, "set-type": cmd_set_type, "carousel": cmd_carousel, "fix-word": cmd_fix_word,
         "variants": cmd_variants, "choose": cmd_choose, "music-preview": cmd_music_preview}[a.cmd](a)
    except UserError as err:
        print(f"XƏTA: {err.message}\nNƏ ETMƏLİ: {err.hint}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
