#!/usr/bin/env python3
"""Openverse SFX: search and download Creative Commons sound effects.

Openverse (https://openverse.org) indexes ~1M+ openly licensed audio records
(Freesound, Wikimedia Commons, Jamendo, ...). Anonymous API access needs no key.

Usage:
  openverse_sfx.py search "whoosh" [--n 10] [--license commercial|modification|all]
                                   [--max-sec 5] [--source freesound]
  openverse_sfx.py get "whoosh" --type whoosh [--n 3] --lib assets/sfx
  openverse_sfx.py get --id <openverse-id> --type hit --lib assets/sfx

`get` saves files as <lib>/<type>/<slug>__<id8>.<ext>, appends attribution to
<lib>/CREDITS.md and records every file in <lib>/openverse_manifest.json, so the
real-sfx placer can pick them up by type.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

API = os.environ.get("OPENVERSE_API", "https://api.openverse.org/v1")
UA = "openmontage-sfx/1.0 (+https://openverse.org)"
# CC0 / PDM need no credit; BY / BY-SA need credit; NC / ND are excluded by default.
LICENSE_TYPES = {"commercial": "commercial", "modification": "commercial,modification", "all": ""}


def _get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    token = os.environ.get("OPENVERSE_TOKEN")  # optional, for higher rate limits
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def search(q: str, n: int = 10, license: str = "commercial", max_sec: float | None = 5.0,
           source: str | None = None, category: str = "sound_effect") -> list[dict]:
    params = {"q": q, "page_size": str(min(max(n * 3, 10), 50)), "mature": "false"}
    if category:
        params["category"] = category
    lt = LICENSE_TYPES.get(license, "commercial")
    if lt:
        params["license_type"] = lt
    if source:
        params["source"] = source
    if max_sec is not None:
        # Openverse length buckets: shortest (<30s), short (30s-2m), medium, long
        params["length"] = "shortest"
    data = json.loads(_get(f"{API}/audio/?{urllib.parse.urlencode(params)}"))
    out = []
    for r in data.get("results", []):
        dur = (r.get("duration") or 0) / 1000.0
        if max_sec is not None and dur and dur > max_sec:
            continue
        out.append(r)
        if len(out) >= n:
            break
    return out


def record(rid: str) -> dict:
    return json.loads(_get(f"{API}/audio/{rid}/"))


def attribution(r: dict) -> str:
    if r.get("attribution"):
        return r["attribution"]
    lic = f"{(r.get('license') or '').upper()} {r.get('license_version') or ''}".strip()
    return f"\"{r.get('title')}\" by {r.get('creator') or 'unknown'} ({lic}) {r.get('foreign_landing_url') or ''}"


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "sound").lower()).strip("-")[:40] or "sound"


def download(r: dict, lib: Path, sfx_type: str) -> Path:
    url = r.get("url")
    if not url:
        raise RuntimeError(f"record {r.get('id')} has no file url")
    ext = (r.get("filetype") or Path(urllib.parse.urlparse(url).path).suffix.lstrip(".") or "mp3").lower()
    d = lib / sfx_type
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{_slug(r.get('title'))}__{str(r['id'])[:8]}.{ext}"
    if not path.exists():
        path.write_bytes(_get(url, timeout=120))
    # manifest
    mf = lib / "openverse_manifest.json"
    items = json.loads(mf.read_text()) if mf.exists() else []
    items = [i for i in items if i.get("id") != r["id"]]
    items.append({
        "id": r["id"], "file": str(path.relative_to(lib)), "type": sfx_type, "title": r.get("title"),
        "creator": r.get("creator"), "license": r.get("license"), "license_version": r.get("license_version"),
        "source": r.get("source"), "landing_url": r.get("foreign_landing_url"),
        "attribution": attribution(r), "duration_s": (r.get("duration") or 0) / 1000.0,
    })
    mf.write_text(json.dumps(items, indent=2, ensure_ascii=False))
    credits = lib / "CREDITS.md"
    line = f"- `{path.relative_to(lib)}` — {attribution(r)}\n"
    existing = credits.read_text() if credits.exists() else "# Sound credits (Openverse)\n\n"
    if line not in existing:
        credits.write_text(existing + line)
    return path


def _row(r: dict) -> str:
    dur = (r.get("duration") or 0) / 1000.0
    lic = f"{r.get('license')} {r.get('license_version') or ''}".strip()
    return f"{r['id']}  {dur:5.1f}s  {lic:<10} {r.get('source', ''):<12} {(r.get('title') or '')[:50]}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("search", "get"):
        p = sub.add_parser(name)
        p.add_argument("query", nargs="?")
        p.add_argument("--n", type=int, default=10 if name == "search" else 3)
        p.add_argument("--license", choices=list(LICENSE_TYPES), default="commercial")
        p.add_argument("--max-sec", type=float, default=5.0, help="max duration; 0 = no limit")
        p.add_argument("--source", help="e.g. freesound, wikimedia_audio")
        p.add_argument("--any-category", action="store_true", help="do not restrict to sound_effect")
        p.add_argument("--json", action="store_true")
        if name == "get":
            p.add_argument("--id", action="append", help="download specific Openverse id(s)")
            p.add_argument("--type", required=True, help="library folder, e.g. whoosh, hit, click, pop")
            p.add_argument("--lib", default="assets/sfx")
    a = ap.parse_args(argv)
    max_sec = a.max_sec or None
    cat = "" if a.any_category else "sound_effect"
    try:
        if a.cmd == "search" or not getattr(a, "id", None):
            if not a.query:
                ap.error("query required")
            rs = search(a.query, a.n, a.license, max_sec, a.source, cat)
        else:
            rs = [record(i) for i in a.id]
    except Exception as e:  # network / HTTP
        print(f"openverse error: {e}\nIf api.openverse.org is blocked, use the earshot skill to "
              f"generate the sound instead.", file=sys.stderr)
        return 2
    if a.cmd == "search":
        if a.json:
            print(json.dumps(rs, indent=2, ensure_ascii=False))
        else:
            for r in rs:
                print(_row(r))
            if not rs:
                print("no results (try --any-category, --license all, --max-sec 0, or other words)")
        return 0
    lib = Path(a.lib)
    for r in rs:
        try:
            print(f"saved {download(r, lib, a.type)}  [{r.get('license')}]")
        except Exception as e:
            print(f"skip {r.get('id')}: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
