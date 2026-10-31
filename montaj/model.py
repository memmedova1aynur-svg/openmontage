"""Layihə modelinin Python tərəfi: yoxlama və zaman xətti düzülüşü.

`montaj/ui/timeline.js` ilə eyni qaydaları izləyir (paritet testlə yoxlanılır):
video qatı maqnitlidir (`order`), bağlı səs videonun başlanğıcını götürür,
digər klipləri öz `start` vaxtı var.
"""

from __future__ import annotations

from typing import Any

TRACK_KINDS = {"video", "speech", "music", "sfx", "text"}
AUDIO_KINDS = {"speech", "music", "sfx"}
MIN_CLIP = 0.1


class ProjectError(ValueError):
    """Layihə məlumatı etibarsızdır (mesaj Azərbaycan dilindədir)."""


def _r(x: float) -> float:
    return round(x * 1000) / 1000


def track_kinds(project: dict[str, Any]) -> dict[str, str]:
    return {t["id"]: t["kind"] for t in project.get("tracks", [])}


def media_map(project: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {m["id"]: m for m in project.get("media", [])}


def clip_dur(c: dict[str, Any]) -> float:
    return float(c["srcOut"]) - float(c["srcIn"])


def video_clips(project: dict[str, Any]) -> list[dict[str, Any]]:
    kinds = track_kinds(project)
    vids = [c for c in project.get("clips", []) if kinds.get(c.get("track")) == "video"]
    return sorted(vids, key=lambda c: c.get("order", 0))


def layout(project: dict[str, Any]) -> dict[str, tuple[float, float]]:
    out: dict[str, tuple[float, float]] = {}
    t = 0.0
    for c in video_clips(project):
        out[c["id"]] = (_r(t), _r(t + clip_dur(c)))
        t += clip_dur(c)
    for c in project.get("clips", []):
        if c["id"] in out:
            continue
        link = c.get("linkedTo")
        if link and link in out:
            s = out[link][0]
        else:
            s = float(c.get("start") or 0)
        out[c["id"]] = (_r(s), _r(s + clip_dur(c)))
    return out


def duration(project: dict[str, Any]) -> float:
    lay = layout(project)
    return _r(max((e for _, e in lay.values()), default=0.0))


def validate(project: dict[str, Any]) -> None:
    """Etibarsız layihədə ProjectError atır."""
    if not isinstance(project, dict):
        raise ProjectError("Layihə obyekt olmalıdır")
    for key in ("id", "tracks", "media", "clips"):
        if key not in project:
            raise ProjectError(f"Layihədə '{key}' sahəsi yoxdur")
    kinds = track_kinds(project)
    if not set(kinds.values()) <= TRACK_KINDS:
        raise ProjectError("Naməlum qat növü")
    media = media_map(project)
    ids: set[str] = set()
    for c in project["clips"]:
        cid = c.get("id")
        if not cid or cid in ids:
            raise ProjectError("Klip id-si boş və ya təkrardır")
        ids.add(cid)
        kind = kinds.get(c.get("track"))
        if kind is None:
            raise ProjectError(f"Klip {cid}: naməlum qat")
        try:
            s_in, s_out = float(c["srcIn"]), float(c["srcOut"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ProjectError(f"Klip {cid}: srcIn/srcOut səhvdir") from exc
        if s_out - s_in < MIN_CLIP - 1e-6:
            raise ProjectError(f"Klip {cid}: müddət çox qısadır")
        if kind == "text":
            if not isinstance(c.get("text", ""), str):
                raise ProjectError(f"Klip {cid}: mətn səhvdir")
            continue
        m = media.get(c.get("media"))
        if m is None:
            raise ProjectError(f"Klip {cid}: media tapılmadı")
        if s_in < -1e-6 or s_out > float(m["duration"]) + 0.05:
            raise ProjectError(f"Klip {cid}: mənbə sərhədlərindən kənardadır")
        if kind == "video" and not m.get("hasVideo"):
            raise ProjectError(f"Klip {cid}: mediada video yoxdur")
        if kind in AUDIO_KINDS and not m.get("hasAudio"):
            raise ProjectError(f"Klip {cid}: mediada səs yoxdur")
    for c in project["clips"]:
        link = c.get("linkedTo")
        if link and link not in ids:
            raise ProjectError(f"Klip {c['id']}: bağlı video tapılmadı")
