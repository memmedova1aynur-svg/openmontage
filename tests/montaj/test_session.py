"""Sessiya CLI-si: Drive linki -> storyboard -> düzəliş -> tətbiq -> render -> layihə faylı."""

from __future__ import annotations

import http.server
import json
import shutil
import threading

import pytest

pytestmark = pytest.mark.skipif(not (shutil.which("ffmpeg") and shutil.which("node")), reason="ffmpeg/node yoxdur")

from tests.montaj.test_montaj import make_silence_source, make_sync_source  # noqa: E402
from tests.montaj.test_v2 import _FakeDrive  # noqa: E402


def test_session_cli_end_to_end(tmp_path, monkeypatch, capsys):
    from montaj import media, session, store

    src = make_silence_source(tmp_path / "s.mp4")
    big = make_sync_source(tmp_path / "big.mp4")
    _FakeDrive.payload = src.read_bytes()
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _FakeDrive)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setenv("MONTAJ_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("MONTAJ_OUT_DIR", str(tmp_path / "out"))
    monkeypatch.setattr(session.drive, "DOWNLOAD_URL", f"http://127.0.0.1:{srv.server_port}/download")
    try:
        assert session.main(["new", "--title", "Sınaq", "--link", "https://drive.google.com/file/d/PUBLICPUBLICPUBLICPUBLIC/view",
                             "--file", str(big), "--client", "Lamiyə", "--goal", "sales"]) == 0
    finally:
        srv.shutdown()
    pid = "sinaq"
    p = store.load(pid)
    assert [m["source"]["type"] for m in p["media"]] == ["drive", "upload"]
    orig = store.project_dir(pid) / p["media"][0]["file"]
    assert orig.read_bytes() == src.read_bytes(), "Drive orijinalı dəyişmədən saxlanılır"
    assert (p["width"], p["height"]) == (202, 360), "çıxış ölçüsü ən böyük mənbəyə görədir"
    assert p["brand"]["name"] == "Lamiyə"
    assert session.main(["storyboard", pid]) == 0
    out = tmp_path / "out" / pid
    assert (out / "storyboard.jpg").stat().st_size > 5000
    assert session.main(["edit", pid, "--exclude", "2", "--text", "1=Salam"]) == 0
    sb = json.loads((store.project_dir(pid) / "storyboard_draft.json").read_text())
    assert sb["cards"][1]["include"] is False and sb["cards"][0]["onScreenText"] == "Salam"
    rev_before = store.load(pid)["revision"]
    assert store.load(pid)["clips"] == [], "storyboard təsdiqlənmədən montaj boşdur"
    assert session.main(["apply", pid]) == 0
    p2 = store.load(pid)
    assert p2["revision"] > rev_before and any(c.get("text") == "Salam" for c in p2["clips"])
    assert session.main(["render", pid]) == 0
    mp4 = next(out.glob("*.mp4"))
    info = media.probe(mp4)
    assert info["hasVideo"] and info["hasAudio"] and (info["width"], info["height"]) == (202, 360)
    assert session.main(["export", pid]) == 0
    exported = json.loads((out / f"{pid}.montaj.json").read_text())
    assert exported["id"] == pid and exported["clips"], "panel formatında layihə faylı"
    capsys.readouterr()


def test_session_cli_bad_link_message(tmp_path, monkeypatch, capsys):
    from montaj import session

    monkeypatch.setenv("MONTAJ_DATA_DIR", str(tmp_path / "data"))
    rc = session.main(["new", "--title", "X", "--link", "https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUvWxYz0"])
    err = capsys.readouterr().err
    assert rc == 2 and "Qovluq linki" in err and "NƏ ETMƏLİ" in err
