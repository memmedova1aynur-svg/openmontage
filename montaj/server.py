"""Montaj paneli serveri (FastAPI).

Marşrutlar:
  GET  /                                    — panel (Azərbaycan dilində)
  GET  /api/status                          — real imkanlar (ffmpeg, whisper, LLM açarı var/yox)
  GET  /api/projects | POST /api/projects   — siyahı / yarat
  GET  /api/projects/{id} | PUT             — yüklə / avtomatik saxla
  POST /api/projects/{id}/media?name=...    — fayl yüklə (xam gövdə, axınla)
  GET  /api/projects/{id}/media/{mid}       — orijinal və ya ?preview=1 proksi (Range dəstəyi)
  GET  /api/projects/{id}/media/{mid}/peaks — dalğa forması
  POST /api/projects/{id}/proposals/silence — səssizlik təklifi (tətbiq etmir)
  POST /api/projects/{id}/transcribe        — yerli transkripsiya işi
  POST /api/projects/{id}/proposals/fillers — doldurucu söz təklifi (transkriptdən)
  POST /api/projects/{id}/render            — MP4 render işi
  GET  /api/jobs/{job}                      — iş statusu
  GET  /api/projects/{id}/renders/{name}    — hazır MP4
"""

from __future__ import annotations

import json
import os
import threading
import time
import traceback
import uuid
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from montaj import media as mediautil
from montaj import store, transcribe
from montaj.model import ProjectError, layout, track_kinds
from montaj.render import render

UI_DIR = Path(__file__).resolve().parent / "ui"
MAX_UPLOAD = int(os.environ.get("MONTAJ_MAX_UPLOAD_MB", "4096")) * 1024 * 1024

app = FastAPI(title="Montaj paneli")
app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")

_jobs: dict[str, dict[str, Any]] = {}
_jobs_lock = threading.Lock()


def _job(kind: str, pid: str, fn: Callable[[Callable[[float], None]], Any]) -> str:
    jid = uuid.uuid4().hex[:12]
    with _jobs_lock:
        _jobs[jid] = {"id": jid, "kind": kind, "project": pid, "status": "running",
                      "progress": 0.0, "startedAt": time.time()}

    def progress(x: float) -> None:
        _jobs[jid]["progress"] = round(x, 3)

    def run() -> None:
        try:
            result = fn(progress)
            _jobs[jid].update(status="done", progress=1.0, result=result)
        except Exception as exc:  # noqa: BLE001 — istifadəçiyə mesaj göstərilir
            traceback.print_exc()
            _jobs[jid].update(status="error", error=str(exc))

    threading.Thread(target=run, daemon=True).start()
    return jid


def _load(pid: str) -> dict[str, Any]:
    try:
        return store.load(pid)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(404, "Layihə tapılmadı") from exc


def _media(project: dict[str, Any], mid: str) -> dict[str, Any]:
    m = next((m for m in project.get("media", []) if m["id"] == mid), None)
    if m is None:
        raise HTTPException(404, "Media tapılmadı")
    return m


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    html = (UI_DIR / "index.html").read_text(encoding="utf-8")
    for asset in ("app.css", "app.js"):
        v = int((UI_DIR / asset).stat().st_mtime)
        html = html.replace(f"/ui/{asset}", f"/ui/{asset}?v={v}")
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


@app.get("/api/status")
def status() -> dict[str, Any]:
    w = transcribe.available()
    return {
        "ffmpeg": mediautil.ffmpeg_available(),
        "transcription": {
            "available": w["installed"],
            "engine": "faster-whisper (yerli)",
            "model": w["model"],
            "note": "Azərbaycan dilində söz kəsimlərinin keyfiyyəti real video ilə hələ təsdiqlənməyib.",
        },
        "silence": {"available": mediautil.ffmpeg_available(), "engine": "ffmpeg silencedetect (yerli)"},
        # Yalnız açarın olub-olmadığı bildirilir — qiyməti heç vaxt.
        "llm": {
            "available": False,
            "keyPresent": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "note": "LLM əsaslı montaj təklifi bu versiyada qoşulmayıb.",
        },
        "render": {"engine": "ffmpeg", "remotion": False},
    }


@app.get("/api/projects")
def projects() -> list[dict[str, Any]]:
    return store.list_projects()


@app.post("/api/projects")
async def create_project(request: Request) -> dict[str, Any]:
    body = await request.json()
    title = (body.get("title") or "Yeni layihə").strip()[:120]
    base = body.get("project") or {}
    if not base.get("tracks"):
        raise HTTPException(400, "Boş layihə şablonu göndərilməlidir")
    base.setdefault("media", [])
    base.setdefault("clips", [])
    base["id"] = "tmp"
    return store.create(title, base)


@app.get("/api/projects/{pid}")
def get_project(pid: str) -> dict[str, Any]:
    return _load(pid)


@app.put("/api/projects/{pid}")
async def put_project(pid: str, request: Request) -> JSONResponse:
    body = await request.json()
    _load(pid)
    try:
        saved = store.save(pid, body["project"], body.get("baseRevision"))
    except store.RevisionConflict as exc:
        return JSONResponse({"error": str(exc), "revision": exc.current}, status_code=409)
    except (ProjectError, KeyError) as exc:
        raise HTTPException(400, str(exc)) from exc
    return JSONResponse({"revision": saved["revision"], "savedAt": saved["savedAt"], "media": saved["media"]})


def _derive(pid: str, mid: str) -> None:
    project = store.load(pid)
    m = next(m for m in project["media"] if m["id"] == mid)
    src = store.project_dir(pid) / m["file"]
    out = store.derived_dir(pid)
    patch: dict[str, Any] = {}
    try:
        mediautil.make_proxy(src, out / f"{mid}.mp4", m["hasVideo"], m["hasAudio"])
        patch["preview"] = f"media/derived/{mid}.mp4"
    except Exception as exc:  # noqa: BLE001
        patch["previewError"] = str(exc)[-300:]
    if m["hasAudio"]:
        try:
            (out / f"{mid}.peaks.json").write_text(json.dumps(mediautil.peaks(src)))
            patch["peaks"] = True
        except Exception:  # noqa: BLE001
            patch["peaks"] = False
    store.update_media_record(pid, mid, patch)


@app.post("/api/projects/{pid}/media")
async def upload_media(pid: str, request: Request, name: str = "fayl") -> dict[str, Any]:
    _load(pid)
    safe = "".join(ch for ch in Path(name).name if ch.isalnum() or ch in "._- ").strip() or "fayl"
    mid = "m_" + uuid.uuid4().hex[:10]
    ext = Path(safe).suffix.lower()[:8] or ".bin"
    dst_dir = store.originals_dir(pid)
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / f"{mid}{ext}"
    tmp = dst.with_suffix(ext + ".part")
    size = 0
    with tmp.open("wb") as fh:
        async for chunk in request.stream():
            size += len(chunk)
            if size > MAX_UPLOAD:
                fh.close()
                tmp.unlink(missing_ok=True)
                raise HTTPException(413, "Fayl çox böyükdür")
            fh.write(chunk)
    if size == 0:
        tmp.unlink(missing_ok=True)
        raise HTTPException(400, "Boş fayl")
    tmp.replace(dst)
    os.chmod(dst, 0o444)  # orijinal yalnız oxunur
    try:
        info = mediautil.probe(dst)
    except Exception as exc:  # noqa: BLE001
        dst.unlink(missing_ok=True)
        raise HTTPException(400, "Fayl oxunmadı — video və ya səs faylı deyil") from exc
    if not (info["hasVideo"] or info["hasAudio"]) or info["duration"] <= 0:
        dst.unlink(missing_ok=True)
        raise HTTPException(400, "Faylda oynadıla bilən video/səs tapılmadı")
    record = {"id": mid, "name": safe, "file": f"media/originals/{dst.name}", "size": size, **info}
    project = store.add_media_record(pid, record)
    threading.Thread(target=_derive, args=(pid, mid), daemon=True).start()
    return {"media": record, "revision": project["revision"]}


@app.get("/api/projects/{pid}/media/{mid}")
def media_file(pid: str, mid: str, preview: int = 0) -> FileResponse:
    project = _load(pid)
    m = _media(project, mid)
    root = store.project_dir(pid)
    rel = m.get("preview") if preview and m.get("preview") else m["file"]
    path = (root / rel).resolve()
    if root.resolve() not in path.parents or not path.is_file():
        raise HTTPException(404, "Fayl tapılmadı")
    media_type = "video/mp4" if rel.endswith(".mp4") else None
    return FileResponse(path, media_type=media_type)


@app.get("/api/projects/{pid}/media/{mid}/peaks")
def media_peaks(pid: str, mid: str) -> FileResponse:
    _load(pid)
    f = store.derived_dir(pid) / f"{mid}.peaks.json"
    if not f.is_file():
        raise HTTPException(404, "Dalğa forması hələ hazır deyil")
    return FileResponse(f, media_type="application/json")


@app.get("/api/projects/{pid}/media/{mid}/frame")
def media_frame(pid: str, mid: str, t: float = 0.0) -> FileResponse:
    """Storyboard üçün kadr (keşlənir). Orijinal fayla toxunmur — yalnız oxuyur."""
    import subprocess

    project = _load(pid)
    m = _media(project, mid)
    if not m.get("hasVideo"):
        raise HTTPException(404, "Mediada video yoxdur")
    t = max(0.0, min(float(t), float(m["duration"]) - 0.05))
    out = store.derived_dir(pid) / "frames" / f"{mid}_{int(round(t * 10))}.jpg"
    if not out.is_file():
        out.parent.mkdir(parents=True, exist_ok=True)
        src = store.project_dir(pid) / m["file"]
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(src), "-frames:v", "1",
             "-vf", "scale=320:-2", "-q:v", "5", str(out)],
            capture_output=True,
        )
        if not out.is_file():
            raise HTTPException(500, "Kadr çıxarılmadı")
    return FileResponse(out, media_type="image/jpeg", headers={"Cache-Control": "max-age=86400"})


def _clip_items(project: dict[str, Any], body: dict[str, Any]) -> list[dict[str, Any]]:
    """Təklif üçün uyğun kliplər: video kliplər + sərbəst danışıq klipləri, əl ilə olmayanlar."""
    kinds = track_kinds(project)
    only = set(body.get("clipIds") or [])
    res = []
    for c in project["clips"]:
        k = kinds.get(c["track"])
        if k == "video" or (k == "speech" and not c.get("linkedTo")):
            if only and c["id"] not in only:
                continue
            res.append(c)
    return res


def _proposal(kind: str, title: str, items: list[dict[str, Any]], skipped: list[dict[str, Any]],
              summary: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"id": "p_" + uuid.uuid4().hex[:10], "kind": kind, "title": title,
            "createdAt": time.time(), "items": items, "skippedManual": skipped,
            "summary": summary, **(extra or {})}


@app.post("/api/projects/{pid}/proposals/silence")
async def propose_silence(pid: str, request: Request) -> dict[str, Any]:
    body = await request.json() if await request.body() else {}
    project = _load(pid)
    noise = float(body.get("noiseDb", -35))
    min_sil = float(body.get("minSilence", 0.6))
    media = {m["id"]: m for m in project["media"]}
    items, skipped = [], []
    removed_total = 0.0
    for c in _clip_items(project, body):
        if c.get("manual"):
            skipped.append({"clipId": c["id"], "reason": "əl ilə düzəliş qorunur"})
            continue
        m = media[c["media"]]
        if not m.get("hasAudio"):
            continue
        src = store.project_dir(pid) / m["file"]
        sil = mediautil.detect_silence(src, c["srcIn"], c["srcOut"], noise, min_sil)
        keep = mediautil.keep_ranges(c["srcIn"], c["srcOut"], sil)
        kept = sum(b - a for a, b in keep)
        cut = (c["srcOut"] - c["srcIn"]) - kept
        if cut < 0.05:
            continue
        removed_total += cut
        items.append({"clipId": c["id"], "expect": {"srcIn": c["srcIn"], "srcOut": c["srcOut"]},
                      "keep": keep, "removed": [list(x) for x in sil], "removedSec": round(cut, 2)})
    summary = (f"{len(items)} klipdə cəmi {removed_total:.1f} san səssizlik silinməsi təklif olunur."
               if items else "Silinəcək səssiz hissə tapılmadı.")
    return _proposal("silence", "Səssiz hissələri çıxar", items, skipped, summary,
                     {"params": {"noiseDb": noise, "minSilence": min_sil}})


def _transcript_path(pid: str, mid: str) -> Path:
    return store.project_dir(pid) / "transcripts" / f"{mid}.json"


@app.post("/api/projects/{pid}/transcribe")
async def start_transcribe(pid: str, request: Request) -> dict[str, Any]:
    if not transcribe.available()["installed"]:
        raise HTTPException(503, "faster-whisper quraşdırılmayıb — transkripsiya işləmir")
    body = await request.json()
    project = _load(pid)
    m = _media(project, body.get("mediaId", ""))
    if not m.get("hasAudio"):
        raise HTTPException(400, "Bu mediada səs yoxdur")
    lang = body.get("language", "az") or None
    src = store.project_dir(pid) / m["file"]

    def work(progress: Callable[[float], None]) -> dict[str, Any]:
        progress(0.05)
        res = transcribe.transcribe(src, 0.0, float(m["duration"]), lang)
        res["mediaId"] = m["id"]
        out = _transcript_path(pid, m["id"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        return {"words": len(res["words"]), "language": res["language"]}

    return {"job": _job("transcribe", pid, work)}


@app.get("/api/projects/{pid}/transcripts/{mid}")
def get_transcript(pid: str, mid: str) -> FileResponse:
    _load(pid)
    f = _transcript_path(pid, mid)
    if not f.is_file():
        raise HTTPException(404, "Transkript yoxdur")
    return FileResponse(f, media_type="application/json")


@app.post("/api/projects/{pid}/proposals/fillers")
async def propose_fillers(pid: str, request: Request) -> dict[str, Any]:
    body = await request.json() if await request.body() else {}
    project = _load(pid)
    items, skipped = [], []
    words_cut = 0
    for c in _clip_items(project, body):
        if c.get("manual"):
            skipped.append({"clipId": c["id"], "reason": "əl ilə düzəliş qorunur"})
            continue
        f = _transcript_path(pid, c["media"])
        if not f.is_file():
            continue
        words = json.loads(f.read_text(encoding="utf-8"))["words"]
        inside = [w for w in words if w["s"] >= c["srcIn"] and w["e"] <= c["srcOut"]]
        rm = transcribe.filler_ranges(inside)
        if not rm:
            continue
        keep = mediautil.keep_ranges(c["srcIn"], c["srcOut"], rm, pad=0.0, min_keep=0.1)
        words_cut += len(rm)
        items.append({"clipId": c["id"], "expect": {"srcIn": c["srcIn"], "srcOut": c["srcOut"]},
                      "keep": keep, "removed": [list(x) for x in rm]})
    summary = (f"{words_cut} doldurucu söz (ee, ıı, hmm…) silinməsi təklif olunur."
               if items else "Transkriptdə doldurucu söz tapılmadı (və ya transkript yoxdur).")
    return _proposal("fillers", "Doldurucu sözləri çıxar", items, skipped, summary)


@app.post("/api/projects/{pid}/render")
async def start_render(pid: str, request: Request) -> dict[str, Any]:
    body = await request.json() if await request.body() else {}
    project = _load(pid)
    want = body.get("revision")
    if want is not None and int(want) != int(project.get("revision", 0)):
        raise HTTPException(409, "Son dəyişikliklər hələ saxlanmayıb — bir az gözləyib yenidən yoxlayın")
    if not layout(project):
        raise HTTPException(400, "Zaman xətti boşdur")
    rev = project.get("revision", 0)
    name = f"montaj_r{rev}_{time.strftime('%Y%m%d-%H%M%S')}.mp4"
    out = store.renders_dir(pid) / name
    snapshot = json.loads(json.dumps(project))

    def work(progress: Callable[[float], None]) -> dict[str, Any]:
        render(snapshot, store.project_dir(pid), out, progress)
        (out.with_suffix(".json")).write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")
        return {"file": name, "url": f"/api/projects/{pid}/renders/{name}", "revision": rev}

    return {"job": _job("render", pid, work)}


@app.get("/api/projects/{pid}/renders/{name}")
def get_render(pid: str, name: str) -> FileResponse:
    f = store.renders_dir(pid) / Path(name).name
    if not f.is_file() or f.suffix != ".mp4":
        raise HTTPException(404, "Render tapılmadı")
    return FileResponse(f, media_type="video/mp4", filename=f.name)


@app.get("/api/jobs/{jid}")
def job(jid: str) -> dict[str, Any]:
    j = _jobs.get(jid)
    if not j:
        raise HTTPException(404, "İş tapılmadı")
    return j
