"""Çəkiliş paketi: bir çəkilişin bütün videoları (Drive qovluğu) bir əmrlə hazırlanır — AI-sız.

Bir çəkiliş = bir müştəri, eyni məkan/işıq, ~10 video (QAYDALAR.md §2–3). Hər fayl ayrıca layihə olur və ardıcıl
bu addımlardan keçir: new → storyboard (transkripsiya + material yoxlaması) → voice-clean → retakes.
Addımlar mövcud `montaj.session` əmrləridir (eyni prosesdə — Whisper modeli bir dəfə yüklənir).

Vəziyyət `<data>/batches/<id>.json`-da saxlanılır: əmr yenidən işə salınanda bitmiş addımlar təkrarlanmır,
xəta verən video digərlərini dayandırmır. Xülasə: `<out>/batches/<id>.md`.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import time
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Any

from montaj import drive, store
from montaj.config import data_dir
from montaj.errors import UserError

STEPS = ["new", "storyboard", "voice-clean", "retakes"]


def batch_id(client: str, date: str) -> str:
    return store.slugify(f"{client} {date}")


def manifest_path(bid: str) -> Path:
    return data_dir() / "batches" / f"{bid}.json"


def out_root() -> Path:
    return Path(os.environ.get("MONTAJ_OUT_DIR", data_dir() / "out"))


def load(bid: str) -> dict[str, Any]:
    p = manifest_path(bid)
    if not p.is_file():
        raise UserError(f"Paket tapılmadı: {bid}", "Əvvəl `batch --link <qovluq> --client <ad>` işə salın.")
    return json.loads(p.read_text(encoding="utf-8"))


def save(m: dict[str, Any]) -> None:
    p = manifest_path(m["id"])
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)


def _run(argv: list[str]) -> tuple[int, str]:
    """`montaj.session` əmrini eyni prosesdə işlət, çıxışı tut. Gözlənilməz xəta paketi dayandırmır."""
    from montaj import session

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            code = session.main(argv)
        except SystemExit as e:  # argparse
            code = int(e.code or 0)
        except Exception:  # noqa: BLE001
            buf.write(traceback.format_exc())
            code = 1
    return code, buf.getvalue()


def _error_line(log: str) -> str:
    lines = [x.strip() for x in log.splitlines() if x.strip()]
    for x in lines:
        if x.startswith("XƏTA:"):
            return x[5:].strip()
    return (lines[-1] if lines else "naməlum xəta")[:200]


def _warnings(pid: str) -> list[str]:
    f = out_root() / pid / "material_yoxlama.json"
    if not f.is_file():
        return []
    r = json.loads(f.read_text(encoding="utf-8"))
    return [w for i in r.get("items", []) for w in i.get("warnings", [])] + list(r.get("notes", []))


def _new_argv(m: dict[str, Any], v: dict[str, Any]) -> list[str]:
    argv = ["new", "--title", v["title"], "--client", m["client"]]
    argv += ["--file", v["file"]] if v.get("file") else ["--link", v["link"]]
    if m.get("type"):
        argv += ["--type", str(m["type"])]
    return argv


def create(client: str, date: str, link: str | None = None, files: list[str] | None = None,
           vtype: int | None = None, list_folder: Callable[[str], list[dict]] | None = None) -> dict[str, Any]:
    """Paketi yarat və ya mövcudunu qaytar. Qovluqdakı yeni fayllar sona əlavə olunur (köhnələr toxunulmur)."""
    bid = batch_id(client, date)
    try:
        m = load(bid)
    except UserError:
        m = {"id": bid, "client": client, "date": date, "type": vtype, "link": link, "created": time.time(), "videos": []}
    if vtype and not m.get("type"):
        m["type"] = vtype
    lister = list_folder or drive.list_folder
    entries = ([{"name": f["name"], "link": f["link"]} for f in lister(link)] if link and drive.is_folder(link)
               else [{"name": Path(link).name, "link": link}] if link else [])
    entries += [{"name": Path(f).name, "file": str(f)} for f in files or []]
    known = {v.get("link") or v.get("file") for v in m["videos"]}
    for e in entries:
        if (e.get("link") or e.get("file")) in known:
            continue
        n = len(m["videos"]) + 1
        m["videos"].append({"n": n, "name": e["name"], "link": e.get("link"), "file": e.get("file"),
                            "title": f"{client} {date} {n:02d}", "pid": None, "steps": {}, "warnings": []})
    if not m["videos"]:
        raise UserError("Paketdə video yoxdur.", "Qovluq linkini (Linki olan hər kəs — Baxan) və ya --file verin.")
    save(m)
    return m


def run(m: dict[str, Any], only: list[int] | None = None, steps: list[str] | None = None,
        log: Callable[[str], None] = print) -> dict[str, Any]:
    steps = steps or STEPS
    for v in m["videos"]:
        if only and v["n"] not in only:
            continue
        for step in steps:
            if v["steps"].get(step) == "ok":
                continue
            if step != "new" and not v["pid"]:
                break
            t0 = time.time()
            log(f"[{v['n']:02d}/{len(m['videos'])}] {v['name']}: {step}…")
            code, out = _run(_new_argv(m, v) if step == "new" else [step, v["pid"]])
            if step == "new" and code == 0:
                v["pid"] = next((x.split()[1] for x in out.splitlines() if x.startswith("layihə:")), None)
                code = 0 if v["pid"] else 1
            logdir = out_root() / (v["pid"] or f"_batch_{m['id']}")
            logdir.mkdir(parents=True, exist_ok=True)
            (logdir / f"batch_{step}.log").write_text(out, encoding="utf-8")
            v["steps"][step] = "ok" if code == 0 else f"xəta: {_error_line(out)}"
            v.setdefault("seconds", {})[step] = round(time.time() - t0, 1)
            if step == "storyboard" and code == 0:
                v["warnings"] = _warnings(v["pid"])
            save(m)
            if code != 0:
                log(f"   ✗ {v['steps'][step]}")
                break
    write_summary(m)
    return m


def summary(m: dict[str, Any]) -> str:
    ok = [v for v in m["videos"] if v["steps"] and all(s == "ok" for s in v["steps"].values())]
    bad = sum(1 for v in m["videos"] if any(s != "ok" for s in v["steps"].values()))
    lines = [f"# Çəkiliş paketi: {m['client']} — {m['date']}", "",
             f"Video: {len(m['videos'])} · hazır: {len(ok)} · xəta: {bad}", "",
             "| # | Fayl | Layihə | Addımlar | Vaxt | Diqqət |", "|---|---|---|---|---|---|"]
    for v in m["videos"]:
        st = ", ".join(f"{k} ✓" if s == "ok" else f"{k} ✗" for k, s in v["steps"].items()) or "başlanmayıb"
        secs = sum((v.get("seconds") or {}).values())
        warn = "; ".join(v["warnings"][:3]) + (" …" if len(v["warnings"]) > 3 else "")
        lines.append(f"| {v['n']} | {v['name']} | {v['pid'] or '—'} | {st} | {secs / 60:.1f} dəq | {warn} |")
    errs = [(v, k, s) for v in m["videos"] for k, s in v["steps"].items() if s != "ok"]
    if errs:
        lines += ["", "## Xətalar"] + [f"- {v['n']} {v['name']} — {k}: {s[6:]}" for v, k, s in errs]
    return "\n".join(lines) + "\n"


def write_summary(m: dict[str, Any]) -> Path:
    p = out_root() / "batches" / f"{m['id']}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(summary(m), encoding="utf-8")
    return p
