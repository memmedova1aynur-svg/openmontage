"""Server işləri: diskdə saxlanılır, brauzer bağlansa da davam edir.

Server yenidən başlasa, yarımçıq iş "interrupted" olur və panel
"yenidən başlat" təklif edir.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable

from montaj import diag
from montaj.config import data_dir
from montaj.errors import UserError

_lock = threading.Lock()
_mem: dict[str, dict[str, Any]] = {}
MAX_PARALLEL = int(os.environ.get("MONTAJ_MAX_JOBS", "2"))
_sem = threading.Semaphore(MAX_PARALLEL)


def _dir() -> Path:
    d = data_dir() / "jobs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write(j: dict[str, Any]) -> None:
    f = _dir() / f"{j['id']}.json"
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(j, ensure_ascii=False))
    os.replace(tmp, f)


def recover() -> None:
    """Server açılanda: yarımçıq işləri 'interrupted' et."""
    for f in _dir().glob("*.json"):
        try:
            j = json.loads(f.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if j.get("status") in ("running", "queued"):
            j["status"] = "interrupted"
            j["error"] = "Server yenidən başladığı üçün iş dayandı."
            j["hint"] = "“Yenidən başlat” düyməsinə toxunun."
            _write(j)
        _mem[j["id"]] = j


def get(jid: str) -> dict[str, Any] | None:
    with _lock:
        if jid in _mem:
            return dict(_mem[jid])
    f = _dir() / f"{jid}.json"
    if f.is_file():
        return json.loads(f.read_text())
    return None


def for_project(pid: str, limit: int = 20) -> list[dict[str, Any]]:
    with _lock:
        js = [dict(j) for j in _mem.values() if j.get("project") == pid]
    js.sort(key=lambda j: j.get("createdAt", 0), reverse=True)
    return js[:limit]


def start(kind: str, pid: str, fn: Callable[[Callable[[float], None]], Any],
          params: dict[str, Any] | None = None, label: str = "") -> str:
    jid = uuid.uuid4().hex[:12]
    j = {"id": jid, "kind": kind, "project": pid, "status": "queued", "progress": 0.0,
         "createdAt": time.time(), "params": params or {}, "label": label}
    with _lock:
        _mem[jid] = j
    _write(j)

    def progress(x: float) -> None:
        with _lock:
            j["progress"] = round(max(0.0, min(1.0, x)), 3)
            snap = dict(j)
        if int(snap["progress"] * 100) % 5 == 0:
            _write(snap)

    def run() -> None:
        with _sem:
            with _lock:
                j["status"] = "running"
                j["startedAt"] = time.time()
            _write(j)
            try:
                res = fn(progress)
                with _lock:
                    j.update(status="done", progress=1.0, result=res, finishedAt=time.time())
            except UserError as e:
                diag.log("warn", f"iş {kind} uğursuz: {e.message}", job=jid, detail=e.detail)
                with _lock:
                    j.update(status="error", error=e.message, hint=e.hint, finishedAt=time.time())
            except Exception as e:  # noqa: BLE001
                diag.exception(f"iş {kind} xətası", job=jid)
                with _lock:
                    j.update(status="error", error="Gözlənilməz xəta baş verdi.",
                             hint="Yenidən cəhd edin. Təkrarlanarsa, Diaqnostika bölməsindəki qeydi göndərin.",
                             detail=str(e)[-500:], finishedAt=time.time())
            _write(j)

    threading.Thread(target=run, daemon=True).start()
    return jid
