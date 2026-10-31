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
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

os.environ.setdefault("MONTAJ_SYNC_DERIVE", "1")

from montaj import analysis, clients, drive, store  # noqa: E402
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
    proj = store.load(pid)
    proj = node_tl("migrate", proj)
    from montaj import reframe
    w, h = reframe.output_size(reframe.primary_video(proj["media"]), a.aspect if a.aspect in reframe.ASPECTS else "source")
    proj.update(options=options, aspect=a.aspect, width=w, height=h, brand=brand, clientId=brand and brand["id"])
    store.save(pid, proj, proj["revision"])
    print(f"layihə: {pid}  çıxış: {w}x{h}")


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
    out = out_dir(a.pid) / f"{a.pid}_r{p['revision']}.mp4"
    render(p, store.project_dir(a.pid), out, lambda x: None, logo_path=_project_logo(p, a.pid))
    info = mediautil.probe(out)
    print(out)
    print(f"çıxış: {info['width']}x{info['height']} {info['fps']} fps {info['duration']} san "
          f"{out.stat().st_size / 1e6:.1f} MB")
    for c in conversions(p):
        print("-", c)


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
                  "colorsConfirmed": "derived" not in (prof.get("theme_source") or ""), "palette": prof.get("palette"),
                  "fonts": prof.get("fonts"), "cautions": prof.get("cautions") or [], "source": "expert-reels profil"}
    saved = store.save(a.pid, p, p["revision"])
    print(f"müştəri: {prof['name']}; rənglər təsdiqlənib: {p['brand']['colorsConfirmed']}; versiya {saved['revision']}")


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


# Rəng korreksiyası şablonları (hamısı yüngül; ölçü/format dəyişmir). Hər video üçün `looks` əmri
# A–D müqayisə şəklini hazırlayır, istifadəçi seçir, seçim plan.json-da "look" ilə verilir.
# Standart "C"-dir (istifadəçinin ilk seçimi); "look": null — rəng düzəlişi yoxdur.
LOOKS: dict[str, dict[str, float]] = {
    "A": {"vibrance": 0.06},
    "B": {"contrast": 1.03, "saturation": 1.04, "vibrance": 0.05},
    "C": {"brightness": 0.01, "contrast": 1.04, "saturation": 1.05, "sharpen": 0.25},
    "D": {"depth": 1.0, "vibrance": 0.07, "sharpen": 0.2},
}
LOOK_LABELS = {"A": "çox az canlılıq", "B": "az kontrast + az canlılıq",
               "C": "az kontrast + bir az işıq + yüngül kəskinlik", "D": "dərinlik + az canlılıq + yüngül kəskinlik"}
LOOK_KEYS = ("brightness", "contrast", "saturation", "vibrance", "depth", "sharpen")


def cmd_looks(a: argparse.Namespace) -> None:
    """Hər video üçün rəng variantları: orijinal + A–D, eyni kadrda (render ilə eyni filtrlər)."""
    from montaj import render

    p = store.load(a.pid)
    vids = [c for c in p["clips"] if c["track"] == "v1" and c.get("media")]
    media = {m["id"]: m for m in p["media"]}
    if vids:
        c = max(vids, key=lambda x: x["srcOut"] - x["srcIn"])
        m, t = media[c["media"]], (c["srcIn"] + c["srcOut"]) / 2
    else:
        m = next((x for x in p["media"] if x.get("hasVideo") and not x.get("isImage")), None)
        if not m:
            raise UserError("Layihədə video yoxdur.", "Əvvəlcə `new` ilə video əlavə edin.")
        t = float(m.get("duration") or 2) / 2
    if a.t is not None:
        t = a.t
    src = store.project_dir(a.pid) / m["file"]
    font = render._font()
    o = out_dir(a.pid)
    tiles = []
    for name in ["orijinal", *LOOKS]:
        label = "Orijinal" if name == "orijinal" else f"{name}: {LOOK_LABELS[name]}"
        adj = {} if name == "orijinal" else LOOKS[name]
        f = ([render.HDR_TO_SDR] if m.get("hdr") else []) + render.color_filters(adj) + render.sharpen_filter(adj)
        f.append("scale=540:-2:flags=lanczos")
        if font:
            esc = label.replace("\\", "").replace(":", "\\:").replace("'", "")
            f.append(f"drawbox=y=0:w=iw:h=40:color=black@0.65:t=fill,drawtext=fontfile={font}:text='{esc}':x=10:y=9:fontsize=20:fontcolor=white")
        tile = o / f"reng_{name}.png"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", str(src), "-frames:v", "1",
                        "-vf", ",".join(f), str(tile)], check=True)
        tiles.append(tile)
    sheet = o / "reng_variantlari.jpg"
    ins = sum((["-i", str(x)] for x in [tiles[0], tiles[1], tiles[2], tiles[0], tiles[3], tiles[4]]), [])
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex",
                    "[0][1][2]hstack=3[t];[3][4][5]hstack=3[b];[t][b]vstack", "-q:v", "3", str(sheet)], check=True)
    for x in tiles:
        x.unlink()
    print(f"kadr: {m.get('name')} {t:.1f} s")
    print(sheet)


def cmd_plan(a: argparse.Namespace) -> None:
    """Təsdiqlənmiş storyboard planını (JSON məlumat) layihəyə tətbiq edir — hər video üçün kod yazılmır."""
    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    for s in plan.get("sfx") or []:
        _sfx_media(a.pid, s["kind"])
    p = store.load(a.pid)
    q = node_tl("migrate", p)
    was_manual = {c["id"] for c in q["clips"] if c.get("manual")}
    q["clips"] = [c for c in q["clips"] if not (c.get("origin") == "plan" and not c.get("manual"))]
    if plan.get("captions") and q.get("subtitles"):
        q = node_tl("setSubtitleStyle", q, plan["captions"].get("style") or {})
        q["subtitles"]["enabled"] = plan["captions"].get("enabled", True)
        q["clips"] = [c for c in q["clips"] if not (c["track"] == "t1" and c.get("origin") == "ai")] if plan.get("dropStoryboardText") else q["clips"]
    for c in plan.get("corrections") or []:
        q = node_tl("replaceEverywhere", q, c["from"], c["to"])["project"]
    for z in plan.get("zooms") or []:  # punch-in: klip zaman xəttində bölünür, ortadakı hissə yaxınlaşdırılır
        for t in (z["to"], z["from"]):
            seg = next((c for c in node_tl("videoClips", q)
                        if _start(q, c["id"]) + 0.15 < t < _start(q, c["id"]) + c["srcOut"] - c["srcIn"] - 0.15), None)
            if seg:
                q = node_tl("split", q, seg["id"], t)
        mid = next(c for c in node_tl("videoClips", q) if abs(_start(q, c["id"]) - z["from"]) < 0.05)
        m = next(x for x in q["media"] if x["id"] == mid["media"])
        fr = {"aspect": q.get("aspect") or "source", "mode": "auto", "s": round(1 / float(z.get("scale", 1.12)), 4),
              "baseW": 1, "baseH": 1, "keys": [{"t": mid["srcIn"], "cx": z.get("cx", 0.5), "cy": z.get("cy", 0.45)}],
              "rotate": 0, "warnings": [], "planZoom": True}
        if m.get("width") and q.get("width") and abs(m["width"] / m["height"] - q["width"] / q["height"]) > 0.02:
            raise UserError("Punch-in yalnız eyni ölçülü kadrda avtomatik qurulur.", "Kadrajı redaktorda əl ilə edin.")
        q = node_tl("setFrame", q, mid["id"], fr, {"manual": False})
    for g in plan.get("graphics") or []:
        q = node_tl("addGraphic", q, {**g, "origin": "plan"})
    look_name = plan.get("look", "C")
    if look_name and look_name not in LOOKS:
        raise UserError(f"Naməlum rəng şablonu: {look_name}", "Mövcud: " + ", ".join(LOOKS))
    keys = LOOK_KEYS
    for c in q["clips"]:  # rəngi əl ilə dəyişdirilmiş klipə toxunulmur; əvvəlki planın şablonu yenilənir
        if c["track"] != "v1":
            continue
        adj = dict(c.get("adjust") or {})
        cur = {k: adj[k] for k in keys if k in adj}
        if cur and cur not in LOOKS.values():
            continue
        for k in keys:
            adj.pop(k, None)
        if look_name:
            adj.update(LOOKS[look_name])
        if adj:
            c["adjust"] = adj
        else:
            c.pop("adjust", None)
    for s in plan.get("sfx") or []:
        med = next(x for x in store.load(a.pid)["media"] if x["id"] == f"sfx_{s['kind']}")
        if not any(x["id"] == med["id"] for x in q["media"]):
            q["media"].append(med)
        q = node_tl("addMedia", {**q, "media": [x for x in q["media"] if x["id"] != med["id"]]}, med,
                    {"targetTrack": "s1", "at": s["t"]})
        new = q["clips"][-1]
        new["volume"] = s.get("vol", 0.3)
        new["origin"] = "plan"
    for c in q["clips"]:  # plan qərarları "əl ilə" sayılmır
        if c["id"] not in was_manual and c.get("origin") in ("plan", "ai", "import", "auto", None):
            c["manual"] = False
    q["planApplied"] = {"at": __import__("time").time(), "file": Path(a.plan).name}
    cur = store.load(a.pid)
    saved = store.save(a.pid, q, cur["revision"])
    print(f"plan tətbiq olundu: {len(plan.get('graphics') or [])} qrafika, {len(plan.get('zooms') or [])} yaxınlaşma, "
          f"{len(plan.get('sfx') or [])} səs effekti, {len(plan.get('corrections') or [])} düzəliş, "
          f"rəng: {look_name or 'yox'}; versiya {saved['revision']}")


def _start(q: dict[str, Any], cid: str) -> float:
    t = 0.0
    for c in node_tl("videoClips", q):
        if c["id"] == cid:
            return t
        t += c["srcOut"] - c["srcIn"]
    return t


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
    n.add_argument("--aspect", default="9:16")
    n.add_argument("--cut", default="suggest", choices=["keep", "suggest", "auto"])
    n.add_argument("--duration", type=float)
    for k in ("format", "goal", "style", "extras"):
        n.add_argument(f"--{k}", action="append")
    for name in ("storyboard", "apply", "render", "export"):
        sub.add_parser(name).add_argument("pid")
    lk = sub.add_parser("looks", help="rəng variantları (orijinal + A–D) müqayisə şəkli")
    lk.add_argument("pid")
    lk.add_argument("--t", type=float, help="mənbə videoda kadrın saniyəsi")
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
         "apply-edits": cmd_apply_edits, "set-client": cmd_set_client, "plan": cmd_plan, "looks": cmd_looks}[a.cmd](a)
    except UserError as err:
        print(f"XƏTA: {err.message}\nNƏ ETMƏLİ: {err.hint}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
