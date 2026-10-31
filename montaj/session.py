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
    e = sub.add_parser("edit")
    e.add_argument("pid")
    e.add_argument("--exclude")
    e.add_argument("--include")
    e.add_argument("--text", action="append")
    e.add_argument("--order")
    e.add_argument("--subtitles", choices=["on", "off"])
    a = ap.parse_args(argv)
    try:
        {"new": cmd_new, "storyboard": cmd_storyboard, "edit": cmd_edit, "apply": cmd_apply,
         "render": cmd_render, "export": cmd_export}[a.cmd](a)
    except UserError as err:
        print(f"XƏTA: {err.message}\nNƏ ETMƏLİ: {err.hint}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
