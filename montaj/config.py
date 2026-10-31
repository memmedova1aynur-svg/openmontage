"""Yollar və mühit parametrləri.

MONTAJ_DATA_DIR     — daimi məlumat qovluğu (Docker volume). Susmaya görə repo/projects-ın valideyni.
MONTAJ_PROJECTS_DIR — layihələr (susmaya görə $MONTAJ_DATA_DIR/projects və ya repo/projects).
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    d = os.environ.get("MONTAJ_DATA_DIR")
    p = Path(d) if d else REPO_ROOT / ".montaj"
    p.mkdir(parents=True, exist_ok=True)
    return p


def projects_dir() -> Path:
    d = os.environ.get("MONTAJ_PROJECTS_DIR")
    if d:
        return Path(d)
    if os.environ.get("MONTAJ_DATA_DIR"):
        return data_dir() / "projects"
    return REPO_ROOT / "projects"


def models_dir() -> Path:
    p = data_dir() / "models"
    p.mkdir(parents=True, exist_ok=True)
    return p
