"""Instagram Reel referansı → yerli MP4: XƏRCLİ yol (Apify) — yalnız istifadəçi açıq razılıq verəndə (`--allow-cost`). Standart: xərcsiz.

Xərcsiz yol (standart): istifadəçi videonu söhbətə fayl kimi əlavə edir və ya Drive linki verir; sonra yerli faylı analiz et (watch-skill). Yalnız linkdən xərcsiz video alınmır
(video baytları mühitdə bağlı CDN-dədir; səhifəni brauzer kimi görünüb oxumaq/giriş divarını aşmaq da edilmir).

Niyə: Instagram videosunun baytları `*.cdninstagram.com`/`*.fbcdn.net` alt-domenlərindədir və mühitdə bağlıdır; mühit ayarına toxunmaq istənilmir.
Apify (api.apify.com) mühitdə artıq icazəlidir və açar mühitin network secret-indədir (söhbətə yazılmır). Actor videonu öz yaddaşına re-host edir, biz oradan endiririk.

  python -m montaj.reference "<reel linki>" [--out qovluq] [--max-usd 0.10]  → yerli MP4 yolunu çap edir
  sonra: .venv-watch/bin/watch-skill watch <mp4> --no-whisper --no-index --out-dir <qovluq>   (səhnə kadrları; kadrlara Read ilə bax)

Xərc: pay-per-event; `maxTotalChargeUsd` tavanı (standart 0.10 $). Yalnız açıq (public) Reel/post; giriş/cookie istifadə olunmur.
Qayda: yalnız şəxsi analiz — faylı montaja, repoya, Drive-a qoyma, kadrlarını təkrar istifadə etmə; işdən sonra sil (`montaj/../video-reference-analyst.md`).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ACTOR = "epctex~instagram-video-downloader"  # re-host edir; giriş: {"startUrls": [url]}
_URL = re.compile(r"^https?://(www\.)?instagram\.com/(reel|reels|p|tv)/[\w-]+", re.I)


def _post(actor: str, body: dict[str, Any], max_usd: float, timeout: int = 280) -> list[dict[str, Any]]:
    q = urllib.parse.urlencode({"maxTotalChargeUsd": f"{max_usd:.2f}", "timeout": str(timeout - 20)})
    req = urllib.request.Request(f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items?{q}", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode() or "[]")


def _video_urls(item: Any) -> list[str]:
    """Nəticədə MP4 linklərini (re-host olunmuş) tap; Apify yaddaşı (api.apify.com) üstün."""
    out: list[str] = []

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
        elif isinstance(x, str) and x.startswith("http") and (".mp4" in x.lower() or "key-value-stores" in x):
            out.append(x)
    walk(item)
    return sorted(set(out), key=lambda u: (0 if "api.apify.com" in u else 1, u))


def fetch_video(url: str, out_dir: Path, max_usd: float = 0.10, actor: str = ACTOR) -> Path:
    if not _URL.match(url): raise SystemExit("Bu Instagram Reel/post linki deyil (…/reel/<id>/ və ya …/p/<id>/ gözlənilir).")
    out_dir.mkdir(parents=True, exist_ok=True)
    items = _post(actor, {"startUrls": [url]}, max_usd)
    cands = [u for it in items for u in _video_urls(it)]
    if not cands: raise SystemExit("Video tapılmadı (post şəxsi, silinmiş və ya actor nəticə vermədi). Videonu fayl/Drive linki kimi istəyin.")
    last = ""
    for u in cands:
        host = urllib.parse.urlparse(u).hostname or ""
        dst = out_dir / "reference.mp4"
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=120) as r: dst.write_bytes(r.read())
            if dst.stat().st_size > 50_000: return dst
        except Exception as e:  # noqa: BLE001
            last = f"{host}: {str(e)[:80]}"
    raise SystemExit(f"Video endirilmədi ({last}). Re-host linki mühitdə bağlı host ola bilər — videonu fayl/Drive linki kimi istəyin.")


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m montaj.reference"); ap.add_argument("url"); ap.add_argument("--out", default="/tmp/reference"); ap.add_argument("--max-usd", type=float, default=0.10)
    ap.add_argument("--allow-cost", action="store_true", help="Apify xərcini istifadəçi açıq təsdiq edib")
    a = ap.parse_args()
    if not a.allow_cost:
        raise SystemExit("Xərcsiz rejim: linkdən video alınmır. İstifadəçidən videonu fayl (söhbətə əlavə) və ya Drive linki kimi istə. Apify yolu yalnız istifadəçi xərcə razılıq verəndə: --allow-cost.")
    print(fetch_video(a.url, Path(a.out), a.max_usd))


if __name__ == "__main__":
    main()
