"""Montaj paneli serveri (FastAPI).

Bütün emal (analiz, transkripsiya, kadraj, render) server işləridir: telefon
kilidlənsə və ya brauzer bağlansa da davam edir; vəziyyət diskdə saxlanılır.
Bütün API və media girişlə qorunur (auth.py).
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from montaj import ai, analysis, auth, clients, diag, drive, jobs, reframe, store, transcribe
from montaj import media as mediautil
from montaj.errors import UserError
from montaj.model import ProjectError, layout, track_kinds
from montaj.render import conversions, output_dims, render

UI_DIR = Path(__file__).resolve().parent / "ui"
MAX_UPLOAD = int(os.environ.get("MONTAJ_MAX_UPLOAD_MB", "4096")) * 1024 * 1024
PUBLIC_PATHS = {"/login", "/api/login", "/healthz", "/ui/login.css", "/ui/manifest.webmanifest", "/ui/icon.svg"}

app = FastAPI(title="Montaj paneli", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")
jobs.recover()


# ---------------------------------------------------------------------------
# Giriş və xəta formatı
# ---------------------------------------------------------------------------

@app.middleware("http")
async def guard(request: Request, call_next):
    path = request.url.path
    if auth.enabled() and path not in PUBLIC_PATHS:
        if not auth.configured():
            return JSONResponse({"error": "Serverdə giriş parolu təyin edilməyib.",
                                 "hint": "MONTAJ_PASSWORD mühit dəyişənini təyin edin (deploy/README.md)."}, status_code=503)
        if not auth.valid_token(request.cookies.get(auth.COOKIE)):
            if path.startswith("/api/"):
                return JSONResponse({"error": "Giriş tələb olunur.", "hint": "Yenidən daxil olun."}, status_code=401)
            return RedirectResponse("/login")
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    return resp


@app.exception_handler(UserError)
async def user_error(_: Request, e: UserError):
    return JSONResponse(e.to_dict(), status_code=400)


@app.exception_handler(HTTPException)
async def http_error(_: Request, e: HTTPException):
    return JSONResponse({"error": str(e.detail), "hint": ""}, status_code=e.status_code)


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {"ok": True}


@app.get("/login", response_class=HTMLResponse)
def login_page() -> HTMLResponse:
    return HTMLResponse((UI_DIR / "login.html").read_text(encoding="utf-8"), headers={"Cache-Control": "no-store"})


@app.post("/api/login")
async def login(request: Request) -> JSONResponse:
    ip = request.client.host if request.client else "?"
    if auth.rate_limited(ip):
        return JSONResponse({"error": "Çox sayda səhv cəhd.", "hint": "10 dəqiqə sonra yenidən yoxlayın."}, status_code=429)
    body = await request.json()
    if not auth.check_password(str(body.get("password", ""))):
        auth.record_fail(ip)
        return JSONResponse({"error": "Parol səhvdir.", "hint": "Yenidən yazın."}, status_code=401)
    resp = JSONResponse({"ok": True})
    resp.set_cookie(auth.COOKIE, auth.make_token(), max_age=auth.TTL, httponly=True,
                    secure=auth.cookie_secure(), samesite="lax")
    return resp


@app.post("/api/logout")
def logout() -> JSONResponse:
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(auth.COOKIE)
    return resp


# ---------------------------------------------------------------------------
# Köməkçilər
# ---------------------------------------------------------------------------

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


async def _json(request: Request) -> dict[str, Any]:
    raw = await request.body()
    return json.loads(raw) if raw else {}


def _project_logo(project: dict[str, Any], pid: str) -> Path | None:
    brand = project.get("brand") or {}
    name = brand.get("logo")
    if not name:
        return None
    p = (clients.logos_dir() / Path(name).name)
    return p if p.is_file() else None


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    html = (UI_DIR / "index.html").read_text(encoding="utf-8")
    for asset in ("app.css", "app.js", "flow.js"):
        f = UI_DIR / asset
        if f.is_file():
            html = html.replace(f"/ui/{asset}", f"/ui/{asset}?v={int(f.stat().st_mtime)}")
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


# ---------------------------------------------------------------------------
# Status və diaqnostika
# ---------------------------------------------------------------------------

_ai_check: dict[str, Any] = {}


@app.get("/api/status")
def status() -> dict[str, Any]:
    w = transcribe.available()
    return {
        "ffmpeg": mediautil.ffmpeg_available(),
        "transcription": {"available": w["installed"], "engine": "faster-whisper (yerli)", "model": w["model"],
                          "note": "Azərbaycan dilində söz kəsimlərinin keyfiyyəti real video ilə hələ təsdiqlənməyib."},
        "silence": {"available": mediautil.ffmpeg_available(), "engine": "ffmpeg silencedetect (yerli)"},
        "ai": {"keyPresent": ai.key_present(), "model": ai.MODEL, "check": _ai_check or None,
               "service": "Anthropic Claude API", "cost": ai.estimate_note()},
        "llm": {"available": ai.key_present(), "keyPresent": ai.key_present()},
        "drive": {"available": True, "note": "Yalnız “linki olan hər kəs” paylaşımlı tək fayllar."},
        "voiceover": {"available": False, "note": "Səsləndirmə xidməti qoşulmayıb (Azure az-AZ və ya ElevenLabs açarı lazımdır)."},
        "musicLibrary": {"available": False, "note": "Lisenziyası təsdiqlənmiş musiqi kitabxanası qoşulmayıb. Öz musiqinizi yükləyə bilərsiniz."},
        "faceModel": {"available": (reframe.models_dir() / "blaze_face_short_range.tflite").is_file()},
        "render": {"engine": "ffmpeg", "remotion": False},
        "auth": {"enabled": auth.enabled()},
    }


@app.post("/api/ai/check")
def ai_check() -> dict[str, Any]:
    res = ai.check_key()
    _ai_check.clear()
    _ai_check.update(res, at=time.time())
    return res


@app.get("/api/diag")
def diagnostics() -> dict[str, Any]:
    import platform

    def ver(cmd):
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout.splitlines()[0]
        except Exception:  # noqa: BLE001
            return None
    return {"logs": diag.recent(200), "python": platform.python_version(),
            "ffmpeg": ver(["ffmpeg", "-version"]), "dataDir": "(gizli)",
            "jobsRunning": sum(1 for j in jobs._mem.values() if j.get("status") == "running")}


# ---------------------------------------------------------------------------
# Müştərilər
# ---------------------------------------------------------------------------

@app.get("/api/clients")
def list_clients() -> list[dict[str, Any]]:
    return clients.load_all()


@app.post("/api/clients")
async def new_client(request: Request) -> dict[str, Any]:
    return clients.create(await _json(request))


@app.put("/api/clients/{cid}")
async def edit_client(cid: str, request: Request) -> dict[str, Any]:
    return clients.update(cid, await _json(request))


@app.post("/api/logos")
async def upload_logo(request: Request, name: str = "logo.png") -> dict[str, Any]:
    ext = Path(name).suffix.lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".svg"):
        raise UserError("Loqo PNG, JPG, WEBP və ya SVG olmalıdır.", "Şəffaf fonlu PNG tövsiyə olunur.")
    data = await request.body()
    if not data or len(data) > 10 * 1024 * 1024:
        raise UserError("Loqo faylı boşdur və ya 10 MB-dan böyükdür.", "Daha kiçik fayl seçin.")
    fname = "logo_" + uuid.uuid4().hex[:10] + (".png" if ext == ".svg" else ext)
    dst = clients.logos_dir() / fname
    if ext == ".svg":
        tmp = dst.with_suffix(".svg")
        tmp.write_bytes(data)
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp), str(dst)], capture_output=True)
        tmp.unlink(missing_ok=True)
        if r.returncode != 0:
            raise UserError("SVG loqo oxunmadı.", "Loqonu PNG kimi yükləyin.")
    else:
        dst.write_bytes(data)
    return {"logo": fname}


@app.get("/api/logos/{name}")
def get_logo(name: str) -> FileResponse:
    f = clients.logos_dir() / Path(name).name
    if not f.is_file():
        raise HTTPException(404, "Loqo tapılmadı")
    return FileResponse(f)


# ---------------------------------------------------------------------------
# Layihələr
# ---------------------------------------------------------------------------

@app.get("/api/projects")
def projects() -> list[dict[str, Any]]:
    return store.list_projects()


@app.post("/api/projects")
async def create_project(request: Request) -> dict[str, Any]:
    body = await _json(request)
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
    body = await _json(request)
    _load(pid)
    try:
        saved = store.save(pid, body["project"], body.get("baseRevision"))
    except store.RevisionConflict as exc:
        return JSONResponse({"error": str(exc), "revision": exc.current}, status_code=409)
    except (ProjectError, KeyError) as exc:
        raise HTTPException(400, str(exc)) from exc
    return JSONResponse({"revision": saved["revision"], "savedAt": saved["savedAt"], "media": saved["media"]})


@app.get("/api/projects/{pid}/jobs")
def project_jobs(pid: str) -> list[dict[str, Any]]:
    _load(pid)
    return [{k: v for k, v in j.items() if k != "detail"} for j in jobs.for_project(pid)]


@app.get("/api/jobs/{jid}")
def job(jid: str) -> dict[str, Any]:
    j = jobs.get(jid)
    if not j:
        raise HTTPException(404, "İş tapılmadı")
    return {k: v for k, v in j.items() if k != "detail"}


@app.post("/api/jobs/{jid}/retry")
def retry_job(jid: str) -> dict[str, Any]:
    j = jobs.get(jid)
    if not j or j.get("status") not in ("error", "interrupted"):
        raise UserError("Bu işi yenidən başlatmaq olmur.", "Əməliyyatı paneldən yenidən başladın.")
    starter = RETRY.get(j["kind"])
    if not starter:
        raise UserError("Bu iş növü üçün yenidən başlatma yoxdur.", "Əməliyyatı paneldən yenidən başladın.")
    return {"job": starter(j["project"], j.get("params") or {})}


# ---------------------------------------------------------------------------
# Media: yükləmə, Drive, önizləmə
# ---------------------------------------------------------------------------

def _derive(pid: str, mid: str) -> None:
    project = store.load(pid)
    m = next(m for m in project["media"] if m["id"] == mid)
    src = store.project_dir(pid) / m["file"]
    out = store.derived_dir(pid)
    patch: dict[str, Any] = {}
    try:
        if m.get("isImage"):
            mediautil.make_image_preview(src, out / f"{mid}.jpg")
            patch["preview"] = f"media/derived/{mid}.jpg"
        else:
            mediautil.make_proxy(src, out / f"{mid}.mp4", m["hasVideo"], m["hasAudio"], bool(m.get("hdr")))
            patch["preview"] = f"media/derived/{mid}.mp4"
    except Exception as exc:  # noqa: BLE001
        diag.exception("önizləmə nüsxəsi alınmadı", media=mid)
        patch["previewError"] = str(exc)[-300:]
    if m["hasAudio"]:
        try:
            (out / f"{mid}.peaks.json").write_text(json.dumps(mediautil.peaks(src)))
            patch["peaks"] = True
        except Exception:  # noqa: BLE001
            patch["peaks"] = False
    store.update_media_record(pid, mid, patch)


def _register(pid: str, tmp: Path, name: str, source: dict[str, Any] | None = None) -> dict[str, Any]:
    safe = "".join(ch for ch in Path(name).name if ch.isalnum() or ch in "._- ").strip() or "fayl"
    mid = "m_" + uuid.uuid4().hex[:10]
    ext = Path(safe).suffix.lower()[:8] or ".bin"
    dst = store.originals_dir(pid) / f"{mid}{ext}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp.replace(dst)
    os.chmod(dst, 0o444)  # orijinal yalnız oxunur
    try:
        info = mediautil.probe(dst)
    except Exception as exc:  # noqa: BLE001
        dst.unlink(missing_ok=True)
        raise UserError("Fayl oxunmadı — video, səs və ya şəkil deyil.",
                        "Başqa fayl seçin. iPhone-da “Ən uyğun” (Most Compatible) formatı ilə göndərmək kömək edə bilər.",
                        detail=str(exc)) from exc
    if not (info["hasVideo"] or info["hasAudio"]) or info["duration"] <= 0:
        dst.unlink(missing_ok=True)
        raise UserError("Faylda oynadıla bilən video/səs/şəkil tapılmadı.", "Başqa fayl seçin.")
    record = {"id": mid, "name": safe, "file": f"media/originals/{dst.name}", "size": dst.stat().st_size,
              "source": source or {"type": "upload"}, **info}
    project = store.add_media_record(pid, record)
    if os.environ.get("MONTAJ_SYNC_DERIVE"):
        _derive(pid, mid)
    else:
        threading.Thread(target=_derive, args=(pid, mid), daemon=True).start()
    return {"media": record, "revision": project["revision"]}


@app.post("/api/projects/{pid}/media")
async def upload_media(pid: str, request: Request, name: str = "fayl") -> dict[str, Any]:
    _load(pid)
    tmpdir = store.originals_dir(pid)
    tmpdir.mkdir(parents=True, exist_ok=True)
    tmp = tmpdir / f".up_{uuid.uuid4().hex[:8]}.part"
    size = 0
    with tmp.open("wb") as fh:
        async for chunk in request.stream():
            size += len(chunk)
            if size > MAX_UPLOAD:
                fh.close()
                tmp.unlink(missing_ok=True)
                raise UserError("Fayl çox böyükdür.", f"{MAX_UPLOAD // 1024**3} GB-dan kiçik fayl seçin.")
            fh.write(chunk)
    if size == 0:
        tmp.unlink(missing_ok=True)
        raise UserError("Fayl boşdur.", "Yükləməni təkrarlayın.")
    return _register(pid, tmp, name)


def _start_drive(pid: str, params: dict[str, Any]) -> str:
    link = params.get("link", "")
    drive.parse_link(link)  # dərhal yoxla — səhv link iş yaratmasın

    def work(progress):
        tmp, name = drive.download(link, store.originals_dir(pid), progress)
        return _register(pid, tmp, name, {"type": "drive", "id": drive.parse_link(link)["id"]})
    return jobs.start("drive", pid, work, params, label="Drive faylı")


@app.post("/api/projects/{pid}/drive")
async def drive_import(pid: str, request: Request) -> dict[str, Any]:
    _load(pid)
    body = await _json(request)
    return {"job": _start_drive(pid, {"link": body.get("link", "")})}


@app.get("/api/projects/{pid}/media/{mid}")
def media_file(pid: str, mid: str, preview: int = 0) -> FileResponse:
    project = _load(pid)
    m = _media(project, mid)
    root = store.project_dir(pid)
    rel = m.get("preview") if preview and m.get("preview") else m["file"]
    path = (root / rel).resolve()
    if root.resolve() not in path.parents or not path.is_file():
        raise HTTPException(404, "Fayl tapılmadı")
    media_type = "video/mp4" if rel.endswith(".mp4") else "image/jpeg" if rel.endswith(".jpg") else None
    return FileResponse(path, media_type=media_type, headers={"Cache-Control": "private, max-age=3600"})


@app.get("/api/projects/{pid}/media/{mid}/peaks")
def media_peaks(pid: str, mid: str) -> FileResponse:
    _load(pid)
    f = store.derived_dir(pid) / f"{mid}.peaks.json"
    if not f.is_file():
        raise HTTPException(404, "Dalğa forması hələ hazır deyil")
    return FileResponse(f, media_type="application/json")


@app.get("/api/projects/{pid}/media/{mid}/frame")
def media_frame(pid: str, mid: str, t: float = 0.0, w: int = 320) -> FileResponse:
    project = _load(pid)
    m = _media(project, mid)
    if not m.get("hasVideo"):
        raise HTTPException(404, "Mediada video yoxdur")
    w = 640 if w > 320 else 320
    t = 0.0 if m.get("isImage") else max(0.0, min(float(t), float(m["duration"]) - 0.05))
    out = store.derived_dir(pid) / "frames" / f"{mid}_{w}_{int(round(t * 10))}.jpg"
    if not out.is_file():
        out.parent.mkdir(parents=True, exist_ok=True)
        tm = "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p," if m.get("hdr") else ""
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(store.project_dir(pid) / m["file"]),
                        "-frames:v", "1", "-vf", f"{tm}scale={w}:-2", "-q:v", "5", str(out)], capture_output=True)
        if not out.is_file():
            raise HTTPException(500, "Kadr çıxarılmadı")
    return FileResponse(out, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=86400"})


# ---------------------------------------------------------------------------
# Analiz + storyboard (AI və ya qaydalar) — təsdiqə qədər montaja toxunmur
# ---------------------------------------------------------------------------

def _draft_path(pid: str) -> Path:
    return store.project_dir(pid) / "storyboard_draft.json"


def _brand(project: dict[str, Any]) -> dict[str, Any] | None:
    return project.get("brand")


def _segments(pid: str, project: dict[str, Any], options: dict[str, Any], progress=None) -> dict[str, list]:
    pdir = store.project_dir(pid)
    vis = [m for m in project["media"] if m.get("hasVideo") or m.get("hasAudio")]
    out: dict[str, list] = {}
    for i, m in enumerate(vis):
        an = analysis.analyze_media(pdir, m, options.get("language", "az"))
        out[m["id"]] = analysis.candidate_segments(m, an, options.get("cutMode", "suggest"))
        if progress:
            progress(0.1 + 0.5 * (i + 1) / max(1, len(vis)))
    return out


def _frames(pid: str, project: dict[str, Any], aspect: str, hint: str, progress=None) -> dict[str, Any]:
    if aspect in ("source", None, ""):
        return {}
    pdir = store.project_dir(pid)
    vids = [m for m in project["media"] if m.get("hasVideo")]
    first = next((m for m in vids if not m.get("isImage")), vids[0] if vids else None)
    _, out_h = reframe.output_size(first, aspect)
    res = {}
    for i, m in enumerate(vids):
        dur = 0.1 if m.get("isImage") else float(m["duration"])
        try:
            samples = reframe.detect_faces(pdir / m["file"], 0, dur, step=0.5 if dur < 120 else 1.0)
        except Exception:  # noqa: BLE001
            diag.exception("üz aşkarlanması alınmadı", media=m["id"])
            samples = []
        res[m["id"]] = reframe.suggest(m, 0, dur, aspect, out_h, samples, hint)
        if progress:
            progress(0.6 + 0.3 * (i + 1) / max(1, len(vids)))
    return res


def _start_storyboard(pid: str, params: dict[str, Any]) -> str:
    options = params.get("options") or {}

    def work(progress):
        project = store.load(pid)
        if not project["media"]:
            raise UserError("Layihədə material yoxdur.", "Əvvəl video və ya şəkil əlavə edin.")
        progress(0.05)
        segs = _segments(pid, project, options, progress)
        fmt = options.get("format") or []
        hint = "product" if "product" in fmt else "event" if "event" in fmt else ""
        frames = _frames(pid, project, options.get("aspect", "9:16"), hint, progress)
        progress(0.92)
        use_ai = options.get("useAi", True) and ai.key_present()
        if use_ai:
            sb = ai.ai_storyboard(store.project_dir(pid), project, segs, options, _brand(project))
        else:
            sb = analysis.rules_storyboard(project, segs, options)
        sb.update(id="sb_" + uuid.uuid4().hex[:8], createdAt=time.time(), options=options, frames=frames,
                  candidates={mid: s for mid, s in segs.items()}, status="draft",
                  removed={mid: analysis.removed_ranges(next(m for m in project["media"] if m["id"] == mid), [
                      c for c in sb["cards"] if c["mediaId"] == mid and c["include"]]) for mid in segs})
        _draft_path(pid).write_text(json.dumps(sb, ensure_ascii=False), encoding="utf-8")
        return {"storyboard": sb["id"], "generator": sb["generator"], "cards": len(sb["cards"])}
    return jobs.start("storyboard", pid, work, params, label="Storyboard")


@app.post("/api/projects/{pid}/storyboard")
async def make_storyboard(pid: str, request: Request) -> dict[str, Any]:
    _load(pid)
    body = await _json(request)
    return {"job": _start_storyboard(pid, {"options": body.get("options") or {}})}


@app.get("/api/projects/{pid}/storyboard/draft")
def get_draft(pid: str) -> dict[str, Any]:
    _load(pid)
    f = _draft_path(pid)
    if not f.is_file():
        raise HTTPException(404, "Storyboard hələ yoxdur")
    return json.loads(f.read_text(encoding="utf-8"))


def _rules_alternatives(card: dict[str, Any], cands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seq = sorted(cands, key=lambda s: s["srcIn"])
    idx = next((i for i, s in enumerate(seq) if s["id"] == card["segmentId"]), None)
    alts = []
    if idx is not None:
        cur = seq[idx]
        if idx > 0:
            p = seq[idx - 1]
            alts.append({"label": "Əvvəlki hissə ilə birlikdə", "srcIn": p["srcIn"], "srcOut": cur["srcOut"],
                         "transcript": (p["text"] + " " + cur["text"]).strip(), "words": p["words"] + cur["words"]})
        if idx + 1 < len(seq):
            n = seq[idx + 1]
            alts.append({"label": "Növbəti hissə ilə birlikdə", "srcIn": cur["srcIn"], "srcOut": n["srcOut"],
                         "transcript": (cur["text"] + " " + n["text"]).strip(), "words": cur["words"] + n["words"]})
        if cur["words"]:
            alts.append({"label": "Sıx kəsim (söz kənarlarına qədər)", "srcIn": round(max(0, cur["words"][0]["s"] - 0.06), 3),
                         "srcOut": round(cur["words"][-1]["e"] + 0.06, 3), "transcript": cur["text"], "words": cur["words"]})
    return alts


@app.post("/api/projects/{pid}/storyboard/card")
async def revise_card(pid: str, request: Request) -> dict[str, Any]:
    """Tək kartı dəyişir (bütün planı yenidən hazırlamır)."""
    project = _load(pid)
    body = await _json(request)
    sb = body.get("storyboard") or {}
    card = next((c for c in sb.get("cards", []) if c["id"] == body.get("cardId")), None)
    if not card:
        raise UserError("Kart tapılmadı.", "Storyboard-u yeniləyin.")
    cands = (sb.get("candidates") or {}).get(card["mediaId"], [])
    if not ai.key_present():
        return {"mode": "rules", "alternatives": _rules_alternatives(card, cands)}
    params = {"storyboard": sb, "cardId": card["id"], "instruction": body.get("instruction", ""),
              "alternative": bool(body.get("alternative"))}

    def work(progress):
        progress(0.1)
        return {"card": ai.ai_revise_card(store.project_dir(pid), project, sb, card, cands,
                                          params["instruction"], params["alternative"], sb.get("options") or {},
                                          _brand(project))}
    return {"mode": "ai", "job": jobs.start("card", pid, work, {}, label="Kart")}


# ---------------------------------------------------------------------------
# Kadraj (tək klip üçün yenidən təklif)
# ---------------------------------------------------------------------------

@app.post("/api/projects/{pid}/reframe")
async def reframe_clip(pid: str, request: Request) -> dict[str, Any]:
    project = _load(pid)
    body = await _json(request)
    m = _media(project, body.get("mediaId", ""))
    aspect = body.get("aspect", "9:16")
    if aspect not in reframe.ASPECTS:
        raise UserError("Naməlum format.", "9:16, 4:5, 1:1 və ya 16:9 seçin.")
    params = {"mediaId": m["id"], "aspect": aspect, "srcIn": float(body.get("srcIn", 0)),
              "srcOut": float(body.get("srcOut", m["duration"]))}

    def work(progress):
        first = next((x for x in project["media"] if x.get("hasVideo") and not x.get("isImage")), m)
        _, out_h = reframe.output_size(first, aspect)
        samples = reframe.detect_faces(store.project_dir(pid) / m["file"], params["srcIn"],
                                       params["srcOut"] if not m.get("isImage") else 0.1)
        progress(0.8)
        return {"frame": reframe.suggest(m, params["srcIn"], params["srcOut"], aspect, out_h, samples, body.get("hint", ""))}
    return {"job": jobs.start("reframe", pid, work, params, label="Kadraj")}


@app.get("/api/projects/{pid}/output-size")
def out_size(pid: str, aspect: str = "9:16") -> dict[str, Any]:
    project = _load(pid)
    first = next((m for m in project["media"] if m.get("hasVideo") and not m.get("isImage")),
                 next((m for m in project["media"] if m.get("hasVideo")), None))
    w, h = reframe.output_size(first, aspect if aspect in reframe.ASPECTS else "source")
    return {"width": w, "height": h}


# ---------------------------------------------------------------------------
# Köhnə təklif marşrutları (redaktordakı “Təkliflər” bölməsi)
# ---------------------------------------------------------------------------

def _clip_items(project: dict[str, Any], body: dict[str, Any]) -> list[dict[str, Any]]:
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


def _proposal(kind, title, items, skipped, summary, extra=None):
    return {"id": "p_" + uuid.uuid4().hex[:10], "kind": kind, "title": title, "createdAt": time.time(),
            "items": items, "skippedManual": skipped, "summary": summary, **(extra or {})}


@app.post("/api/projects/{pid}/proposals/silence")
async def propose_silence(pid: str, request: Request) -> dict[str, Any]:
    body = await _json(request)
    project = _load(pid)
    noise, min_sil = float(body.get("noiseDb", -35)), float(body.get("minSilence", 1.2))
    media = {m["id"]: m for m in project["media"]}
    items, skipped, total = [], [], 0.0
    for c in _clip_items(project, body):
        if c.get("manual"):
            skipped.append({"clipId": c["id"], "reason": "əl ilə düzəliş qorunur"})
            continue
        m = media[c["media"]]
        if not m.get("hasAudio"):
            continue
        sil = mediautil.detect_silence(store.project_dir(pid) / m["file"], c["srcIn"], c["srcOut"], noise, min_sil)
        keep = mediautil.keep_ranges(c["srcIn"], c["srcOut"], sil, pad=0.25)
        cut = (c["srcOut"] - c["srcIn"]) - sum(b - a for a, b in keep)
        if cut < 0.05:
            continue
        total += cut
        items.append({"clipId": c["id"], "expect": {"srcIn": c["srcIn"], "srcOut": c["srcOut"]}, "keep": keep,
                      "removed": [list(x) for x in sil], "removedSec": round(cut, 2)})
    summary = (f"{len(items)} klipdə cəmi {total:.1f} san uzun səssizlik." if items else "Uzun səssizlik tapılmadı.")
    return _proposal("silence", "Uzun səssizlikləri çıxar", items, skipped, summary,
                     {"params": {"noiseDb": noise, "minSilence": min_sil}})


def _transcript_path(pid: str, mid: str) -> Path:
    return store.project_dir(pid) / "transcripts" / f"{mid}.json"


@app.post("/api/projects/{pid}/transcribe")
async def start_transcribe(pid: str, request: Request) -> dict[str, Any]:
    if not transcribe.available()["installed"]:
        raise UserError("Transkripsiya modulu quraşdırılmayıb.", "Serverdə faster-whisper quraşdırın.")
    body = await _json(request)
    project = _load(pid)
    m = _media(project, body.get("mediaId", ""))
    if not m.get("hasAudio"):
        raise UserError("Bu mediada səs yoxdur.", "Səsli fayl seçin.")
    lang = body.get("language", "az") or None

    def work(progress):
        progress(0.05)
        res = transcribe.transcribe(store.project_dir(pid) / m["file"], 0.0, float(m["duration"]), lang)
        res["mediaId"] = m["id"]
        out = _transcript_path(pid, m["id"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        return {"words": len(res["words"]), "language": res["language"]}
    return {"job": jobs.start("transcribe", pid, work, {"mediaId": m["id"]}, label="Transkripsiya")}


@app.get("/api/projects/{pid}/transcripts/{mid}")
def get_transcript(pid: str, mid: str) -> FileResponse:
    _load(pid)
    f = _transcript_path(pid, mid)
    if not f.is_file():
        an = analysis.analysis_path(store.project_dir(pid), mid)
        if an.is_file() and json.loads(an.read_text()).get("transcribed"):
            return FileResponse(an, media_type="application/json")
        raise HTTPException(404, "Transkript yoxdur")
    return FileResponse(f, media_type="application/json")


@app.post("/api/projects/{pid}/proposals/fillers")
async def propose_fillers(pid: str, request: Request) -> dict[str, Any]:
    body = await _json(request)
    project = _load(pid)
    items, skipped, n = [], [], 0
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
        n += len(rm)
        items.append({"clipId": c["id"], "expect": {"srcIn": c["srcIn"], "srcOut": c["srcOut"]}, "keep": keep,
                      "removed": [list(x) for x in rm]})
    summary = f"{n} doldurucu söz (ee, ıı, hmm…)." if items else "Doldurucu söz tapılmadı (və ya transkript yoxdur)."
    return _proposal("fillers", "Doldurucu sözləri çıxar", items, skipped, summary)


# ---------------------------------------------------------------------------
# Caption
# ---------------------------------------------------------------------------

def _edited_transcript(pid: str, project: dict[str, Any]) -> str:
    pdir = store.project_dir(pid)
    parts = []
    kinds = track_kinds(project)
    lay = layout(project)
    for c in sorted([c for c in project["clips"] if kinds.get(c["track"]) == "video"], key=lambda c: lay[c["id"]][0]):
        an = analysis.analysis_path(pdir, c["media"])
        if not an.is_file():
            an = _transcript_path(pid, c["media"])
        if not an.is_file():
            continue
        words = json.loads(an.read_text(encoding="utf-8")).get("words", [])
        parts.append(" ".join(w["w"] for w in words if w["s"] >= c["srcIn"] - 0.05 and w["e"] <= c["srcOut"] + 0.05))
    return " ".join(p for p in parts if p).strip()


@app.post("/api/projects/{pid}/caption")
def caption(pid: str) -> dict[str, Any]:
    project = _load(pid)
    if not ai.key_present():
        raise UserError("Caption üçün AI bağlantısı qurulmayıb.", "Serverdə ANTHROPIC_API_KEY təyin edin və ya caption-u özünüz yazın.")
    text = _edited_transcript(pid, project)
    onscreen = [c.get("text", "") for c in project["clips"] if track_kinds(project).get(c["track"]) == "text" and c["track"] == "t1"]

    def work(progress):
        progress(0.1)
        return ai.ai_caption(text, project.get("options") or {}, _brand(project), onscreen)
    return {"job": jobs.start("caption", pid, work, {}, label="Caption")}


# ---------------------------------------------------------------------------
# Render və paylaşma
# ---------------------------------------------------------------------------

def _start_render(pid: str, params: dict[str, Any]) -> str:
    project = _load(pid)
    want = params.get("revision")
    if want is not None and int(want) != int(project.get("revision", 0)):
        raise HTTPException(409, "Son dəyişikliklər hələ saxlanmayıb — bir az gözləyib yenidən yoxlayın")
    if not layout(project):
        raise UserError("Zaman xətti boşdur.", "Əvvəl montajı təsdiqləyin və ya klip əlavə edin.")
    rev = project.get("revision", 0)
    name = f"montaj_r{rev}_{time.strftime('%Y%m%d-%H%M%S')}.mp4"
    out = store.renders_dir(pid) / name
    snapshot = json.loads(json.dumps(project))
    logo = _project_logo(project, pid)

    def work(progress):
        render(snapshot, store.project_dir(pid), out, progress, logo_path=logo)
        out.with_suffix(".json").write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")
        return {"file": name, "url": f"/api/projects/{pid}/renders/{name}", "revision": rev,
                "size": out.stat().st_size}
    return jobs.start("render", pid, work, {"revision": None}, label="MP4")


RETRY = {"render": _start_render, "storyboard": _start_storyboard, "drive": _start_drive}


@app.post("/api/projects/{pid}/render")
async def start_render(pid: str, request: Request) -> dict[str, Any]:
    body = await _json(request)
    return {"job": _start_render(pid, {"revision": body.get("revision")})}


@app.get("/api/projects/{pid}/conversions")
def get_conversions(pid: str) -> dict[str, Any]:
    project = _load(pid)
    w, h = output_dims(project)
    return {"width": w, "height": h, "items": conversions(project)}


@app.get("/api/projects/{pid}/renders")
def list_renders(pid: str) -> list[dict[str, Any]]:
    _load(pid)
    d = store.renders_dir(pid)
    if not d.is_dir():
        return []
    return [{"file": f.name, "url": f"/api/projects/{pid}/renders/{f.name}", "size": f.stat().st_size,
             "createdAt": f.stat().st_mtime}
            for f in sorted(d.glob("montaj_*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True)]


@app.get("/api/projects/{pid}/renders/{name}")
def get_render(pid: str, name: str, download: int = 0) -> FileResponse:
    f = store.renders_dir(pid) / Path(name).name
    if not f.is_file() or f.suffix != ".mp4":
        raise HTTPException(404, "Render tapılmadı")
    return FileResponse(f, media_type="video/mp4", filename=f.name if download else None)


@app.get("/api/projects/{pid}/renders/{name}/cover")
def render_cover(pid: str, name: str, t: float = 0.0) -> FileResponse:
    f = store.renders_dir(pid) / Path(name).name
    if not f.is_file():
        raise HTTPException(404, "Render tapılmadı")
    out = store.renders_dir(pid) / "covers" / f"{f.stem}_{int(t * 10)}.jpg"
    if not out.is_file():
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{max(0, t):.2f}", "-i", str(f), "-frames:v", "1",
                        "-q:v", "2", str(out)], capture_output=True)
        if not out.is_file():
            raise HTTPException(500, "Cover çıxarılmadı")
    return FileResponse(out, media_type="image/jpeg", filename=out.name)
