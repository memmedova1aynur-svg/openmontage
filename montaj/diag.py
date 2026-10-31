"""Diaqnostika: texniki loglar istifadəçi axınından ayrı saxlanılır."""

from __future__ import annotations

import collections
import json
import threading
import time
import traceback
from typing import Any

from montaj.config import data_dir

_buf: collections.deque = collections.deque(maxlen=500)
_lock = threading.Lock()


def log(level: str, msg: str, **extra: Any) -> None:
    rec = {"t": time.time(), "level": level, "msg": msg[:4000], **{k: str(v)[:4000] for k, v in extra.items()}}
    with _lock:
        _buf.append(rec)
        try:
            with (data_dir() / "diag.log").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            pass


def exception(msg: str, **extra: Any) -> None:
    log("error", msg, trace=traceback.format_exc(), **extra)


def recent(n: int = 200) -> list[dict]:
    with _lock:
        return list(_buf)[-n:]
