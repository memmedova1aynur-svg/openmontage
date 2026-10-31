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


def test_editor_page_and_edits_roundtrip(tmp_path, monkeypatch):
    """Redaktor səhifəsi şəxsi məlumat daşımır; düzəliş faylı tətbiq olunur və render orijinaldan hazırlanır."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.montaj import editor_fixture
    from tests.montaj.test_montaj import beep_onsets, flash_onsets

    monkeypatch.setenv("MONTAJ_OUT_DIR", str(tmp_path / "out"))
    pid = editor_fixture.make(tmp_path / "data", tmp_path)
    from montaj import session, store

    assert session.main(["editor", pid]) == 0
    html = (tmp_path / "out" / pid / "editor" / "index.html").read_text()
    assert "media/originals" not in html and "drive" not in html.lower() and "window.TL" in html
    p = store.load(pid)
    v1 = [c for c in p["clips"] if c["track"] == "v1"][0]
    txt = [c for c in p["clips"] if c["track"] == "t1"][0]
    edits = {"schema": 1, "projectId": pid, "baseRevision": p["revision"],
             "clips": {v1["id"]: {"srcIn": 0.5, "srcOut": 5.5, "base": {"srcIn": 0.5, "srcOut": 3.6}}},
             "texts": {txt["id"]: {"x": 0.3, "y": 0.62, "base": {"x": None, "y": None}}}}
    f = tmp_path / "edits.json"
    f.write_text(json.dumps({"data": edits}))
    assert session.main(["apply-edits", pid, str(f)]) == 0
    p2 = store.load(pid)
    assert [c["srcOut"] for c in p2["clips"] if c["id"] == v1["id"]] == [5.5]
    bad = dict(edits, projectId="basqa")
    f.write_text(json.dumps(bad))
    assert session.main(["apply-edits", pid, str(f)]) == 2
    assert session.main(["render", pid]) == 0
    mp4 = next((tmp_path / "out" / pid).glob("*.mp4"))
    fl, bp = flash_onsets(mp4), beep_onsets(mp4)
    assert len(fl) == 8 and max(abs(a - b) for a, b in zip(fl, bp)) <= 1 / 30 + 0.005



def _fixture(tmp_path, monkeypatch):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.montaj import editor_fixture

    monkeypatch.setenv("MONTAJ_OUT_DIR", str(tmp_path / "out"))
    return editor_fixture.make(tmp_path / "data", tmp_path)


def _draft_and_analysis(pid):
    """Fixture-in saxta söz vaxtları ilə storyboard qaralaması və analiz faylı (Whisper işlədilmir)."""
    from montaj import analysis, session, store
    from tests.montaj.editor_fixture import WORDS

    p = store.load(pid)
    mid = p["media"][0]["id"]
    f = analysis.analysis_path(store.project_dir(pid), mid)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"mediaId": mid, "words": [dict(w, p=0.4 if w["w"] == "üç" else 0.95) for w in WORDS],
                             "model": "test"}), encoding="utf-8")
    frame = next(c["frame"] for c in p["clips"] if c["track"] == "v1")
    cards = [{"id": f"c{i + 1}", "mediaId": mid, "srcIn": a, "srcOut": b, "include": True,
              "words": [w for w in WORDS if a <= w["s"] and w["e"] <= b]} for i, (a, b) in enumerate([(0.5, 3.6), (6.5, 9.6)])]
    for c in cards:
        c["text"] = " ".join(w["w"] for w in c["words"])
    session._save_draft(pid, {"generator": "rules", "musicMood": "", "musicNote": "", "overallNote": "", "removed": {},
                              "subtitles": True, "candidates": {mid: [{"words": WORDS}]}, "cards": cards,
                              "frames": {mid: frame}, "status": "draft", "options": {}})
    return mid


def test_plan_look_choice_and_manual_color_kept(tmp_path, monkeypatch):
    """Rəng: standart A; seçilən şablon (C) render filtrinə düşür; əl ilə rəngə toxunulmur; "look": null götürür."""
    pid = _fixture(tmp_path, monkeypatch)
    from montaj import render, session, store

    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"captions": {"enabled": True, "style": {"type": "caption"}}}))
    assert session.main(["plan", pid, str(plan)]) == 0
    vids = [c for c in store.load(pid)["clips"] if c["track"] == "v1"]
    assert vids and all(c["adjust"]["look"] == "A" for c in vids), "standart: A (təbii)"
    plan.write_text(json.dumps({"look": "C"}))
    assert session.main(["plan", pid, str(plan)]) == 0
    v = next(c for c in store.load(pid)["clips"] if c["track"] == "v1")
    chain = render.video_chain(v, {"width": 202, "height": 360}, 202, 360, "30", False, 30)
    assert "curves=master=" in chain and "colortemperature=temperature=6700" in chain
    assert "unsharp" not in chain, "süni kəskinlik yoxdur"

    p = store.load(pid)  # bir klipin rəngi əl ilə dəyişdirilir (look işarəsi yoxdur)
    p["clips"] = [dict(c, adjust={"contrast": 1.2, "mirror": True}) if c["id"] == vids[0]["id"] else c for c in p["clips"]]
    store.save(pid, p, p["revision"])
    plan.write_text(json.dumps({"look": None}))
    assert session.main(["plan", pid, str(plan)]) == 0
    after = {c["id"]: c.get("adjust") for c in store.load(pid)["clips"] if c["track"] == "v1"}
    assert after[vids[0]["id"]] == {"contrast": 1.2, "mirror": True}, "əl ilə rəng qorunur"
    assert all(after[c["id"]] is None for c in vids[1:]), "plan şablonu götürülür"
    plan.write_text(json.dumps({"look": "Z"}))
    assert session.main(["plan", pid, str(plan)]) == 2


def test_looks_sheet(tmp_path, monkeypatch):
    """`looks`: 3 kadr × (Orijinal, A, B, C) müqayisə şəkli; aralıq fayllar silinir."""
    pid = _fixture(tmp_path, monkeypatch)
    from montaj import media, session

    assert session.main(["looks", pid]) == 0
    sheet = tmp_path / "out" / pid / "reng_variantlari.jpg"
    info = media.probe(sheet)
    assert info["width"] == 4 * 360 and info["height"] == 3 * 202, "3 sətir (640x360 mənbə → 360x202)"
    assert not list((tmp_path / "out" / pid).glob("reng_*.png"))


def test_cut_safe_boundary_keeps_words(tmp_path, monkeypatch, capsys):
    """`cut`: aralıq qaralamadan çıxarılır, sərhəd söz içinə düşmür; layihə təsdiqsiz dəyişmir."""
    pid = _fixture(tmp_path, monkeypatch)
    from montaj import session, store
    from tests.montaj.editor_fixture import WORDS

    _draft_and_analysis(pid)
    rev = store.load(pid)["revision"]
    assert session.main(["cut", pid, "1.45-1.95"]) == 0  # "iki" (2.0–2.4) saxlanmalı: aralıq onun yanındadır
    assert session.main(["cut", pid, "1.50-2.95"]) == 0  # "iki" çıxarılır
    d = session._load_draft(pid)["cards"]
    for c in d:
        for t in (c["srcIn"], c["srcOut"]):
            assert not any(w["s"] + 0.01 < t < w["e"] - 0.01 for w in WORDS), f"kəsim sözün içində: {t}"
    kept = [w["w"] for c in d for w in c["words"]]
    assert "iki" not in kept and "bir" in kept and "üç" in kept, kept
    assert len(d) == 3, "birinci kart iki yerə bölünür"
    assert store.load(pid)["revision"] == rev, "storyboard təsdiqlənmədən montaj dəyişmir"


def test_music_plan_preview_verify_words(tmp_path, monkeypatch, capsys):
    """Musiqi: plan ilə m1 trekinə (yumşaq giriş/çıxış, ducking); dinləmə nümunəsi; render yoxlaması; şübhəli sözlər."""
    import subprocess

    pid = _fixture(tmp_path, monkeypatch)
    from montaj import media, session, store

    mus = tmp_path / "sinaq_musiqi.m4a"  # yalnız test üçün sintez səs
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "sine=f=220:d=20", "-c:a", "aac", str(mus)], check=True)
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"look": None, "music": {"file": str(mus), "volume": 0.1}}))
    assert session.main(["plan", pid, str(plan)]) == 0
    p = store.load(pid)
    m1 = [c for c in p["clips"] if c["track"] == "m1"]
    assert len(m1) == 1 and m1[0]["volume"] == 0.1 and m1[0]["fadeIn"] > 0 and m1[0]["fadeOut"] > 0 and p["mix"]["duck"]
    assert session.main(["plan", pid, str(plan)]) == 0
    assert len([c for c in store.load(pid)["clips"] if c["track"] == "m1"]) == 1, "təkrar plan musiqini ikiləşdirmir"
    assert session.main(["music-preview", pid, str(mus), "--seconds", "5"]) == 0
    prev = tmp_path / "out" / pid / "musiqi_1.m4a"
    assert media.probe(prev)["hasAudio"] and 4.5 < media.probe(prev)["duration"] < 5.6
    assert session.main(["render", pid]) == 0
    _draft_and_analysis(pid)
    capsys.readouterr()
    assert session.main(["verify", pid, "--no-asr"]) == 0
    out = capsys.readouterr().out
    assert "kəsim sərhədi" in out and "səs/görüntü uzunluğu" in out and "yoxlanılmayıb" in out
    assert session.main(["words", pid]) == 0
    assert "“üç”" in capsys.readouterr().out, "aşağı əminlikli söz siyahıda"


def test_variants_and_choose(tmp_path, monkeypatch):
    """2 storyboard variantı önizlənir (layihə dəyişmir); seçilən variant tətbiq olunur."""
    pid = _fixture(tmp_path, monkeypatch)
    from montaj import media, session, store

    _draft_and_analysis(pid)
    rev = store.load(pid)["revision"]
    a = tmp_path / "A.json"
    b = tmp_path / "B.json"
    a.write_text(json.dumps({"title": "Sakit", "look": "A", "graphics": [{"type": "title", "text": "Başlıq A", "start": 0.2, "dur": 2}]}))
    b.write_text(json.dumps({"title": "Dinamik", "look": "C", "storyboard": {"order": [2, 1]},
                             "graphics": [{"type": "card", "heading": "Kart", "text": "B", "start": 1, "dur": 2}]}))
    assert session.main(["variants", pid, str(a), str(b)]) == 0
    o = tmp_path / "out" / pid
    assert media.probe(o / "storyboard_variantlari.jpg")["height"] > 400
    assert media.probe(o / "variant_B.mp4")["width"] == 540
    assert store.load(pid)["revision"] == rev, "önizləmə layihəni dəyişmir"
    assert session.main(["choose", pid, str(b)]) == 0
    p = store.load(pid)
    assert any(c.get("type") == "card" for c in p["clips"]) and p["planApplied"]["look"] == "C"
