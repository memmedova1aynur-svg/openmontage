"""Google Drive linkindən ORİJİNAL faylı yükləmək (önizləmə nüsxəsini yox).

Dəstəklənir: "Linki olan hər kəs görə bilər" paylaşımlı tək fayl linkləri.
Dəstəklənmir (Google OAuth lazımdır): şəxsi fayllar, qovluq linkləri.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs, urlparse

import requests

from montaj.errors import UserError

DOWNLOAD_URL = os.environ.get("MONTAJ_DRIVE_URL", "https://drive.usercontent.google.com/download")
_ID = re.compile(r"^[A-Za-z0-9_-]{20,}$")


def parse_link(link: str) -> dict:
    link = (link or "").strip()
    u = urlparse(link)
    host = (u.netloc or "").lower()
    if not host.endswith(("drive.google.com", "docs.google.com", "drive.usercontent.google.com")):
        raise UserError("Bu Google Drive linki deyil.", "Drive-da faylı açın, “Paylaş → Linki kopyala” edin və buraya yapışdırın.")
    if "/folders/" in u.path:
        raise UserError("Qovluq linki hələ dəstəklənmir.",
                        "Qovluqdakı hər videonun öz linkini ayrıca əlavə edin.")
    m = re.search(r"/file/d/([A-Za-z0-9_-]+)", u.path) or re.search(r"/d/([A-Za-z0-9_-]+)", u.path)
    fid = m.group(1) if m else (parse_qs(u.query).get("id") or [""])[0]
    if not _ID.match(fid or ""):
        raise UserError("Linkdə fayl kodu tapılmadı.", "Faylın “Paylaş” menyusundan alınmış tam linki yapışdırın.")
    return {"id": fid}


def _filename(resp: requests.Response, fid: str) -> str:
    cd = resp.headers.get("content-disposition", "")
    m = re.search(r"filename\*=UTF-8''([^;]+)", cd) or re.search(r'filename="([^"]+)"', cd)
    if m:
        from urllib.parse import unquote

        return unquote(m.group(1))
    return f"drive_{fid}"


def download(link: str, dst_dir: Path, progress: Callable[[float], None] | None = None,
             session: requests.Session | None = None, base_url: str | None = None,
             max_bytes: int = 8 * 1024**3) -> tuple[Path, str]:
    fid = parse_link(link)["id"]
    s = session or requests.Session()
    base_url = base_url or DOWNLOAD_URL
    params = {"id": fid, "export": "download", "confirm": "t"}
    try:
        r = s.get(base_url, params=params, stream=True, timeout=60)
    except requests.RequestException as e:
        raise UserError("Drive-a qoşulmaq alınmadı.", "Bir az sonra yenidən cəhd edin.", detail=str(e)) from e
    ctype = r.headers.get("content-type", "")
    if r.status_code in (401, 403, 404) or ctype.startswith("text/html"):
        r.close()
        raise UserError(
            "Fayl açıq deyil və ya tapılmadı.",
            "Drive-da faylın paylaşımını “Linki olan hər kəs — Baxan” edin və linki yenidən yapışdırın.",
            detail=f"HTTP {r.status_code} {ctype}",
        )
    if r.status_code >= 400:
        raise UserError("Drive faylı vermədi.", "Bir az sonra yenidən cəhd edin.", detail=f"HTTP {r.status_code}")
    total = int(r.headers.get("content-length") or 0)
    name = _filename(r, fid)
    dst_dir.mkdir(parents=True, exist_ok=True)
    tmp = dst_dir / f".drive_{fid}.part"
    got = 0
    with tmp.open("wb") as fh:
        for chunk in r.iter_content(1024 * 1024):
            if not chunk:
                continue
            got += len(chunk)
            if got > max_bytes:
                fh.close()
                tmp.unlink(missing_ok=True)
                raise UserError("Fayl çox böyükdür.", "8 GB-dan kiçik fayl seçin.")
            fh.write(chunk)
            if progress and total:
                progress(min(0.99, got / total))
    if got == 0:
        tmp.unlink(missing_ok=True)
        raise UserError("Drive boş cavab qaytardı.", "Linki yoxlayıb yenidən cəhd edin.")
    return tmp, name
