"""Google Drive linkindən ORİJİNAL faylı yükləmək (önizləmə nüsxəsini yox).

Dəstəklənir: "Linki olan hər kəs görə bilər" paylaşımlı tək fayl və QOVLUQ linkləri (`expand`).
Dəstəklənmir (Google OAuth lazımdır): şəxsi fayllar.

Etibarlılıq (uzun 4K videolar, bulud serverinin paylaşılan IP-si):
* kəsilən ötürmə HTTP Range ilə qaldığı yerdən davam edir (bir neçə cəhd, artan fasilə);
* alınan bayt sayı `content-length` ilə yoxlanılır — yarımçıq fayl qəbul olunmur;
* Google-un HTML xəbərdarlıqları (virus yoxlaması forması, endirmə limiti, "çox adam endirib", avtomatik sorğu bloku,
  giriş səhifəsi) tanınır və aydın mesaja çevrilir;
* əsas ünvan alınmasa `drive.google.com/uc` ehtiyat ünvanı sınanır;
* mühitdə pulsuz `GOOGLE_API_KEY` (Drive API) varsa, əvvəl rəsmi API ilə yüklənir — anonim endirmə limitlərindən asılı deyil.
"""

from __future__ import annotations

import html as _html
import os
import re
import time
from collections.abc import Callable
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import requests

from montaj.errors import UserError

DOWNLOAD_URL = os.environ.get("MONTAJ_DRIVE_URL", "https://drive.usercontent.google.com/download")
FALLBACK_URL = os.environ.get("MONTAJ_DRIVE_FALLBACK_URL", "https://drive.google.com/uc")
FOLDER_URL = os.environ.get("MONTAJ_DRIVE_FOLDER_URL", "https://drive.google.com/embeddedfolderview")
API_URL = os.environ.get("MONTAJ_DRIVE_API_URL", "https://www.googleapis.com/drive/v3/files")
_ID = re.compile(r"^[A-Za-z0-9_-]{20,}$")
RETRIES = 6          # kəsilmədən sonra davam cəhdləri
BACKOFF = 2.0        # saniyə; hər cəhddə ikiqat
_NET = (requests.ConnectionError, requests.Timeout, requests.exceptions.ChunkedEncodingError)

QUOTA = ("Google Drive bu faylın endirmə limitini keçib — paylaşım düzgündür.",
         ("Drive-da faylın surətini çıxarın (Make a copy) və YENİ surətin linkini göndərin, və ya bir neçə saat sonra "
         "yenidən cəhd edin. Daimi həll: mühitə pulsuz GOOGLE_API_KEY əlavə edin (montaj/IS_AXINI.md, “Drive”)."))
BLOCKED = ("Google bu serverdən gələn endirmələri müvəqqəti məhdudlaşdırıb (avtomatik sorğu yoxlaması).",
           ("10–30 dəqiqə sonra yenidən cəhd edin. Daimi həll: mühitə pulsuz GOOGLE_API_KEY əlavə edin "
           "(montaj/IS_AXINI.md, “Drive”) — rəsmi API bu blokdan asılı deyil."))
PRIVATE = ("Fayl açıq deyil və ya tapılmadı.",
           ("Drive-da faylın paylaşımını “Linki olan hər kəs — Baxan” edin və linki yenidən yapışdırın. "
           "Fayl başqasının Drive-ındadırsa, sahibi də bunu etməlidir."))


def _ids(link: str) -> tuple[str, str]:
    """(növ, kod): növ 'file' və ya 'folder'."""
    link = (link or "").strip()
    u = urlparse(link)
    host = (u.netloc or "").lower()
    if not host.endswith(("drive.google.com", "docs.google.com", "drive.usercontent.google.com")):
        raise UserError("Bu Google Drive linki deyil.", "Drive-da faylı açın, “Paylaş → Linki kopyala” edin və buraya yapışdırın.")
    m = re.search(r"/folders/([A-Za-z0-9_-]+)", u.path)
    if m:
        return "folder", m.group(1)
    m = re.search(r"/file/d/([A-Za-z0-9_-]+)", u.path) or re.search(r"/d/([A-Za-z0-9_-]+)", u.path)
    fid = m.group(1) if m else (parse_qs(u.query).get("id") or [""])[0]
    if not _ID.match(fid or ""):
        raise UserError("Linkdə fayl kodu tapılmadı.", "Faylın “Paylaş” menyusundan alınmış tam linki yapışdırın.")
    return "file", fid


def parse_link(link: str) -> dict:
    """Tək fayl linki → {"id": ...}. Qovluq linki üçün əvvəlcə `expand` çağırın."""
    kind, fid = _ids(link)
    if kind == "folder":
        raise UserError("Qovluq linki birbaşa fayl kimi açılmır.",
                        "`expand` ilə qovluqdakı faylların siyahısını alın və ya hər videonun linkini ayrıca əlavə edin.")
    return {"id": fid}


def is_folder(link: str) -> bool:
    try:
        return _ids(link)[0] == "folder"
    except UserError:
        return False


def _api_key() -> str:
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("MONTAJ_DRIVE_API_KEY") or ""


def list_folder(link: str, session: requests.Session | None = None) -> list[dict]:
    """Açıq qovluqdakı fayllar: [{"id", "name", "link"}], ada görə sıralı. Alt qovluqlar daxil deyil."""
    kind, fold = _ids(link)
    if kind != "folder":
        raise UserError("Bu qovluq linki deyil.", "Drive-da qovluğu açıb “Paylaş → Linki kopyala” edin.")
    s = session or requests.Session()
    out: list[dict] = []
    key = _api_key()
    if key:
        try:
            tok = None
            while True:
                params = {"q": f"'{fold}' in parents and trashed = false", "key": key, "pageSize": 1000,
                          "fields": "nextPageToken, files(id, name, mimeType)", "orderBy": "name"}
                if tok:
                    params["pageToken"] = tok
                r = s.get(API_URL, params=params, timeout=30)
                if r.status_code != 200:
                    out = []
                    break
                js = r.json()
                out += [{"id": f["id"], "name": f["name"]} for f in js.get("files", [])
                        if f.get("mimeType") != "application/vnd.google-apps.folder"]
                tok = js.get("nextPageToken")
                if not tok:
                    break
        except (requests.RequestException, ValueError):
            out = []
    if not out:
        try:
            r = s.get(FOLDER_URL, params={"id": fold}, timeout=30)
        except requests.RequestException as e:
            raise UserError("Drive qovluğuna qoşulmaq alınmadı.", "Bir az sonra yenidən cəhd edin.", detail=str(e)) from e
        if r.status_code != 200:
            raise UserError("Qovluq açıq deyil və ya tapılmadı.",
                            "Drive-da qovluğun paylaşımını “Linki olan hər kəs — Baxan” edin.", detail=f"HTTP {r.status_code}")
        page = r.text
        for m in re.finditer(r'id="entry-([A-Za-z0-9_-]{20,})"(.*?)flip-entry-title">([^<]*)<', page, re.DOTALL):
            body = m.group(2)
            if "/folders/" in body:
                continue  # alt qovluq
            out.append({"id": m.group(1), "name": _html.unescape(m.group(3)).strip()})
        out.sort(key=lambda f: f["name"].lower())
    for f in out:
        f["link"] = f"https://drive.google.com/file/d/{f['id']}/view"
    if not out:
        raise UserError("Qovluqda fayl tapılmadı.",
                        "Qovluğun paylaşımını “Linki olan hər kəs — Baxan” edin; fayllar alt qovluqdadırsa, alt qovluğun linkini göndərin.")
    return out


def expand(links: list[str] | None, session: requests.Session | None = None) -> list[str]:
    """Fayl və qovluq linkləri → fayl linkləri (qovluq açılır, sıra saxlanılır)."""
    out: list[str] = []
    for link in links or []:
        if is_folder(link):
            files = list_folder(link, session)
            print(f"qovluq: {len(files)} fayl — " + ", ".join(f["name"] for f in files))
            out += [f["link"] for f in files]
        else:
            out.append(link)
    return out


def _filename(resp: requests.Response, fid: str) -> str:
    cd = resp.headers.get("content-disposition", "")
    m = re.search(r"filename\*=UTF-8''([^;]+)", cd) or re.search(r'filename="([^"]+)"', cd)
    if m:
        return unquote(m.group(1))
    return f"drive_{fid}"


def _html_problem(text: str, status: int) -> tuple[str, str, str] | None:
    """Google-un HTML cavabını tanı → (mesaj, nə etməli, detal) və ya None (virus forması / naməlum)."""
    t = text or ""
    if "Quota exceeded" in t or "Too many users have viewed or downloaded" in t or "download quota" in t.lower():
        return (*QUOTA, "quota exceeded")
    if status == 429 or "unusual traffic" in t or "automated queries" in t or "/sorry/" in t:
        return (*BLOCKED, f"HTTP {status} rate-limited")
    return None


def _proxy_hint() -> str:
    """Agent proksisinin son ötürmə xətaları (varsa) — diaqnostika üçün, açar/URL göstərmədən."""
    px = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if not px:
        return ""
    try:
        js = requests.get(px.rstrip("/") + "/__agentproxy/status", timeout=5, proxies={"http": None, "https": None}).json()
    except Exception:  # noqa: BLE001
        return ""
    fails = js.get("recentRelayFailures") or []
    if not fails:
        return ""
    last = fails[-1] if isinstance(fails, list) else fails
    return f" | proksi: {str(last)[:200]}"


class _Src:
    """Bir mənbə cəhdi: (url, params, headers). API açarı detal mesajlarına düşmür."""

    def __init__(self, name: str, url: str, params: dict, headers: dict | None = None):
        self.name, self.url, self.params, self.headers = name, url, params, headers or {}


def _sources(fid: str, base_url: str | None) -> list[_Src]:
    src = []
    key = _api_key()
    if key and not base_url:
        src.append(_Src("api", f"{API_URL}/{fid}", {"alt": "media", "key": key, "supportsAllDrives": "true",
                                                     "acknowledgeAbuse": "true"}))
    src.append(_Src("usercontent", base_url or DOWNLOAD_URL, {"id": fid, "export": "download", "confirm": "t"}))
    if not base_url and FALLBACK_URL:
        src.append(_Src("uc", FALLBACK_URL, {"id": fid, "export": "download", "confirm": "t"}))
    return src


def _get(s: requests.Session, url: str, params: dict | None, headers: dict | None = None):
    last = None
    for i in range(3):
        try:
            return s.get(url, params=params, headers=headers or {}, stream=True, timeout=(30, 120))
        except _NET as e:
            last = e
            time.sleep(BACKOFF * (2 ** i))
        except requests.RequestException as e:
            last = e
            break
    raise UserError("Drive-a qoşulmaq alınmadı.", "Bir az sonra yenidən cəhd edin.", detail=f"{type(last).__name__}{_proxy_hint()}")


def _open(s: requests.Session, src: _Src, fid: str) -> requests.Response:
    """Faylın baytlarını verən cavabı aç (virus forması keçilir) və ya UserError."""
    r = _get(s, src.url, src.params, src.headers)
    ctype = r.headers.get("content-type", "")
    if r.status_code == 200 and ctype.startswith("text/html"):
        text = r.text
        r.close()
        prob = _html_problem(text, r.status_code)
        if prob:
            raise UserError(prob[0], prob[1], detail=prob[2])
        # Böyük fayllarda "virus scan warning" forması: gizli sahələrlə (uuid) yenidən istə.
        fields = dict(re.findall(r'<input type="hidden" name="([^"]+)" value="([^"]*)"', text))
        if fields.get("id") == fid:
            action = re.search(r'action="([^"]+)"', text)
            r = _get(s, _html.unescape(action.group(1)) if action else src.url, fields)
            ctype = r.headers.get("content-type", "")
            if ctype.startswith("text/html"):
                text = r.text
                r.close()
                prob = _html_problem(text, r.status_code)
                if prob:
                    raise UserError(prob[0], prob[1], detail=prob[2])
                raise UserError(*PRIVATE, detail=f"{src.name}: HTTP {r.status_code} html after confirm")
        else:
            raise UserError(*PRIVATE, detail=f"{src.name}: HTTP {r.status_code} {ctype}")
    if r.status_code == 429 or r.status_code >= 500:
        body = ""
        try:
            body = r.text[:2000]
        finally:
            r.close()
        prob = _html_problem(body, 429) if r.status_code == 429 else None
        if prob:
            raise UserError(prob[0], prob[1], detail=f"{src.name}: {prob[2]}")
        raise UserError("Drive faylı vermədi.", "Bir az sonra yenidən cəhd edin.", detail=f"{src.name}: HTTP {r.status_code}")
    if r.status_code in (401, 403, 404):
        body = r.text[:2000] if src.name == "api" else ""
        r.close()
        if "downloadQuotaExceeded" in body or "userRateLimitExceeded" in body or "rateLimitExceeded" in body:
            raise UserError(*QUOTA, detail=f"{src.name}: quota")
        raise UserError(*PRIVATE, detail=f"{src.name}: HTTP {r.status_code}")
    if r.status_code >= 400 or ctype.startswith("text/html"):
        r.close()
        raise UserError("Drive faylı vermədi.", "Bir az sonra yenidən cəhd edin.", detail=f"{src.name}: HTTP {r.status_code}")
    return r


def _total(r: requests.Response, have: int) -> int:
    cr = r.headers.get("content-range", "")
    m = re.search(r"/(\d+)\s*$", cr)
    if m:
        return int(m.group(1))
    n = int(r.headers.get("content-length") or 0)
    return n + have if r.status_code == 206 else n


def _stream(s: requests.Session, r: requests.Response, src: _Src, tmp: Path, max_bytes: int,
            progress: Callable[[float], None] | None) -> int:
    """Faylı tmp-ə yaz; kəsilsə Range ilə davam et. Qaytarır: bayt sayı (ölçü yoxlanılıb)."""
    final_url = r.url  # yönləndirmədən sonrakı birbaşa ünvan
    total = _total(r, 0)
    got = 0
    fh = tmp.open("wb")
    tries = 0
    try:
        while True:
            try:
                for chunk in r.iter_content(1024 * 1024):
                    if not chunk:
                        continue
                    got += len(chunk)
                    if got > max_bytes:
                        raise UserError("Fayl çox böyükdür.", "8 GB-dan kiçik fayl seçin.")
                    fh.write(chunk)
                    if progress and total:
                        progress(min(0.99, got / total))
                r.close()
                if not total or got >= total:
                    break
                err = f"yarımçıq: {got}/{total}"
            except _NET as e:
                r.close()
                err = type(e).__name__
            tries += 1
            if tries > RETRIES:
                raise UserError("Drive faylı yarımçıq endirildi (bağlantı dəfələrlə kəsildi).",
                                "Bir az sonra yenidən cəhd edin; təkrarlansa faylın surətini çıxarıb (Make a copy) yeni linki göndərin.",
                                detail=f"{src.name}: {err}{_proxy_hint()}")
            time.sleep(BACKOFF * (2 ** min(tries - 1, 4)))
            fh.flush()
            try:
                r = s.get(final_url, headers={**src.headers, "Range": f"bytes={got}-"}, stream=True, timeout=(30, 120))
            except _NET:
                r = None
            if r is None:
                continue
            if r.status_code == 206:
                pass  # davam
            elif r.status_code == 200 and not r.headers.get("content-type", "").startswith("text/html"):
                fh.seek(0)
                fh.truncate()
                got = 0  # server Range dəstəkləmir — başdan
            else:
                # birbaşa ünvanın vaxtı keçib — mənbəni yenidən aç və başdan yaz
                r.close()
                r = _open(s, src, src.params.get("id") or src.url.rsplit("/", 1)[-1])
                final_url = r.url
                fh.seek(0)
                fh.truncate()
                got = 0
            total = _total(r, got) or total
    finally:
        fh.close()
    return got


def download(link: str, dst_dir: Path, progress: Callable[[float], None] | None = None,
             session: requests.Session | None = None, base_url: str | None = None,
             max_bytes: int = 8 * 1024**3) -> tuple[Path, str]:
    fid = parse_link(link)["id"]
    s = session or requests.Session()
    dst_dir.mkdir(parents=True, exist_ok=True)
    tmp = dst_dir / f".drive_{fid}.part"
    errors: list[UserError] = []
    for src in _sources(fid, base_url):
        try:
            r = _open(s, src, fid)
            name = _filename(r, fid)
            if src.name == "api" and name == f"drive_{fid}":
                try:  # API alt=media fayl adını vermir — metadata
                    meta = s.get(f"{API_URL}/{fid}", params={"fields": "name", "key": src.params["key"],
                                                            "supportsAllDrives": "true"}, timeout=30).json()
                    name = meta.get("name") or name
                except (requests.RequestException, ValueError):
                    pass
            got = _stream(s, r, src, tmp, max_bytes, progress)
        except UserError as e:
            tmp.unlink(missing_ok=True)
            if "çox böyükdür" in e.message:
                raise
            errors.append(e)
            continue
        if got == 0:
            tmp.unlink(missing_ok=True)
            errors.append(UserError("Drive boş cavab qaytardı.", "Linki yoxlayıb yenidən cəhd edin.", detail=src.name))
            continue
        return tmp, name
    # ən mənalı xətanı qaytar: limit/blok > paylaşım > digər
    for key in (QUOTA[0], BLOCKED[0]):
        for e in errors:
            if e.message == key:
                raise e
    for e in errors:
        if e.message == PRIVATE[0]:
            raise e
    raise errors[0] if errors else UserError("Drive faylı vermədi.", "Bir az sonra yenidən cəhd edin.")
