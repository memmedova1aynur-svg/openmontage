"""Fərq yoxlayıcısı: storyboard variantları HƏQİQƏTƏN fərqlidirmi? Rəng/mətn fərqi sayılmır.

Hər plan öz dəstindən (`kit`) və oxlarından (`axes`) təsvir olunur: layout, form (yazı forması), caption, motion, card, density, hook.
Qayda: hər iki variant FƏRQLİ dəstdən olmalı və 7 oxdan ən azı 4-də fərqlənməlidir. Dəstsiz (köhnə) plan graphics növlərindən "classic" kimi
təxmin edilir. Təkrar əleyhinə yaddaş (`memory.py`) ilə birlikdə `variants` tərəfindən çağırılır.

  python -m montaj.difference A.json B.json C.json      # fərq yoxdursa çıxış kodu 1
"""

from __future__ import annotations

import itertools
import json
import sys
from typing import Any

AXES = ("layout", "form", "caption", "motion", "card", "density", "hook")
MIN_DIFF = 4
LEGACY = {"layout": "top-card", "form": "sans-card", "caption": "box", "motion": "pop", "card": "card", "density": "mid", "hook": "typography-card"}


def axes_of(plan: dict[str, Any]) -> dict[str, str]:
    if plan.get("axes"):
        return {**LEGACY, **plan["axes"]}
    a = dict(LEGACY)
    types = {g.get("type") for g in plan.get("graphics") or []}
    if plan.get("broll"):
        a.update(layout="cover-broll", density="high")
    if not types and not plan.get("broll"):
        a.update(card="none", density="low", form="captions-only")
    return a


def kit_of(plan: dict[str, Any]) -> str:
    return plan.get("kit") or "classic"


def check(plans: dict[str, dict[str, Any]], min_diff: int = MIN_DIFF) -> dict[str, Any]:
    """plans: {"A": plan, ...}. Qayıdır {"ok", "pairs": [{a,b,diff,same}], "problems": [..]}."""
    pairs, problems = [], []
    for (na, pa), (nb, pb) in itertools.combinations(plans.items(), 2):
        xa, xb = axes_of(pa), axes_of(pb)
        same = [k for k in AXES if xa.get(k) == xb.get(k)]
        diff = len(AXES) - len(same)
        pairs.append({"a": na, "b": nb, "diff": diff, "same": same})
        if kit_of(pa) == kit_of(pb):
            problems.append(f"{na} və {nb} eyni üslub dəstindədir ({kit_of(pa)})")
        elif diff < min_diff:
            problems.append(f"{na} və {nb} yalnız {diff}/{len(AXES)} oxda fərqlənir (≥{min_diff} olmalıdır; eyni: {', '.join(same)})")
    return {"ok": not problems, "pairs": pairs, "problems": problems}


def main(argv: list[str] | None = None) -> int:
    files = (argv if argv is not None else sys.argv[1:])
    if len(files) < 2:
        print("ən azı 2 plan faylı verin")
        return 2
    plans = {chr(65 + i): json.load(open(f, encoding="utf-8")) for i, f in enumerate(files)}
    rep = check(plans)
    for p in rep["pairs"]:
        print(f"{p['a']}–{p['b']}: {p['diff']}/{len(AXES)} ox fərqlənir (eyni: {', '.join(p['same']) or '—'})")
    for x in rep["problems"]:
        print("!", x)
    print("variantlar fərqlidir" if rep["ok"] else "variantlar çox oxşardır")
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
