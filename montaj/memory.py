"""Təkrar əleyhinə yaddaş: müştərinin son üslub dəstləri, təsdiq edilənlər və rədd edilənlər (profildə `history`, `approved`, `rejected`).

Qayda: son 2 videoda işlənmiş dəst təkrar təklif olunmur; rədd edilmiş dəst (istifadəçi `--rejected` ilə qeyd edibsə) təklif olunmur.
Yalnız İSTİFADƏÇİNİN təsdiqlədiyi/rədd etdiyi qərarlar yazılır (`choose --remember [--rejected ...]`); fərziyyə daimi qayda olmur.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from montaj import difference, kits

GLOBAL = Path(__file__).resolve().parent / "kit_decisions.json"  # istifadəçinin ÜMUMİ qərarları (müştəridən asılı olmayaraq)


def global_decisions() -> dict[str, dict[str, str]]:
    try:
        d = json.loads(GLOBAL.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"liked": {}, "rejected": {}}
    return {"liked": d.get("liked") or {}, "rejected": d.get("rejected") or {}}

RECENT_N = 2


def _hist(profile: dict[str, Any] | None) -> list[dict[str, Any]]:
    return [h for h in ((profile or {}).get("history") or []) if isinstance(h, dict)]


def recent_kits(profile: dict[str, Any] | None, n: int = RECENT_N) -> list[str]:
    ks = [h["kit"] for h in _hist(profile) if h.get("kit")]
    return ks[-n:]


def rejected_kits(profile: dict[str, Any] | None) -> list[str]:
    return [r["kit"] if isinstance(r, dict) else str(r) for r in ((profile or {}).get("rejected") or [])]


def blocked(profile: dict[str, Any] | None) -> dict[str, str]:
    out = {k: f"son {RECENT_N} videoda işlənib" for k in recent_kits(profile)}
    out.update({k: "istifadəçi rədd edib" for k in rejected_kits(profile)})
    out.update({k: "istifadəçi ümumiyyətlə bəyənməyib" for k in global_decisions()["rejected"]})
    return out


def suggest(profile: dict[str, Any] | None, n: int = 3, tags: list[str] | None = None) -> list[str]:
    """n dəst: bloklananlar xaric, bir-birindən oxlar üzrə ən uzaq (xəsis seçim); mövzu teqlərinə uyğun olan üstün."""
    bl = blocked(profile)
    liked = global_decisions()["liked"]
    pool = [k for k in kits.KITS if k not in bl]
    tags = [t.lower() for t in tags or []]
    score = lambda k: sum(any(t in s.lower() for s in kits.KITS[k]["suits"]) for t in tags) + (2 if k in liked else 0)  # noqa: E731
    pool.sort(key=lambda k: (-score(k), k))
    chosen: list[str] = []
    while pool and len(chosen) < n:
        if not chosen:
            chosen.append(pool.pop(0))
            continue
        far = lambda k: min(sum(kits.KITS[k]["axes"].get(a) != kits.KITS[c]["axes"].get(a) for a in difference.AXES) for c in chosen)  # noqa: E731
        best = max(pool, key=lambda k: (far(k), score(k)))
        pool.remove(best)
        chosen.append(best)
    return chosen


def check_plans(profile: dict[str, Any] | None, plans: dict[str, dict[str, Any]]) -> list[str]:
    """Planlardakı dəstlər müştəri yaddaşına zidd gəlirmi (son istifadə olunan / rədd edilən)."""
    bl = blocked(profile)
    return [f"{name}: “{difference.kit_of(p)}” dəsti {bl[difference.kit_of(p)]} — başqa dəst seç"
            for name, p in plans.items() if difference.kit_of(p) in bl and difference.kit_of(p) != "classic"]


def apply(profile: dict[str, Any], entry: dict[str, Any], rejected: list[str] | None, date: str) -> None:
    """Təsdiqlənmiş seçimi profilə yazır: history (artıq entry), approved, rejected."""
    if entry.get("kit"):
        profile.setdefault("approved", []).append({"kit": entry["kit"], "video": entry.get("video"), "date": date})
    for k in rejected or []:
        if k and k not in rejected_kits(profile):
            profile.setdefault("rejected", []).append({"kit": k, "video": entry.get("video"), "date": date})
