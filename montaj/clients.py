"""Müştəri profilləri. Məlum olmayan brend məlumatı boş qalır — uydurulmur."""

from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from montaj.config import data_dir
from montaj.errors import UserError

INITIAL_NAMES = [
    "Aynur Həkimova", "Aytən Cəlilova", "Günel Dəmirova", "Kənan Zərbiyev", "Lamiyə",
    "Murad Elxan", "Nərgiz Məmmədova", "Nilüfər Mehdiyeva", "Rəhimə Niyazlı", "Rəşad Rəşidov",
    "Səidə Əliyeva", "Sevinc Məhsimova", "Sura Malik", "Ülkər Rəşidova", "Xalidə Baycan",
    "Aynur Məmmədova", "Xəyyam Hüseynov",
]
FIELDS = ("name", "field", "colors", "font", "logo", "preferences")
_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
_lock = threading.Lock()


def _file() -> Path:
    return data_dir() / "clients.json"


def _blank(name: str) -> dict[str, Any]:
    return {"id": "cl_" + uuid.uuid4().hex[:8], "name": name, "field": "", "colors": [],
            "font": "", "logo": None, "preferences": "", "createdAt": time.time()}


def load_all() -> list[dict[str, Any]]:
    with _lock:
        f = _file()
        if not f.is_file():
            items = [_blank(n) for n in INITIAL_NAMES]
            _save(items)
            return items
        return json.loads(f.read_text(encoding="utf-8"))


def _save(items: list[dict[str, Any]]) -> None:
    f = _file()
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, f)


def clean(patch: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k in FIELDS:
        if k not in patch:
            continue
        v = patch[k]
        if k == "colors":
            cols = [c.strip() for c in (v or []) if isinstance(c, str) and c.strip()]
            bad = [c for c in cols if not _HEX.match(c)]
            if bad:
                raise UserError(f"Rəng kodu səhvdir: {bad[0]}", "Rəngi #RRGGBB formatında yazın, məsələn #1A2B3C.")
            out[k] = [c.upper() for c in cols][:8]
        elif k == "logo":
            out[k] = v if (v is None or isinstance(v, str)) else None
        else:
            out[k] = str(v or "").strip()[:500]
    if "name" in out and not out["name"]:
        raise UserError("Müştərinin adı boş ola bilməz.", "Ad yazın.")
    return out


def create(data: dict[str, Any]) -> dict[str, Any]:
    c = _blank("")
    c.update(clean(data))
    if not c["name"]:
        raise UserError("Müştərinin adı boş ola bilməz.", "Ad yazın.")
    items = load_all()
    with _lock:
        items.append(c)
        _save(items)
    return c


def update(cid: str, patch: dict[str, Any]) -> dict[str, Any]:
    items = load_all()
    with _lock:
        for c in items:
            if c["id"] == cid:
                c.update(clean(patch))
                c["updatedAt"] = time.time()
                _save(items)
                return c
    raise UserError("Müştəri tapılmadı.", "Siyahını yeniləyin.")


def get(cid: str) -> dict[str, Any] | None:
    return next((c for c in load_all() if c["id"] == cid), None)


def logos_dir() -> Path:
    d = data_dir() / "logos"
    d.mkdir(parents=True, exist_ok=True)
    return d
