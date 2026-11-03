"""Hazır video və şəkil axtarışı (B-roll, seçim kartları üçün) — yalnız pulsuz və müəllif qeydi TƏLƏB ETMƏYƏN lisenziyalar.

Mənbələr (bu mühitin şəbəkəsində işləyənlər):
  mixkit    — video; Mixkit Stock Video Free License (kommersiya, qeyd tələb etmir); açar lazım deyil
  pixabay   — video və şəkil; Pixabay Content License (kommersiya, qeyd tələb etmir); PIXABAY_API_KEY (pulsuz) lazımdır
  wikimedia — şəkil; yalnız CC0 / Public domain (CC BY, CC BY-SA müəllif qeydi tələb edir — seçilmir)
Pexels və Openverse bu mühitdə bağlıdır. Sorğu ingiliscə daha yaxşı işləyir (məs. "breastfeeding", "baby bottle").
Hər faylın mənbəyi və lisenziyası `manifest.json`-a yazılır; müştəri reklamında lisenziyanı yoxla.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

UA = {"User-Agent": "Mozilla/5.0 (montaj stock search)"}
MIXKIT_LICENSE = "Mixkit Stock Video Free License (kommersiya istifadəsi pulsuz, müəllif qeydi tələb etmir)"
PIXABAY_LICENSE = "Pixabay Content License (kommersiya istifadəsi pulsuz, müəllif qeydi tələb etmir)"
FREE_WIKI = ("cc0", "public domain", "pd", "pdm")


def _get(url: str, timeout: int = 30) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def mixkit(query: str, n: int = 8) -> list[dict[str, Any]]:
    slug = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")
    html = _get(f"https://mixkit.co/free-stock-video/{slug}/").decode("utf-8", "ignore")
    ids = list(dict.fromkeys(re.findall(r"assets\.mixkit\.co/videos/(\d+)/\1-", html)))
    out = []
    for vid in ids[:n]:
        res = [int(r) for r in re.findall(rf"assets\.mixkit\.co/videos/{vid}/{vid}-(\d+)\.mp4", html)]
        best = max([r for r in res if r <= 1080] or res or [720])
        out.append({"source": "mixkit", "id": vid, "kind": "video", "url": f"https://assets.mixkit.co/videos/{vid}/{vid}-{best}.mp4",
                    "thumb": f"https://assets.mixkit.co/videos/{vid}/{vid}-thumb-360-0.jpg", "page": f"https://mixkit.co/free-stock-video/{slug}/",
                    "license": MIXKIT_LICENSE})
    return out


def pixabay(query: str, kind: str = "image", n: int = 8) -> list[dict[str, Any]]:
    key = os.environ.get("PIXABAY_API_KEY")
    if not key:
        return []
    q = urllib.parse.quote(query)
    if kind == "video":
        d = json.loads(_get(f"https://pixabay.com/api/videos/?key={key}&q={q}&per_page={max(3, n)}&safesearch=true"))
        out = []
        for h in d.get("hits", [])[:n]:
            v = h.get("videos", {})
            best = v.get("large") or v.get("medium") or v.get("small") or {}
            if best.get("url"):
                out.append({"source": "pixabay", "id": str(h["id"]), "kind": "video", "url": best["url"],
                            "thumb": best.get("thumbnail") or "", "page": h.get("pageURL", ""), "license": PIXABAY_LICENSE})
        return out
    d = json.loads(_get(f"https://pixabay.com/api/?key={key}&q={q}&image_type=photo&per_page={max(3, n)}&safesearch=true"))
    return [{"source": "pixabay", "id": str(h["id"]), "kind": "image", "url": h.get("largeImageURL") or h.get("webformatURL"),
             "thumb": h.get("previewURL", ""), "page": h.get("pageURL", ""), "license": PIXABAY_LICENSE} for h in d.get("hits", [])[:n]]


def wikimedia(query: str, n: int = 8) -> list[dict[str, Any]]:
    q = urllib.parse.quote(query)
    d = json.loads(_get("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrnamespace=6"
                        f"&gsrsearch={q}%20filetype:bitmap&gsrlimit=40&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=1280"))
    out = []
    for p in (d.get("query") or {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        lic = ((ii.get("extmetadata") or {}).get("LicenseShortName") or {}).get("value", "")
        if not any(lic.lower().startswith(x) for x in FREE_WIKI):
            continue  # müəllif qeydi tələb edən lisenziyalar seçilmir
        out.append({"source": "wikimedia", "id": str(p.get("pageid")), "kind": "image", "url": ii.get("thumburl") or ii.get("url"),
                    "thumb": ii.get("thumburl") or "", "page": ii.get("descriptionurl", ""), "license": f"{lic} (Wikimedia Commons)",
                    "title": p.get("title", "")})
        if len(out) >= n:
            break
    return out


def search(query: str, kind: str = "video", n: int = 8, source: str | None = None) -> list[dict[str, Any]]:
    srcs = [source] if source else (["mixkit", "pixabay"] if kind == "video" else ["pixabay", "wikimedia"])
    out: list[dict[str, Any]] = []
    for s in srcs:
        try:
            if s == "mixkit" and kind == "video":
                out += mixkit(query, n)
            elif s == "pixabay":
                out += pixabay(query, kind, n)
            elif s == "wikimedia" and kind == "image":
                out += wikimedia(query, n)
        except Exception as e:  # noqa: BLE001 — bir mənbə işləməsə digəri qalır
            out.append({"source": s, "error": str(e)[:160]})
    return out


def download(items: list[dict[str, Any]], dst: Path) -> list[dict[str, Any]]:
    dst.mkdir(parents=True, exist_ok=True)
    done = []
    for i, it in enumerate([x for x in items if x.get("url")], 1):
        ext = ".mp4" if it["kind"] == "video" else (Path(urllib.parse.urlparse(it["url"]).path).suffix.lower() or ".jpg")
        f = dst / f"{i:02d}_{it['source']}_{it['id']}{ext}"
        if not f.is_file():
            try:
                f.write_bytes(_get(it["url"], timeout=120))
            except Exception as e:  # noqa: BLE001
                done.append({**it, "error": str(e)[:160]})
                continue
        done.append({**it, "file": str(f), "n": i})
    (dst / "manifest.json").write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
    return done


def contact_sheet(items: list[dict[str, Any]], out: Path) -> Path | None:
    """Nömrəli kiçik şəkillər (video üçün 1-ci saniyə) — seçim üçün."""
    from PIL import Image, ImageDraw, ImageFont

    files = [it for it in items if it.get("file")]
    if not files:
        return None
    tw, th, cols = 240, 240, 4
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 8) + 8, rows * (th + 30) + 8), (20, 22, 26))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    for k, it in enumerate(files):
        x, y = 8 + (k % cols) * (tw + 8), 8 + (k // cols) * (th + 30)
        tmp = out.parent / "_t.jpg"
        src = it["file"]
        args = ["ffmpeg", "-y", "-v", "error", *(["-ss", "1"] if it["kind"] == "video" else []), "-i", src, "-frames:v", "1",
                "-vf", f"scale={tw}:{th}:force_original_aspect_ratio=decrease,pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2", str(tmp)]
        if subprocess.run(args, capture_output=True).returncode == 0 and tmp.is_file():
            sheet.paste(Image.open(tmp).convert("RGB"), (x, y))
        d.text((x, y + th + 6), f"#{it['n']} {it['source']}" + (" · video" if it["kind"] == "video" else ""), font=font, fill=(230, 232, 236))
    (out.parent / "_t.jpg").unlink(missing_ok=True)
    sheet.save(out, quality=85)
    return out
