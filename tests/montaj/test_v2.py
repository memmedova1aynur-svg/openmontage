"""Montaj paneli v2: giriş, işlər, Drive, müştərilər, kəsim qaydaları, storyboard, render əlavələri."""

from __future__ import annotations

import http.server
import json
import shutil
import subprocess
import threading
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg yoxdur")

from tests.montaj.test_montaj import base_project, beep_onsets, flash_onsets, make_silence_source, make_sync_source  # noqa: E402


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("MONTAJ_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("MONTAJ_PROJECTS_DIR", str(tmp_path / "projects"))
    monkeypatch.setenv("MONTAJ_AUTH", "off")
    monkeypatch.setenv("MONTAJ_SYNC_DERIVE", "1")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    return tmp_path


def wait_job(c, jid, timeout=120):
    for _ in range(int(timeout * 10)):
        j = c.get(f"/api/jobs/{jid}").json()
        if j["status"] not in ("running", "queued"):
            return j
        time.sleep(0.1)
    raise AssertionError("iş bitmədi")


# --- giriş -----------------------------------------------------------------

def test_auth_required_and_login(env, monkeypatch):
    from fastapi.testclient import TestClient

    from montaj.server import app

    monkeypatch.setenv("MONTAJ_AUTH", "on")
    monkeypatch.setenv("MONTAJ_PASSWORD", "düzgün-parol")
    monkeypatch.setenv("MONTAJ_COOKIE_SECURE", "0")
    c = TestClient(app)
    assert c.get("/api/projects").status_code == 401
    assert c.get("/", follow_redirects=False).status_code in (302, 307)
    assert c.get("/healthz").status_code == 200
    r = c.post("/api/login", json={"password": "səhv"})
    assert r.status_code == 401 and "hint" in r.json()
    r = c.post("/api/login", json={"password": "düzgün-parol"})
    assert r.status_code == 200
    assert "httponly" in r.headers["set-cookie"].lower()
    assert c.get("/api/projects").status_code == 200
    # media yolu da qorunur
    c2 = TestClient(app)
    assert c2.get("/api/projects/x/media/y").status_code == 401


def test_auth_unconfigured_refuses(env, monkeypatch):
    from fastapi.testclient import TestClient

    from montaj.server import app

    monkeypatch.setenv("MONTAJ_AUTH", "on")
    monkeypatch.delenv("MONTAJ_PASSWORD", raising=False)
    monkeypatch.delenv("MONTAJ_PASSWORD_SHA256", raising=False)
    r = TestClient(app).get("/api/projects")
    assert r.status_code == 503 and "MONTAJ_PASSWORD" in r.json()["hint"]


# --- işlər -----------------------------------------------------------------

def test_jobs_persist_and_recover(env):
    from montaj import jobs

    gate = threading.Event()
    jid = jobs.start("test", "p1", lambda pr: (pr(0.5), gate.wait(5), {"ok": 1})[-1])
    time.sleep(0.2)
    on_disk = json.loads((env / "data" / "jobs" / f"{jid}.json").read_text())
    assert on_disk["status"] == "running"
    # server restartını təqlid et
    jobs._mem.clear()
    jobs.recover()
    j = jobs.get(jid)
    assert j["status"] == "interrupted" and "Yenidən" in j["hint"]
    gate.set()


def test_job_user_error_has_hint(env):
    from montaj import jobs
    from montaj.errors import UserError

    def bad(_):
        raise UserError("Fayl açıq deyil.", "Paylaşımı açın.")
    jid = jobs.start("x", "p", bad)
    for _ in range(50):
        if jobs.get(jid)["status"] == "error":
            break
        time.sleep(0.05)
    j = jobs.get(jid)
    assert j["error"] == "Fayl açıq deyil." and j["hint"] == "Paylaşımı açın."


# --- Drive -----------------------------------------------------------------

def test_drive_parse():
    from montaj.drive import parse_link
    from montaj.errors import UserError

    fid = "1AbCdEfGhIjKlMnOpQrStUvWxYz012345"
    for link in (f"https://drive.google.com/file/d/{fid}/view?usp=sharing",
                 f"https://drive.google.com/open?id={fid}",
                 f"https://drive.google.com/uc?id={fid}&export=download"):
        assert parse_link(link)["id"] == fid
    with pytest.raises(UserError, match="Qovluq"):
        parse_link("https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUvWxYz0")
    with pytest.raises(UserError):
        parse_link("https://example.com/file/d/abc")


class _FakeDrive(http.server.BaseHTTPRequestHandler):
    payload = b""

    def do_GET(self):  # noqa: N802
        if "id=PRIVATEPRIVATEPRIVATEPRIVATE" in self.path:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html>Sign in</html>")
            return
        self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Content-Length", str(len(self.payload)))
        self.send_header("Content-Disposition", "attachment; filename=\"video.mp4\"; filename*=UTF-8''M%C9%99nim%20video.mp4")
        self.end_headers()
        self.wfile.write(self.payload)

    def log_message(self, *a):
        pass


def test_drive_download_original_bytes(tmp_path):
    from montaj import drive
    from montaj.errors import UserError

    src = make_silence_source(tmp_path / "s.mp4")
    _FakeDrive.payload = src.read_bytes()
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _FakeDrive)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}/download"
    try:
        out, name = drive.download("https://drive.google.com/file/d/PUBLICPUBLICPUBLICPUBLIC/view", tmp_path / "dl",
                                   base_url=base)
        assert name == "Mənim video.mp4"
        assert out.read_bytes() == src.read_bytes(), "orijinal baytlar dəyişməməlidir"
        with pytest.raises(UserError, match="açıq deyil"):
            drive.download("https://drive.google.com/file/d/PRIVATEPRIVATEPRIVATEPRIVATE/view", tmp_path / "dl",
                           base_url=base)
    finally:
        srv.shutdown()


# --- müştərilər -------------------------------------------------------------

def test_clients_seed_and_no_invented_brand(env):
    from fastapi.testclient import TestClient

    from montaj.clients import INITIAL_NAMES
    from montaj.server import app

    c = TestClient(app)
    items = c.get("/api/clients").json()
    assert [x["name"] for x in items] == INITIAL_NAMES
    assert len(items) == 17
    assert all(x["colors"] == [] and x["font"] == "" and x["logo"] is None and x["field"] == "" for x in items)
    r = c.put(f"/api/clients/{items[0]['id']}", json={"colors": ["#zzz"]})
    assert r.status_code == 400 and "#RRGGBB" in r.json()["hint"]
    r = c.put(f"/api/clients/{items[0]['id']}", json={"colors": ["#1a2b3c"], "field": "Pediatriya"})
    assert r.json()["colors"] == ["#1A2B3C"]
    new = c.post("/api/clients", json={"name": "Test Müştəri", "field": "Kosmetika"}).json()
    assert new["name"] == "Test Müştəri"


# --- kəsim qaydaları ---------------------------------------------------------

WORDS = [
    {"w": "Salam,", "s": 0.50, "e": 0.90}, {"w": "bu", "s": 1.00, "e": 1.15}, {"w": "gün", "s": 1.20, "e": 1.50},
    # 0.6 s vurğu pauzası — saxlanmalıdır
    {"w": "vacib", "s": 2.10, "e": 2.60}, {"w": "mövzu.", "s": 2.65, "e": 3.10},
    # 2.4 s uzun pauza — kəsim namizədi
    {"w": "ee", "s": 5.50, "e": 5.80}, {"w": "Birinci", "s": 6.30, "e": 6.80}, {"w": "qayda", "s": 6.85, "e": 7.30},
]


def _inside_word(t):
    return any(w["s"] + 1e-6 < t < w["e"] - 1e-6 for w in WORDS)


def test_cut_points_never_inside_words_and_keep_short_pauses():
    from montaj.analysis import segments_from_words

    segs = segments_from_words(WORDS, 9.0)
    assert len(segs) == 2, "yalnız uzun pauzada bölünməlidir"
    assert "vacib" in segs[0]["text"], "qısa vurğu pauzası hissənin içində qalır"
    for s in segs:
        assert not _inside_word(s["srcIn"]) and not _inside_word(s["srcOut"])
    assert segs[0]["srcOut"] <= 3.10 + 0.25 + 1e-6 and segs[0]["srcOut"] >= 3.10
    # avtomatik təmizləmə: doldurucu söz çıxır, yenə də söz yarıda kəsilmir
    segs2 = segments_from_words(WORDS, 9.0, long_pause=0.8, drop_fillers=True)
    assert all("ee" not in s["text"].split() for s in segs2)
    for s in segs2:
        assert not _inside_word(s["srcIn"]) and not _inside_word(s["srcOut"])


SILENCES = [(0.0, 0.45), (1.55, 2.05), (3.15, 5.45), (7.4, 9.0)]


def test_safe_segments_snap_and_keep_untranscribed_audio():
    from montaj.analysis import segments_safe

    segs = segments_safe(9.0, SILENCES, WORDS, long_pause=1.2)
    assert len(segs) == 2
    for s in segs:
        assert not _inside_word(s["srcIn"]) and not _inside_word(s["srcOut"])
    assert "vacib" in segs[0]["text"], "0.5 s vurğu pauzası saxlanılır"
    # transkriptdə olmayan səs (məs. musiqi 7.4-dən sonra yoxdur, amma 3.15-dən əvvəl var) atılmır
    segs_nw = segments_safe(9.0, SILENCES, [], long_pause=1.2)
    assert len(segs_nw) == 2 and segs_nw[0]["srcIn"] < 0.5
    # səssizliyin ortasına düşən kəsim sözün içinə düşmür, hətta sərhəd sözə yaxındırsa
    tight = segments_safe(9.0, [(3.0, 5.6)], WORDS, long_pause=1.2, breath=0.0)
    for s in tight:
        assert not _inside_word(s["srcIn"]) and not _inside_word(s["srcOut"])
    auto = segments_safe(9.0, SILENCES, WORDS, long_pause=0.8, drop_fillers=True)
    assert all("ee" not in s["text"].split() for s in auto)


def test_cut_modes():
    from montaj.analysis import candidate_segments

    m = {"id": "m1", "duration": 9.0, "hasAudio": True, "hasVideo": True}
    an = {"duration": 9.0, "words": WORDS, "silences": SILENCES}
    keep = candidate_segments(m, an, "keep")
    assert keep[0]["srcIn"] == 0.0 and keep[-1]["srcOut"] == 9.0
    assert all(abs(a["srcOut"] - b["srcIn"]) < 1e-6 for a, b in zip(keep, keep[1:])), "olduğu kimi: boşluq yoxdur"
    sug = candidate_segments(m, an, "suggest")
    assert sum(s["srcOut"] - s["srcIn"] for s in sug) < 9.0


# --- storyboard axını (AI açarı olmadan) --------------------------------------

def test_storyboard_rules_flow_and_frames(env):
    from fastapi.testclient import TestClient

    from montaj.server import app

    c = TestClient(app)
    pid = c.post("/api/projects", json={"title": "SB", "project": base_project([])}).json()["id"]
    src = make_silence_source(env / "s.mp4")
    m = c.post(f"/api/projects/{pid}/media?name=klip.mp4", content=src.read_bytes()).json()["media"]
    rev_before = c.get(f"/api/projects/{pid}").json()["revision"]
    jid = c.post(f"/api/projects/{pid}/storyboard",
                 json={"options": {"format": ["talking_head"], "goal": ["sales"], "cutMode": "suggest",
                                   "aspect": "9:16", "extras": []}}).json()["job"]
    j = wait_job(c, jid, 300)
    assert j["status"] == "done", j
    sb = c.get(f"/api/projects/{pid}/storyboard/draft").json()
    assert sb["generator"] == "rules"
    assert len(sb["cards"]) == 2, "2 s sükut iki hissəyə bölür"
    assert sb["frames"][m["id"]]["aspect"] == "9:16"
    # storyboard montajı dəyişmir
    assert c.get(f"/api/projects/{pid}").json()["revision"] == rev_before
    # tək kart üçün alternativlər (qaydalar rejimi)
    r = c.post(f"/api/projects/{pid}/storyboard/card", json={"storyboard": sb, "cardId": sb["cards"][1]["id"]}).json()
    assert r["mode"] == "rules" and any("Əvvəlki" in a["label"] for a in r["alternatives"])
    # caption açarsız: aydın xəta
    r = c.post(f"/api/projects/{pid}/caption")
    assert r.status_code == 400 and "ANTHROPIC_API_KEY" in r.json()["hint"]


# --- render əlavələri ---------------------------------------------------------

def _probe_json(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)["streams"]


def test_render_hdr_image_crop_logo_endcard_duck(tmp_path):
    from montaj.media import probe
    from montaj.render import conversions, render, render_plan

    hlg = tmp_path / "hlg.mov"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=1920x1080:r=30000/1001:d=3",
                    "-f", "lavfi", "-i", "sine=f=500:d=3", "-c:v", "libx265", "-pix_fmt", "yuv420p10le",
                    "-x265-params", "colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc:log-level=error",
                    "-color_primaries", "bt2020", "-color_trc", "arib-std-b67", "-colorspace", "bt2020nc",
                    "-c:a", "aac", "-shortest", str(hlg)], check=True)
    img = tmp_path / "foto.jpg"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc=s=1200x1600", "-frames:v", "1", str(img)], check=True)
    music = tmp_path / "m.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "sine=f=220:d=10", str(music)], check=True)
    logo = tmp_path / "logo.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=red:s=200x100", "-frames:v", "1", str(logo)], check=True)
    mv, mi, mm = probe(hlg), probe(img), probe(music)
    assert mv["hdr"] and mi.get("isImage")
    media = [{"id": "V", "name": "hlg.mov", "file": "hlg.mov", **mv}, {"id": "I", "name": "foto.jpg", "file": "foto.jpg", **mi},
             {"id": "M", "name": "m.wav", "file": "m.wav", **mm}]
    p = base_project(media)
    p.update(width=1080, height=1920, fpsRate="30000/1001", mirrorAll=False,
             mix={"speech": 1, "music": 0.8, "sfx": 1, "voice": 1, "duck": True},
             branding={"logo": {"enabled": True, "position": "top-right", "size": 0.2},
                       "end": {"enabled": True, "duration": 2, "showLogo": True, "cta": "Bizi izləyin", "contact": "+994 00 000 00 00", "bg": "#112233"}})
    frame = {"aspect": "9:16", "mode": "auto", "s": 1.0, "baseW": (9 / 16 * 1080) / 1920, "baseH": 1.0,
             "keys": [{"t": 0, "cx": 0.3, "cy": 0.5}, {"t": 2, "cx": 0.7, "cy": 0.5}], "rotate": 0}
    p["clips"] = [
        {"id": "v1c", "track": "v1", "media": "V", "srcIn": 0, "srcOut": 3, "order": 0, "frame": frame,
         "adjust": {"mirror": True, "brightness": 0.05, "contrast": 1.1, "saturation": 1.2, "temperature": 5500}},
        {"id": "a1c", "track": "a1", "media": "V", "srcIn": 0, "srcOut": 3, "linkedTo": "v1c", "volume": 1},
        {"id": "v2c", "track": "v1", "media": "I", "srcIn": 0, "srcOut": 2, "order": 1},
        {"id": "mc", "track": "m1", "media": "M", "srcIn": 0, "srcOut": 7, "start": 0, "volume": 1},
        {"id": "sub", "track": "c1", "media": None, "srcIn": 0, "srcOut": 1.5, "start": 0.2, "text": "Subtitr ə ş ğ"},
    ]
    p["tracks"].append({"id": "c1", "kind": "text", "name": "Subtitr"})
    out = render(p, tmp_path, tmp_path / "out.mp4", logo_path=logo)
    st = _probe_json(out)
    v = next(s for s in st if s["codec_type"] == "video")
    assert (v["width"], v["height"]) == (1080, 1920)
    assert v["codec_name"] == "h264" and v["pix_fmt"] == "yuv420p"
    assert v.get("color_transfer") == "bt709", "HDR SDR-ə çevrilməli və BT.709 kimi işarələnməlidir"
    assert v["r_frame_rate"] == "30000/1001", "kadr tezliyi saxlanılır"
    plan = render_plan(p)
    assert abs(plan["total"] - (7 + 2)) < 0.05  # musiqi 7 s + sonluq 2 s
    dur = float(next(s for s in st if s["codec_type"] == "audio")["duration"])
    assert abs(dur - plan["total"]) < 0.15
    conv = " ".join(conversions(p))
    assert "HDR" in conv and "HEVC" in conv and "10-bit" in conv and "şəkil" in conv


def test_sync_preserved_with_crop_and_mirror(tmp_path):
    """Kadraj + güzgü + rəng əlavə olunanda da səs-görüntü sinxronu qalır."""
    from montaj.media import probe
    from montaj.render import render

    src = make_sync_source(tmp_path / "s.mp4")
    info = probe(src)
    p = base_project([{"id": "S", "name": "s.mp4", "file": "s.mp4", **info}])
    p.update(width=202, height=360)
    fr = {"aspect": "9:16", "mode": "manual", "s": 1, "baseW": (9 / 16 * 360) / 640, "baseH": 1, "keys": [{"t": 0, "cx": 0.5, "cy": 0.5}]}
    p["clips"] = [
        {"id": "a", "track": "v1", "media": "S", "srcIn": 6.55, "srcOut": 12, "order": 0, "frame": fr, "adjust": {"mirror": True, "contrast": 1.1}},
        {"id": "aa", "track": "a1", "media": "S", "srcIn": 6.55, "srcOut": 12, "linkedTo": "a"},
        {"id": "b", "track": "v1", "media": "S", "srcIn": 0, "srcOut": 4.55, "order": 1, "frame": fr},
        {"id": "bb", "track": "a1", "media": "S", "srcIn": 0, "srcOut": 4.55, "linkedTo": "b"},
    ]
    out = render(p, tmp_path, tmp_path / "o.mp4")
    fl, bp = flash_onsets(out), beep_onsets(out)
    assert len(fl) == 9 and len(bp) == 9
    assert max(abs(a - b) for a, b in zip(fl, bp)) <= 1 / 30 + 0.005


def test_reframe_suggest_logic():
    from montaj.reframe import output_size, suggest

    m = {"width": 1920, "height": 1080}
    samples = [{"t": t / 2, "faces": [{"x": 0.62, "y": 0.18, "w": 0.08, "h": 0.15, "score": 0.9}]} for t in range(10)]
    fr = suggest(m, 0, 5, "9:16", 1080, samples)
    assert fr["mode"] == "auto" and fr["s"] == 1.0, "yaxınlaşma yoxdur (mənbə ehtiyatı yoxdur)"
    assert abs(fr["keys"][0]["cx"] - 0.66) < 0.03
    assert len(fr["keys"]) == 1, "sabit üz — kadraj tərpənmir"
    # iki nəfər uzaqda: xəbərdarlıq
    two = [{"t": 0, "faces": [{"x": 0.1, "y": 0.2, "w": 0.08, "h": 0.15}, {"x": 0.85, "y": 0.2, "w": 0.08, "h": 0.15}]}]
    assert any("sığmır" in w for w in suggest(m, 0, 1, "9:16", 1080, two)["warnings"])
    assert any("Üz tapılmadı" in w for w in suggest(m, 0, 1, "9:16", 1080, [{"t": 0, "faces": []}])["warnings"])
    assert output_size({"width": 1920, "height": 1080}, "9:16") == (608, 1080)
    assert output_size({"width": 3840, "height": 2160}, "9:16") == (1080, 1920)
