"""Layihə saxlanması: projects/<id>/montaj.json + media/originals (dəyişməz).

Yazılar atomikdir; hər saxlamadan əvvəlki versiya `montaj_history/` qovluğunda
saxlanılır (son 30 versiya).
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any

from montaj.model import validate

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECTS_DIR = Path(os.environ.get("MONTAJ_PROJECTS_DIR", REPO_ROOT / "projects"))
PROJECT_FILE = "montaj.json"
HISTORY_KEEP = 30

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_lock = threading.Lock()


def projects_dir() -> Path:
    from montaj.config import projects_dir as _pd

    return _pd()


def check_id(pid: str) -> str:
    if not _ID_RE.match(pid or ""):
        raise ValueError("Layihə id-si yalnız kiçik hərf, rəqəm, '-' və '_' ola bilər")
    return pid


def project_dir(pid: str) -> Path:
    return projects_dir() / check_id(pid)


def originals_dir(pid: str) -> Path:
    return project_dir(pid) / "media" / "originals"


def derived_dir(pid: str) -> Path:
    return project_dir(pid) / "media" / "derived"


def renders_dir(pid: str) -> Path:
    return project_dir(pid) / "renders"


def slugify(title: str) -> str:
    tr = str.maketrans("əöüğışçƏÖÜĞİŞÇ", "eougiscEOUGISC")
    s = re.sub(r"[^a-z0-9]+", "-", title.translate(tr).lower()).strip("-")
    return (s or "layihe")[:40]


def _atomic_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    tmp.write_text(data, encoding="utf-8")
    os.replace(tmp, path)


def list_projects() -> list[dict[str, Any]]:
    out = []
    root = projects_dir()
    if not root.is_dir():
        return out
    for f in sorted(root.glob(f"*/{PROJECT_FILE}"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            p = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        out.append({
            "id": p.get("id"), "title": p.get("title"),
            "revision": p.get("revision", 0), "updatedAt": f.stat().st_mtime,
            "clips": len(p.get("clips", [])), "media": len(p.get("media", [])),
        })
    return out


def load(pid: str) -> dict[str, Any]:
    f = project_dir(pid) / PROJECT_FILE
    if not f.is_file():
        raise FileNotFoundError(pid)
    return json.loads(f.read_text(encoding="utf-8"))


def create(title: str, base: dict[str, Any]) -> dict[str, Any]:
    with _lock:
        stem = slugify(title)
        pid = stem
        n = 2
        while (projects_dir() / pid).exists():
            pid = f"{stem}-{n}"
            n += 1
        project = dict(base)
        project["id"] = pid
        project["title"] = title
        project["revision"] = 1
        project["savedAt"] = time.time()
        validate(project)
        originals_dir(pid).mkdir(parents=True, exist_ok=True)
        _atomic_write(project_dir(pid) / PROJECT_FILE, json.dumps(project, ensure_ascii=False, indent=1))
        return project


def save(pid: str, project: dict[str, Any], base_revision: int | None) -> dict[str, Any]:
    """Layihəni saxlayır; media siyahısını serverdəki həqiqətdən götürür."""
    with _lock:
        current = load(pid)
        if base_revision is not None and int(base_revision) != int(current.get("revision", 0)):
            raise RevisionConflict(current.get("revision", 0))
        project = dict(project)
        project["id"] = pid
        # Media qeydləri serverin probe nəticəsidir — müştəri dəyişə bilməz,
        # amma müştəri hələ görmədiyi media itməsin.
        server_media = {m["id"]: m for m in current.get("media", [])}
        client_ids = [m["id"] for m in project.get("media", []) if m.get("id") in server_media]
        rest = [mid for mid in server_media if mid not in client_ids]
        project["media"] = [server_media[mid] for mid in client_ids + rest]
        validate(project)
        hist = project_dir(pid) / "montaj_history"
        hist.mkdir(exist_ok=True)
        _atomic_write(hist / f"rev_{int(current.get('revision', 0)):06d}.json",
                      json.dumps(current, ensure_ascii=False))
        olds = sorted(hist.glob("rev_*.json"))
        for old in olds[:-HISTORY_KEEP]:
            old.unlink(missing_ok=True)
        project["revision"] = int(current.get("revision", 0)) + 1
        project["savedAt"] = time.time()
        _atomic_write(project_dir(pid) / PROJECT_FILE, json.dumps(project, ensure_ascii=False, indent=1))
        return project


def add_media_record(pid: str, record: dict[str, Any]) -> dict[str, Any]:
    with _lock:
        current = load(pid)
        current.setdefault("media", []).append(record)
        current["revision"] = int(current.get("revision", 0)) + 1
        _atomic_write(project_dir(pid) / PROJECT_FILE, json.dumps(current, ensure_ascii=False, indent=1))
        return current


def update_media_record(pid: str, media_id: str, patch: dict[str, Any]) -> None:
    with _lock:
        current = load(pid)
        for m in current.get("media", []):
            if m["id"] == media_id:
                m.update(patch)
        # revision artırılmır: bu, yalnız törəmə fayl statusudur
        _atomic_write(project_dir(pid) / PROJECT_FILE, json.dumps(current, ensure_ascii=False, indent=1))


class RevisionConflict(Exception):
    def __init__(self, current: int):
        super().__init__(f"Layihə başqa yerdə dəyişib (versiya {current})")
        self.current = current
