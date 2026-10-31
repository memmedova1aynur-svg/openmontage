"""Montaj paneli testləri: saxlama, render, səs-görüntü sinxronu, API.

Sintetik material: hər tam saniyədə ağ kadr + eyni anda 1 kHz siqnal.
Kəsmə/bölmə/yerdəyişmədən sonra render edilmiş MP4-də hər siqnal öz ağ
kadrı ilə üst-üstə düşməlidir.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg yoxdur")

REPO = Path(__file__).resolve().parents[2]
FPS = 30


def make_sync_source(path: Path, dur: float = 12.0) -> Path:
    cond = "lt(mod(t\\,1)\\,0.1)*gte(t\\,0.5)"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i",
        f"color=c=black:s=640x360:r={FPS}:d={dur},drawbox=x=0:y=0:w=iw:h=ih:color=white:t=fill:enable='{cond}'",
        "-f", "lavfi", "-i",
        f"aevalsrc='if({cond}\\,0.8*sin(2*PI*1000*t)\\,0)':s=48000:d={dur}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-g", "30", "-c:a", "aac", "-shortest", str(path),
    ], check=True)
    return path


def make_silence_source(path: Path) -> Path:
    # 0-2 s ton, 2-4 s sükut, 4-6 s ton
    expr = "if(lt(t\\,2)+gte(t\\,4)\\,0.5*sin(2*PI*440*t)\\,0)"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i", f"testsrc2=s=320x240:r={FPS}:d=6",
        "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d=6",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(path),
    ], check=True)
    return path


def flash_onsets(path: Path) -> list[float]:
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vf", "scale=32:18,format=gray",
         "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    frames = np.frombuffer(out, dtype=np.uint8).reshape(-1, 32 * 18).mean(axis=1)
    on = frames > 128
    return [i / FPS for i in range(len(on)) if on[i] and (i == 0 or not on[i - 1])]


def beep_onsets(path: Path, rate: int = 48000) -> list[float]:
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(rate), "-f", "s16le", "-"],
        capture_output=True, check=True).stdout
    pcm = np.abs(np.frombuffer(out, dtype=np.int16).astype(np.float32) / 32768)
    hop = rate // 1000  # 1 ms
    env = pcm[: len(pcm) // hop * hop].reshape(-1, hop).max(axis=1)
    res, quiet = [], 1000
    for i, v in enumerate(env):
        if v > 0.2:
            if quiet >= 300:
                res.append(i / 1000)
            quiet = 0
        else:
            quiet += 1
    return res


def node_layout(project: dict) -> dict:
    script = (
        "import('" + (REPO / "montaj/ui/timeline.js").as_posix() + "').then(TL=>{"
        "const p=JSON.parse(require('fs').readFileSync(0,'utf8'));"
        "console.log(JSON.stringify(Object.fromEntries([...TL.layout(p)].map(([k,v])=>[k,[v.start,v.end]]))));})"
    )
    out = subprocess.run(["node", "-e", script], input=json.dumps(project), capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def base_project(media: list[dict]) -> dict:
    return {
        "schema": 1, "id": "tmp", "title": "Test", "revision": 0, "width": 640, "height": 360, "fps": FPS,
        "tracks": [
            {"id": "v1", "kind": "video", "name": "Video"}, {"id": "a1", "kind": "speech", "name": "Danışıq"},
            {"id": "m1", "kind": "music", "name": "Musiqi"}, {"id": "s1", "kind": "sfx", "name": "Səs effekti"},
            {"id": "t1", "kind": "text", "name": "Mətn"},
        ],
        "media": media, "clips": [], "proposals": [],
    }


@pytest.fixture()
def tmp_projects(tmp_path, monkeypatch):
    monkeypatch.setenv("MONTAJ_PROJECTS_DIR", str(tmp_path / "projects"))
    return tmp_path / "projects"


def test_render_sync_after_split_delete_extend_move(tmp_path):
    from montaj.media import probe
    from montaj.render import render, render_plan

    src = make_sync_source(tmp_path / "src.mp4")
    info = probe(src)
    m = {"id": "S", "name": "src.mp4", "file": "src.mp4", **info}
    p = base_project([m])
    # Model əməliyyatlarının nəticəsi: [6.55..12] əvvələ köçürülüb, [0..3.55] klipi 4.55-ə qədər geri uzadılıb,
    # [3.55..6.55] silinib. (Eyni ardıcıllıq JS testində timeline.js ilə yoxlanılır.)
    p["clips"] = [
        {"id": "v_last", "track": "v1", "media": "S", "srcIn": 6.55, "srcOut": 12.0, "order": 0},
        {"id": "a_last", "track": "a1", "media": "S", "srcIn": 6.55, "srcOut": 12.0, "linkedTo": "v_last", "volume": 1},
        {"id": "v_first", "track": "v1", "media": "S", "srcIn": 0.0, "srcOut": 4.55, "order": 1},
        {"id": "a_first", "track": "a1", "media": "S", "srcIn": 0.0, "srcOut": 4.55, "linkedTo": "v_first", "volume": 1},
        {"id": "t_1", "track": "t1", "media": None, "srcIn": 0, "srcOut": 2, "start": 1, "text": "Salam, dünya! Əəə şçğıöü"},
    ]
    assert node_layout(p) == {k: list(v) for k, v in __import__("montaj.model", fromlist=["layout"]).layout(p).items()}
    out = render(p, tmp_path, tmp_path / "out.mp4")
    plan = render_plan(p)
    got = probe(out)
    assert got["hasVideo"] and got["hasAudio"]
    assert abs(got["duration"] - plan["total"]) < 0.1

    flashes = flash_onsets(out)
    beeps = beep_onsets(out)
    # gözlənilən: birinci klipdə 7,8,9,10,11 -> 5 çaxma, ikincidə 1,2,3,4 -> 4 çaxma
    assert len(flashes) == 9, flashes
    assert len(beeps) == 9, beeps
    second_start = plan["video"][1]["start"]
    expected = [s - 6.55 for s in (7, 8, 9, 10, 11)] + [second_start + s for s in (1, 2, 3, 4)]
    for e, f, b in zip(expected, flashes, beeps):
        assert abs(f - e) <= 1.5 / FPS, (e, f)
        assert abs(b - f) <= 1.0 / FPS + 0.005, f"səs-görüntü sürüşməsi {b - f:.3f}s"


def test_store_save_reopen_and_history(tmp_projects):
    from montaj import store

    p = store.create("Mənim layihəm", base_project([]))
    assert p["id"] == "menim-layihem"
    p["clips"] = [{"id": "t1x", "track": "t1", "media": None, "srcIn": 0, "srcOut": 2, "start": 0, "text": "a"}]
    s1 = store.save(p["id"], p, base_revision=1)
    assert s1["revision"] == 2
    with pytest.raises(store.RevisionConflict):
        store.save(p["id"], p, base_revision=1)
    again = store.load(p["id"])
    assert again["clips"][0]["text"] == "a"
    assert (store.project_dir(p["id"]) / "montaj_history" / "rev_000001.json").is_file()
    bad = dict(again, clips=[{"id": "x", "track": "v1", "media": "nope", "srcIn": 0, "srcOut": 1, "order": 0}])
    from montaj.model import ProjectError
    with pytest.raises(ProjectError):
        store.save(p["id"], bad, None)


def test_silence_detection_and_keep_ranges(tmp_path):
    from montaj.media import detect_silence, keep_ranges

    src = make_silence_source(tmp_path / "s.mp4")
    sil = detect_silence(src, 0, 6, -35, 0.6)
    assert len(sil) == 1
    a, b = sil[0]
    assert abs(a - 2) < 0.1 and abs(b - 4) < 0.1
    keep = keep_ranges(0, 6, sil)
    assert len(keep) == 2
    assert keep[0][0] == 0 and abs(keep[0][1] - 2.12) < 0.1
    assert abs(keep[1][0] - 3.88) < 0.1 and keep[1][1] == 6


def test_api_flow_upload_propose_render(tmp_projects, tmp_path):
    from fastapi.testclient import TestClient

    from montaj.server import app

    c = TestClient(app)
    r = c.post("/api/projects", json={"title": "API test", "project": base_project([])})
    assert r.status_code == 200, r.text
    pid = r.json()["id"]
    src = make_silence_source(tmp_path / "s.mp4")
    data = src.read_bytes()
    r = c.post(f"/api/projects/{pid}/media?name=klip.mp4", content=data)
    assert r.status_code == 200, r.text
    m = r.json()["media"]
    assert m["hasVideo"] and m["hasAudio"] and abs(m["duration"] - 6) < 0.1
    original = tmp_projects / pid / m["file"]
    sha_before = hashlib.sha256(original.read_bytes()).hexdigest()

    # proksi və dalğa forması fonda hazırlanır
    for _ in range(100):
        rec = next(x for x in c.get(f"/api/projects/{pid}").json()["media"] if x["id"] == m["id"])
        if rec.get("preview"):
            break
        time.sleep(0.1)
    assert rec.get("preview")
    assert c.get(f"/api/projects/{pid}/media/{m['id']}/peaks").status_code == 200
    rr = c.get(f"/api/projects/{pid}/media/{m['id']}?preview=1", headers={"Range": "bytes=0-99"})
    assert rr.status_code == 206 and len(rr.content) == 100

    proj = c.get(f"/api/projects/{pid}").json()
    proj["clips"] = [
        {"id": "v1c", "track": "v1", "media": m["id"], "srcIn": 0, "srcOut": m["duration"], "order": 0, "manual": False},
        {"id": "a1c", "track": "a1", "media": m["id"], "srcIn": 0, "srcOut": m["duration"], "linkedTo": "v1c", "volume": 1, "manual": False},
    ]
    r = c.put(f"/api/projects/{pid}", json={"project": proj, "baseRevision": proj["revision"]})
    assert r.status_code == 200, r.text
    rev = r.json()["revision"]

    pr = c.post(f"/api/projects/{pid}/proposals/silence", json={}).json()
    assert pr["items"] and pr["items"][0]["clipId"] == "v1c"
    assert len(pr["items"][0]["keep"]) == 2
    # təklif montajı dəyişmir
    assert c.get(f"/api/projects/{pid}").json()["revision"] == rev

    # əl ilə düzəlişdən sonra təklif həmin klipi atlayır
    proj = c.get(f"/api/projects/{pid}").json()
    for cl in proj["clips"]:
        cl["manual"] = True
    rev = c.put(f"/api/projects/{pid}", json={"project": proj, "baseRevision": rev}).json()["revision"]
    pr2 = c.post(f"/api/projects/{pid}/proposals/silence", json={}).json()
    assert not pr2["items"] and pr2["skippedManual"][0]["clipId"] == "v1c"

    # köhnə versiya ilə render rədd edilir, cari versiya ilə işləyir
    assert c.post(f"/api/projects/{pid}/render", json={"revision": rev - 1}).status_code == 409
    job = c.post(f"/api/projects/{pid}/render", json={"revision": rev}).json()["job"]
    for _ in range(300):
        j = c.get(f"/api/jobs/{job}").json()
        if j["status"] != "running":
            break
        time.sleep(0.1)
    assert j["status"] == "done", j
    out = c.get(j["result"]["url"])
    assert out.status_code == 200 and len(out.content) > 1000
    assert hashlib.sha256(original.read_bytes()).hexdigest() == sha_before, "orijinal dəyişməməlidir"

    st = c.get("/api/status").json()
    assert st["llm"]["available"] is False
    assert "ANTHROPIC_API_KEY" not in json.dumps(st)


@pytest.mark.skipif(not shutil.which("node"), reason="node yoxdur")
def test_timeline_js_node_suite():
    r = subprocess.run(["node", "--test", str(REPO / "tests/montaj/timeline.test.mjs")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
