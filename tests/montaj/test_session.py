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


def test_framefix_tilt_and_center(tmp_path):
    """Əyrilik fondakı xətlərdən ölçülür (işarə ffmpeg rotate ilə uyğun); ortalama pəncərəsi həddi aşmır."""
    import subprocess

    from montaj import framefix

    src = tmp_path / "xetler.mp4"  # üfüqi zolaqlar, 2.5° saat əqrəbi istiqamətində fırladılmış
    vf = ("drawbox=y=500:w=iw:h=6:color=white:t=fill,drawbox=y=900:w=iw:h=6:color=white:t=fill,"
          "drawbox=y=1300:w=iw:h=6:color=white:t=fill,rotate=2.5*PI/180:ow=iw:oh=ih:c=gray")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=gray:s=1080x1920:d=2", "-vf", vf,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(src)], check=True)
    t = framefix.detect_tilt(src, 0, 2)
    assert t["angle"] is not None and 2.0 < t["angle"] < 3.0, t
    flat = tmp_path / "duz.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=gray:s=1080x1920:d=2", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", str(flat)], check=True)
    assert framefix.detect_tilt(flat, 0, 2)["angle"] is None, "xətt yoxdursa bucaq uydurulmur"
    s, cx, cy = framefix.center_window(0.62, 0.2, 1.12)
    assert s >= 1 / 1.12 - 1e-6 and cx > 0.5 and abs(cx - 0.62) < 0.08, "qismən ortalama, yaxınlaşma həddində"
    assert framefix.center_window(0.51, 0.2, 1.12)[0] == 1.0, "artıq ortadadırsa yaxınlaşma yoxdur"


def test_broll_cover_pip_insert(tmp_path, monkeypatch):
    """B-roll: cover (danışıq + altyazı davam edir), pip (küncdə), insert (əsas video təbii pauzada dayanır).
    B-roll mediası storyboard kartlarına düşmür."""
    import subprocess

    import numpy as np

    pid = _fixture(tmp_path, monkeypatch)
    from montaj import media, render, server, session, store

    red = tmp_path / "qirmizi.mp4"   # 16:9, səssiz — cover və pip üçün
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=red:s=640x360:d=5", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", str(red)], check=True)
    blue = tmp_path / "goy.mp4"      # səsli — insert üçün
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=blue:s=360x640:d=3", "-f", "lavfi",
                    "-i", "sine=f=880:d=3", "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(blue)], check=True)
    assert session.main(["add-broll", pid, "--file", str(red), "--file", str(blue)]) == 0
    p = store.load(pid)
    assert sum(1 for m in p["media"] if m.get("role") == "broll") == 2
    sb = server.build_storyboard(pid, {"aspect": "9:16", "useAi": False})
    brolls = {m["id"] for m in p["media"] if m.get("role") == "broll"}
    assert not any(c["mediaId"] in brolls for c in sb["cards"]), "B-roll storyboard kartına düşmür"

    before = sum(c["srcOut"] - c["srcIn"] for c in session.node_tl("videoClips", p))
    def sub_text(x):
        return " ".join(c["text"] for c in sorted((c for c in x["clips"] if c["track"] == "c1" and not c.get("hidden")),
                                                   key=lambda c: c["start"]))
    subs_before = sub_text(p)
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"look": None, "broll": [
        {"name": "qirmizi.mp4", "mode": "cover", "at": 1.0, "dur": 1.5},
        {"name": "qirmizi.mp4", "mode": "pip", "at": 4.5, "dur": 1.0, "scale": 0.4, "x": 0.7, "y": 0.3},
        {"name": "goy.mp4", "mode": "insert", "at": 5.0, "dur": 1.0}]}))
    assert session.main(["plan", pid, str(plan)]) == 0
    q = store.load(pid)
    after = sum(c["srcOut"] - c["srcIn"] for c in session.node_tl("videoClips", q))
    assert abs(after - before - 1.0) < 0.01, "insert müddəti əlavə edir"
    assert sub_text(q) == subs_before, "altyazı sözləri itmir (insert yerində altyazı iki yerə bölünə bilər)"
    assert len([c for c in q["clips"] if c["track"] == "v2"]) == 2
    assert session.main(["plan", pid, str(plan)]) == 0, "təkrar plan"
    q2 = store.load(pid)
    assert len([c for c in q2["clips"] if c["track"] == "v2"]) == 2 and \
        abs(sum(c["srcOut"] - c["srcIn"] for c in session.node_tl("videoClips", q2)) - after) < 0.01, "ikiləşmir"

    assert session.main(["render", pid]) == 0
    mp4 = sorted((tmp_path / "out" / pid).glob(f"{pid}_r*.mp4"))[-1]
    W, H = q2["width"], q2["height"]

    def frame(t):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", str(mp4), "-frames:v", "1", "-f", "rawvideo",
                              "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        return np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(int)

    f = frame(1.7)
    assert f[H // 2, W // 2, 0] > 180 and f[H // 2, W // 2, 2] < 80, "cover: kadr B-roll ilə örtülür"
    f = frame(0.5)
    assert not (f[H // 2, W // 2, 0] > 180 and f[H // 2, W // 2, 2] < 80), "cover-dən əvvəl əsas video"
    seq = session.node_tl("videoClips", q2)
    acc, ins = 0.0, None
    for c in seq:
        if c.get("broll"):
            ins = acc
        acc += c["srcOut"] - c["srcIn"]
    f = frame(round(ins + 0.5, 2))
    assert f[H // 2, W // 2, 2] > 180 and f[H // 2, W // 2, 0] < 80, "insert: göy kadr"
    assert media.probe(mp4)["duration"] > before + 0.9


def test_voice_clean_render_uses_clean_track(tmp_path, monkeypatch):
    """Arxa səs təmizləmə: təmizlənmiş nüsxə eyni uzunluqda yazılır, orijinal dəyişmir, render danışıq qatında
    onu işlədir; "off" söndürür. Model yoxdursa test atlanır."""
    import hashlib

    from montaj import voiceclean
    st = voiceclean.available()
    if not (st["installed"] and st["model"]):
        pytest.skip("DeepFilterNet quraşdırılmayıb")
    pid = _fixture(tmp_path, monkeypatch)
    from montaj import media, render, session, store

    p = store.load(pid)
    m = p["media"][0]
    orig = store.project_dir(pid) / m["file"]
    h0 = hashlib.sha1(orig.read_bytes()).hexdigest()
    assert session.main(["voice-clean", pid, "--mode", "on"]) == 0
    q = store.load(pid)
    vc = q["voiceClean"][m["id"]]
    cf = store.project_dir(pid) / vc["file"]
    assert cf.is_file() and abs(media.probe(cf)["duration"] - m["duration"]) < 0.05, "eyni uzunluq (sinxron)"
    assert hashlib.sha1(orig.read_bytes()).hexdigest() == h0, "orijinal dəyişmir"
    cmd = render.build_command(q, store.project_dir(pid), tmp_path / "x.mp4", tmp_path)
    assert any(str(a).endswith(".clean.wav") for a in cmd), "render təmizlənmiş danışığı işlədir"
    assert session.main(["voice-clean", pid, "--mode", "off"]) == 0
    assert store.load(pid)["voiceClean"] == {}


def test_broll_insert_near_clip_boundary(tmp_path, monkeypatch):
    """Araya kadr vaxtı klip sərhədinə çox yaxın olanda (bölmə mümkün deyil) həmin sərhədə qoyulur."""
    import subprocess

    pid = _fixture(tmp_path, monkeypatch)
    from montaj import session, store

    blue = tmp_path / "goy.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=blue:s=360x640:d=2", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", str(blue)], check=True)
    assert session.main(["add-broll", pid, "--file", str(blue)]) == 0
    p = session.node_tl("migrate", store.load(pid))
    seq = session.node_tl("videoClips", p)
    edge = seq[0]["srcOut"] - seq[0]["srcIn"]  # birinci klipin sonu (zaman xəttində)
    q = session._apply_broll(pid, p, {"name": "goy.mp4", "mode": "insert", "at": edge + 0.05, "dur": 1.0})
    seq2 = session.node_tl("videoClips", q)
    assert [c.get("broll", False) for c in seq2] == [False, True, False], "sərhədə qoyulur, klip bölünmür"


def test_claude_broll_scene_render_and_plan(tmp_path, monkeypatch):
    """Claude-un hazırladığı B-roll: kataloq; səhnə layihə rəngində render olunur (keş), plan "make" ilə
    insert kimi qoyulur, təkrar plan media ikiləşdirmir. Remotion yoxdursa atlanır."""
    from montaj import sceneclip
    if not sceneclip.NODE_MODULES.is_dir():
        pytest.skip("remotion-composer/node_modules yoxdur")
    pid = _fixture(tmp_path, monkeypatch)
    from montaj import media, session, store

    cat = sceneclip.catalog()
    assert len(cat) >= 30 and {"checklist", "stat", "chat", "timeline"} <= set(cat) and "items" in cat["checklist"]["props"]
    before = sum(c["srcOut"] - c["srcIn"] for c in session.node_tl("videoClips", store.load(pid)))
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"look": None, "broll": [{"make": {"kind": "checklist", "props": {
        "label": "Sınaq", "title": "Üç addım", "items": ["bir", "iki", "üç"], "times": [0.1, 0.4, 0.7]}},
        "mode": "insert", "at": 1.0, "dur": 1.5}]}))
    assert session.main(["plan", pid, str(plan)]) == 0
    p = store.load(pid)
    gen = [m for m in p["media"] if (m.get("source") or {}).get("type") == "generated"]
    assert len(gen) == 1 and gen[0]["role"] == "broll"
    assert media.probe(store.project_dir(pid) / gen[0]["file"])["width"] == 1080
    after = sum(c["srcOut"] - c["srcIn"] for c in session.node_tl("videoClips", p))
    assert abs(after - before - 1.5) < 0.02, "insert müddəti əlavə edir"
    assert session.main(["plan", pid, str(plan)]) == 0
    assert len([m for m in store.load(pid)["media"] if (m.get("source") or {}).get("type") == "generated"]) == 1, "keş: ikiləşmir"


def test_loudness_delivery_retakes(tmp_path, monkeypatch):
    """Render səsi −14 LUFS-a gətirir (video kopyalanır); böyük fayl üçün yüngül nüsxə; təkrar cümlə tapılır."""
    import subprocess

    pid = _fixture(tmp_path, monkeypatch)
    from montaj import quality, render, session

    assert session.main(["render", pid]) == 0
    mp4 = sorted((tmp_path / "out" / pid).glob(f"{pid}_r*.mp4"))[-1]
    lo = render.measure_loudness(mp4)
    assert lo and abs(lo["input_i"] - render.LOUDNESS_TARGET) < 1.0 and lo["input_tp"] <= -1.0
    big = tmp_path / "big.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=1080x1920:d=4", "-f", "lavfi", "-i",
                    "sine=d=4", "-shortest", "-c:v", "libx264", "-crf", "0", "-c:a", "aac", str(big)], check=True)
    cap = big.stat().st_size / 1e6 / 3
    ig = render.delivery_copy(big, tmp_path / "ig.mp4", cap_mb=cap)
    assert ig and ig.stat().st_size / 1e6 <= cap * 1.05
    assert render.delivery_copy(ig, tmp_path / "x.mp4", cap_mb=cap * 2) is None, "kiçik faylda nüsxə yoxdur"

    def W(txt, t0):
        return [{"w": w, "s": round(t0 + i * 0.35, 2), "e": round(t0 + i * 0.35 + 0.3, 2)} for i, w in enumerate(txt.split())]
    words = W("Salam əziz analar.", 0) + W("Bu gün sizə laktasiya haqqında", 1.6) + W("Bu gün sizə laktasiya haqqında danışacam.", 4.0) + W("Sonra su için.", 7.5)
    r = quality.find_retakes(words)
    assert len(r) == 1 and r[0]["drop"]["s"] == 1.6 and r[0]["drop"]["e"] == 4.0
    assert quality.find_retakes(W("Bir iki üç dörd.", 0) + W("Beş altı yeddi.", 2)) == []


def test_glossary_save_restore_layout_lowlight(tmp_path, monkeypatch):
    """Müştəri lüğəti (fix-word --remember + plan); layihə paketi bərpası; kart təhlükəsiz zonada; D (zəif işıq)."""
    import shutil as sh

    pid = _fixture(tmp_path, monkeypatch)
    from montaj import quality, render, session, store

    prof = tmp_path / "test-musteri.json"
    prof.write_text(json.dumps({"name": "Test Müştəri", "theme": session.DEFAULT_SCENE_THEME}), encoding="utf-8")
    monkeypatch.setattr(session, "profile_path", lambda name: prof)
    monkeypatch.setattr(session, "expert_profile", lambda name: json.loads(prof.read_text(encoding="utf-8")))
    p = store.load(pid)
    p["brand"] = {"name": "Test Müştəri"}
    store.save(pid, p, p["revision"])
    assert session.main(["fix-word", pid, "yeddi", "Yeddi", "--remember"]) == 0
    g = json.loads(prof.read_text(encoding="utf-8"))["glossary"]
    assert g["fixes"] == [{"from": "yeddi", "to": "Yeddi"}] and session.glossary_terms(json.loads(prof.read_text())) == ["Yeddi"]

    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"look": "D", "graphics": [{"type": "title", "text": "Yuxarıda başlıq", "start": 0.2, "dur": 2, "y": 0.02}]}))
    assert session.main(["plan", pid, str(plan)]) == 0
    q = store.load(pid)
    assert any(c.get("from") == "yeddi" for c in q["subtitles"]["corrections"]), "lüğət düzəlişi plana düşür"
    v = next(c for c in q["clips"] if c["track"] == "v1")
    assert "hqdn3d" in ",".join(render.color_filters(v["adjust"])) and v["adjust"]["look"] == "D"
    lay = quality.layout_check(q, store.project_dir(pid), tmp_path / "lay")
    assert any("yuxarı" in x["what"] for x in lay), lay

    pack = tmp_path / "paket.tar.gz"
    assert session.main(["save", pid, "--out", str(pack)]) == 0
    m = q["media"][0]
    orig = store.project_dir(pid) / m["file"]
    keep = tmp_path / "orijinal.mp4"
    sh.copyfile(orig, keep)
    monkeypatch.setenv("MONTAJ_DATA_DIR", str(tmp_path / "data2"))
    monkeypatch.setenv("MONTAJ_OUT_DIR", str(tmp_path / "out2"))
    assert session.main(["restore", str(pack), "--file", f"{m['id']}={keep}"]) == 0
    r = store.load(pid)
    assert r["revision"] == q["revision"] and r["clips"] == q["clips"]
    assert (store.project_dir(pid) / m["file"]).read_bytes() == keep.read_bytes()


def test_ad_scan_plan_variants(tmp_path, monkeypatch, capsys):
    """Reklam: faktlar danışıqdan tapılır (qiymət, tarix, yer, çağırış, fayda), uydurulmur; 3 plan; plan render olunur."""
    pid = _fixture(tmp_path, monkeypatch)
    from montaj import ad, analysis, graphics, session, store

    def W(txt, t0):
        return [{"w": w, "s": round(t0 + i * 0.3, 2), "e": round(t0 + i * 0.3 + 0.25, 2), "p": 0.9} for i, w in enumerate(txt.split())]
    words = (W("Satışda çətinlik çəkirsiniz?", 0.5) + W("Təlimdə danışmağı öyrənəcəksiniz.", 1.6) + W("Qiyməti 250 manat.", 6.6)
             + W("Cəmi 10 yer var.", 7.9) + W("Şərhlərdə SATIŞ yazın.", 9.0))
    p = store.load(pid)
    mid = p["media"][0]["id"]
    f = analysis.analysis_path(store.project_dir(pid), mid)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"mediaId": mid, "words": words, "model": "test"}), encoding="utf-8")
    frame = next(c["frame"] for c in p["clips"] if c["track"] == "v1")
    cards = [{"id": "c1", "mediaId": mid, "srcIn": 0.3, "srcOut": 10.5, "include": True, "words": words, "text": ""}]
    session._save_draft(pid, {"generator": "rules", "musicMood": "", "musicNote": "", "overallNote": "", "removed": {},
                              "subtitles": True, "candidates": {mid: [{"words": words}]}, "cards": cards, "frames": {mid: frame},
                              "status": "draft", "options": {}})
    r = ad.scan(words)
    kinds = {x["kind"]: x for x in r["facts"]}
    assert r["offer"] == "təlim" and kinds["price"]["value"] == "250 AZN" and kinds["seats"]["value"] == "Son 10 yer"
    assert kinds["cta"]["keyword"] == "SATIŞ" and "benefit" in kinds
    assert ad.scan(W("Bu gün hava gözəldir.", 0))["facts"] == [], "fakt yoxdursa heç nə uydurulmur"
    assert session.main(["ad-scan", pid]) == 0 and session.main(["ad-plan", pid]) == 0
    o = tmp_path / "out" / pid
    plans = {k: json.loads((o / f"ad_plan_{k}.json").read_text(encoding="utf-8")) for k in "ABC"}
    types = {k: {g["type"] for g in v["graphics"]} for k, v in plans.items()}
    assert all({"offer", "cta", "badge"} <= t for t in types.values()) and "list" in types["B"] and plans["C"]["broll"]
    cta = next(g for g in plans["A"]["graphics"] if g["type"] == "cta")
    assert cta["keyword"] == "SATIŞ" and abs(cta["start"] - (9.0 - 0.3)) < 0.05, "vaxt zaman xəttinə çevrilir"
    assert {"offer", "cta", "badge"} <= graphics.TYPES
    (o / "plan_A.json").write_text(json.dumps({k: v for k, v in plans["A"].items() if not k.startswith("_")}), encoding="utf-8")
    assert session.main(["choose", pid, str(o / "plan_A.json")]) == 0
    assert session.main(["render", pid]) == 0
    assert any(c.get("type") == "offer" for c in store.load(pid)["clips"])


def test_seminar_highlights_extract(tmp_path, monkeypatch, capsys):
    """Seminar: müstəqil hissələr (təşkilati/asılı başlanğıc seçilmir), hissə ayrıca layihəyə çıxır —
    orijinal hard link (surət yox), analiz təkrar istifadə olunur, kart aralığı düzgündür."""
    pid = _fixture(tmp_path, monkeypatch)
    from montaj import analysis, seminar, session, store

    def W(txt, t0):
        return [{"w": w, "s": round(t0 + i * 0.35, 2), "e": round(t0 + i * 0.35 + 0.3, 2), "p": 0.9} for i, w in enumerate(txt.split())]
    words, t = [], 0.0
    for s in ["Salam, xoş gəlmisiniz.", "Niyə uşaq ağlayanda onu susdurmaq səhvdir?", "Çünki hissini tanımır.",
              "Yəni, ən vacib addım hissi tanımaqdır.", "Kimin sualı var?", "Bu barədə sonra danışarıq."]:
        ws = W(s, t); words += ws; t = ws[-1]["e"] + 0.9
    hs = seminar.highlights(words, min_s=3, max_s=12)
    assert hs and hs[0]["start_text"].startswith("Niyə") and hs[0]["end_text"].endswith("tanımaqdır.")
    assert not any(h["start_text"].startswith(("Salam", "Kimin", "Bu")) for h in hs)

    p = store.load(pid)
    m = p["media"][0]
    f = analysis.analysis_path(store.project_dir(pid), m["id"])
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"mediaId": m["id"], "words": [dict(w, s=w["s"] + 0.5, e=w["e"] + 0.5) for w in words], "model": "test"}))
    assert session.main(["highlights", pid, "--min", "3", "--max", "12"]) == 0
    assert "extract" in capsys.readouterr().out
    assert session.main(["extract", pid, f"{m['id']}:2.0-6.5", "--title", "Hissə bir"]) == 0
    c = store.load("hisse-bir")
    assert c["parent"]["id"] == pid and c["width"] == p["width"] and [x["id"] for x in c["media"]] == [m["id"]]
    a_src, a_dst = store.project_dir(pid) / m["file"], store.project_dir("hisse-bir") / m["file"]
    assert a_dst.stat().st_ino == a_src.stat().st_ino or a_dst.read_bytes() == a_src.read_bytes()
    assert analysis.analysis_path(store.project_dir("hisse-bir"), m["id"]).is_file(), "analiz təkrar istifadə olunur"
    card = session._load_draft("hisse-bir")["cards"][0]
    assert (card["srcIn"], card["srcOut"]) == (2.0, 6.5) and all(2.0 - 0.02 <= w["s"] and w["e"] <= 6.55 for w in card["words"])


def test_motion_graphics_scenes_scan_cover_pip(tmp_path, monkeypatch):
    """Motion graphics: 7 qrafik səhnə render olunur; danışıqdakı rəqəmlər tapılır (birləşmir); cover_pip-də
    səhnə kadrı tutur, danışan isə dairədə görünür. Remotion yoxdursa atlanır."""
    import subprocess

    import numpy as np

    from montaj import ad, sceneclip
    if not sceneclip.NODE_MODULES.is_dir():
        pytest.skip("remotion-composer/node_modules yoxdur")

    def W(txt, t0=0):
        return [{"w": w, "s": round(t0 + i * 0.35, 2), "e": round(t0 + i * 0.35 + 0.3, 2)} for i, w in enumerate(txt.split())]
    r = ad.scan_numbers(W("2022-ci ildə 120, 2023-də 260, 2024-də 410.") + W("Əvvəl 8 saat, indi isə 1 saat.", 6) + W("Bu gün hava gözəldir.", 10))
    assert [n["value"] for n in r[0]["numbers"]] == [2022, 120, 2023, 260, 2024, 410] and r[0]["suggest"].startswith("mg_line")
    assert r[1]["suggest"] == "mg_compare" and len(r) == 2, "rəqəmsiz cümlə siyahıya düşmür"

    cat = sceneclip.catalog()
    mg = {"mg_bar": {"items": [{"label": "A", "value": 3}]}, "mg_line": {"points": [{"label": "1", "value": 1}, {"label": "2", "value": 2}]},
          "mg_donut": {"value": 50}, "mg_compare": {"a": {"label": "A", "value": 1}, "b": {"label": "B", "value": 2}},
          "mg_steps": {"steps": ["bir", "iki"]}, "mg_code": {"lines": ["print(1)"]}, "mg_kpi": {"items": [{"value": 1200, "label": "x"}]}}
    assert set(mg) <= set(cat)
    th = {"primary": "#203040", "primaryDeep": "#101820", "accent": "#F2C94C", "accentSoft": "#DDDDDD", "text": "#FFFFFF", "onAccent": "#101820", "cardAlpha": 0.94}
    for k, props in mg.items():
        png = sceneclip.render(k, props, 2.0, th, tmp_path / "scenes", still=True)
        assert png.stat().st_size > 10000, k

    pid = _fixture(tmp_path, monkeypatch)
    from montaj import session, store

    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"look": None, "broll": [{"make": {"kind": "mg_donut", "props": {"value": 50}}, "mode": "cover_pip", "at": 0.5, "dur": 2.0}]}))
    assert session.main(["plan", pid, str(plan)]) == 0
    assert session.main(["render", pid]) == 0
    mp4 = sorted((tmp_path / "out" / pid).glob(f"{pid}_r*.mp4"))[-1]
    q = store.load(pid)
    Wd, Hd = q["width"], q["height"]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "1.5", "-i", str(mp4), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(Hd, Wd, 3).astype(int)
    D = int(Wd * 0.3) // 2 * 2
    cx, cy = int(Wd * 0.07) + D // 2, int(Hd * 0.6)
    inside = fr[cy - D // 6: cy + D // 6, cx - D // 6: cx + D // 6]
    scene_bg = fr[int(Hd * 0.08), Wd // 2]
    assert np.abs(inside.mean(axis=(0, 1)) - scene_bg).sum() > 30, "dairədə danışanın görüntüsü olmalıdır (səhnə fonu deyil)"
    th0 = session.DEFAULT_SCENE_THEME  # fixture-də müştəri yoxdur → neytral tema; fon primary → primaryDeep qradiyenti
    hexrgb = lambda h: np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)])
    px = fr[int(Hd * 0.3), int(Wd * 0.9)]
    assert min(np.abs(px - hexrgb(th0["primary"])).sum(), np.abs(px - hexrgb(th0["primaryDeep"])).sum()) < 45, "dairədən kənarda səhnə kadrı tutur"


def test_tale_plan_scenes_sticker(tmp_path, monkeypatch):
    """Nağıl: obraz/məkan/hərəkət danışıqdan, obraz yeri video boyu eyni, kitabxanada olmayan obraz uydurulmur;
    tale_scene render olunur; şəffaf obraz (sticker) real kadrın üstündə alfa ilə görünür."""
    import subprocess

    import numpy as np

    from montaj import sceneclip, tale

    def W(txt, t0):
        return [{"w": w, "s": round(t0 + i * 0.4, 2), "e": round(t0 + i * 0.4 + 0.35, 2)} for i, w in enumerate(txt.split())]
    words, t = [], 0.0
    for s in ["Meşədə bir tülkü yaşayırmış.", "Tülkü dovşanla rastlaşdı.", "Tülkü dedi: «Gəl dost olaq».", "Dovşan sevindi.", "Canavar baxırdı."]:
        ws = W(s, t); words += ws; t = ws[-1]["e"] + 0.8
    r = tale.plan(words, lambda x: round(x, 2), t)
    scenes = [b["make"]["props"] for b in r["broll"]]
    assert r["_characters"] == ["fox", "rabbit"] and scenes[0]["bg"] == "forest"
    fox_x = {c["x"] for s in scenes for c in s["chars"] if c["kind"] == "fox"}
    assert len(fox_x) == 1, "obraz öz yerində qalır"
    assert any(c.get("action") == "talk" for c in scenes[2]["chars"]) and scenes[3]["chars"][0]["action"] == "jump"
    assert any("canavar" in x for x in r["_review"]) and not any(c["kind"] == "wolf" for s in scenes for c in s["chars"])
    if not sceneclip.NODE_MODULES.is_dir():
        pytest.skip("remotion-composer/node_modules yoxdur")
    th = {"primary": "#203040", "primaryDeep": "#101820", "accent": "#F2C94C", "accentSoft": "#DDDDDD", "text": "#FFFFFF", "onAccent": "#101820", "cardAlpha": 0.94}
    assert sceneclip.render("tale_scene", scenes[1], 2.0, th, tmp_path / "scenes", still=True).stat().st_size > 20000

    pid = _fixture(tmp_path, monkeypatch)
    from montaj import session, store

    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"look": None, "broll": [{"make": {"kind": "tale_char", "props": {"transparent": True,
        "char": {"kind": "fox", "x": 540, "y": 1500, "scale": 2.0, "enterFrom": "none"}}}, "mode": "sticker", "at": 0.3, "dur": 2.0}]}))
    assert session.main(["plan", pid, str(plan)]) == 0
    gen = [m for m in store.load(pid)["media"] if (m.get("source") or {}).get("type") == "generated"]
    assert gen and gen[0]["file"].endswith(".mov"), "şəffaf obraz ProRes 4444 (alfa)"
    assert session.main(["render", pid]) == 0
    mp4 = sorted((tmp_path / "out" / pid).glob(f"{pid}_r*.mp4"))[-1]
    q = store.load(pid)
    Wd, Hd = q["width"], q["height"]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "1.5", "-i", str(mp4), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(Hd, Wd, 3).astype(int)
    body = fr[int(Hd * (1500 - 120 * 2) / 1920), int(Wd * (540 - 125) / 1080)]  # tülkünün gövdəsinin yan hissəsi (narıncı; ortası ağ qarındır)
    assert body[0] > 170 and body[2] < 120, f"obraz görünür: {body}"
    corner = fr[int(Hd * 0.1), int(Wd * 0.1)]
    assert not (corner[0] > 170 and corner[2] < 120), "obrazdan kənarda əsas video (alfa şəffafdır)"


def test_video_carousel(tmp_path, monkeypatch):
    """Video karusel: sıra sözləri ilə fikir slaydları, örtük/çağırış, slayd əsas montajdan kəsilir (əsas dəyişmir),
    hər slayd 1080x1350 MP4, sayğac və başlıq; örtük və ümumi şəkil."""
    import subprocess

    from montaj import carousel

    def W(txt, t0):
        return [{"w": w, "s": round(t0 + i * 0.4, 2), "e": round(t0 + i * 0.4 + 0.35, 2)} for i, w in enumerate(txt.split())]
    words, t = [], 0.0
    for s in ["Satışda üç səhv var.", "Birincisi, qiymət yazmırsınız heç vaxt orada.", "Bu müştərini itirir tamamilə.",
              "İkincisi, cavab gec gəlir sizdən.", "Müştəri gözləmir.", "Üçüncüsü, çağırış yoxdur sonda heç.", "Direktə yazın."]:
        ws = W(s, t); words += ws; t = ws[-1]["e"] + 0.5
    ideas = carousel.split_ideas(words, min_s=1.0)
    assert [i["first"].split()[0] for i in ideas] == ["Satışda", "Birincisi,", "İkincisi,", "Üçüncüsü,"]
    r = carousel.plan(words, lambda x: x, t, {"tl": words[-1]["s"], "value": "Direktə yazın", "keyword": ""})
    sl = r["slides"]
    assert len(sl) == 3 and sl[0]["cover"] and sl[0]["title"].startswith("Satışda") and sl[-1].get("cta")
    assert sl[1]["title"].startswith("Cavab"), sl[1]["title"]
    assert all(s["to"] - s["from"] <= carousel.MAX_SLIDE + 1 for s in sl)
    assert all(x["to"] <= y["from"] for x, y in zip(sl, sl[1:])), "slaydlar üst-üstə düşmür"

    pid = _fixture(tmp_path, monkeypatch)
    from montaj import session, store

    before = json.dumps(store.load(pid)["clips"], sort_keys=True)
    q = session.node_tl("migrate", store.load(pid))
    total = sum(c["srcOut"] - c["srcIn"] for c in session.node_tl("videoClips", q))
    part = carousel.slice_project(q, 1.0, 4.0, session.node_tl)
    assert abs(sum(c["srcOut"] - c["srcIn"] for c in session.node_tl("videoClips", part)) - 3.0) < 0.05
    plan = tmp_path / "carousel.json"
    plan.write_text(json.dumps({"slides": [{"from": 0, "to": 3.0, "title": "Vacib mövzu", "cover": True},
                                           {"from": 3.0, "to": round(total, 2), "title": "İkinci fikir", "cta": {"text": "Yazın"}}]}))
    assert session.main(["carousel", pid, str(plan)]) == 0
    assert json.dumps(store.load(pid)["clips"], sort_keys=True) == before, "əsas montaj dəyişmir"
    o = tmp_path / "out" / pid / "carousel"
    for i, d in ((1, 3.0), (2, total - 3.1)):
        info = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                               "-of", "json", str(o / f"slide_{i:02d}.mp4")], capture_output=True, text=True, check=True).stdout
        js = json.loads(info)
        assert (js["streams"][0]["width"], js["streams"][0]["height"]) == (1080, 1350)
        assert abs(float(js["format"]["duration"]) - d) < 0.3
    assert (o / "ortuk.jpg").stat().st_size > 5000 and (o / "karusel.jpg").stat().st_size > 5000


def test_video_type_registry(tmp_path, monkeypatch, capsys):
    """Növ reyestri: ardıcıllıq, sorğu, layihədə növ qeydi, növün formatı, verify qaydaları, müştəri tarixçəsi."""
    from pathlib import Path

    from montaj import types

    fam = [n for f in types.FAMILIES.values() for n in f["types"]]
    assert sorted(fam) == sorted(types.TYPES), "hər növ bir ailədədir"
    for n, t in types.TYPES.items():
        assert all(a in types.APPROACHES for a in t["approaches"]) and t["status"] in types.STATUS_LABEL
        assert len(t["variants"]) == 3 or t["status"] == "planned", n
        assert t["status"] == "ready" or t.get("gaps"), f"{n}: çatışmayan yazılmalıdır"
        for r in t.get("rules", []):
            assert r in ("source_order", "horizontal", "graphic_numbers_spoken")
    doc = (Path(__file__).resolve().parents[2] / "templates/expert-reels/VIDEO_TYPES.md").read_text(encoding="utf-8")
    assert all(f"| {n} |" in doc for n in types.TYPES), "VIDEO_TYPES.md ilə reyestr uyğundur"
    sv = types.survey()
    assert len(sv["family"]) <= 4 and all(2 <= len(v) <= 4 for v in sv["type_by_family"].values())
    assert not any(o["type"] == 17 for v in sv["type_by_family"].values() for o in v), "planlaşdırılan növ sorğuda yoxdur"
    assert types._numbers("350 AZN, 1 200 nəfər, 4,5 ay") == {350, 1200, 4}

    pid = _fixture(tmp_path, monkeypatch)
    from montaj import session, store

    _draft_and_analysis(pid)
    assert session.main(["set-type", pid, "3", "--goal", "reklam/satış"]) == 0
    p = store.load(pid)
    assert p["videoType"]["type"] == 3 and p["videoType"]["approaches"] == ["M01"]
    assert any("storyboard A" in x for x in session._type_hints(p))
    rep = session.type_checks(pid, p, {})
    assert not rep["problems"] and any("ardıcıllığı qorunub" in c for c in rep["checks"])

    q = session.node_tl("addGraphic", session.node_tl("migrate", p), {"type": "offer", "text": "Təlim", "price": "350 AZN",
                                                                       "heading": "2 ay", "start": 0.5, "dur": 2, "origin": "plan"})
    rep = session.type_checks(pid, q, {})
    assert [x["what"] for x in rep["problems"]] == ["növ qaydası: qrafikada danışıqda olmayan rəqəm(lər): 350 — uydurma olmamalıdır"]

    assert session.main(["edit", pid, "--order", "2,1"]) == 0 and session.main(["apply", pid]) == 0
    rep = session.type_checks(pid, store.load(pid), {})
    assert any("ardıcıllığı dəyişib" in x["what"] for x in rep["problems"]), "reklamda hook əvvələ çəkilmir"

    prof = tmp_path / "x.json"
    prof.write_text(json.dumps({"name": "Sınaq", "history": []}), encoding="utf-8")
    monkeypatch.setattr(session, "profile_path", lambda name: prof)
    p = store.load(pid)
    p["brand"] = {"name": "Sınaq"}
    store.save(pid, p, p["revision"])
    _draft_and_analysis(pid)
    plan = tmp_path / "A.json"
    plan.write_text(json.dumps({"title": "Təmiz + vurğu", "approach": "M04 + punch-in", "look": None}), encoding="utf-8")
    assert session.main(["choose", pid, str(plan)]) == 0
    h = json.loads(prof.read_text(encoding="utf-8"))["history"][-1]
    assert h["type"] == 3 and h["approach"] == "M04" and h["variant"] == "Təmiz + vurğu" and h["engine"] == "montaj"
    assert store.load(pid)["videoType"]["approaches"] == ["M04"]

    src = tmp_path / "sinxron.mp4"
    capsys.readouterr()
    assert session.main(["new", "--title", "Dərs 1", "--file", str(src), "--type", "15"]) == 0
    out = capsys.readouterr().out
    pid2 = out.split("layihə: ")[1].split()[0]
    p2 = store.load(pid2)
    assert p2["aspect"] == "16:9" and p2["width"] > p2["height"] and p2["videoType"]["type"] == 15
    assert session.main(["types", "99"]) == 2


def test_event_montage_beats(tmp_path, monkeypatch):
    """M09: musiqi vuruşları (±10 ms), zəif kadr (bulanıq) seçilmir, kəsimlər vuruşa düşür, görüntünün öz səsi söndürülür."""
    import subprocess

    import numpy as np

    from montaj import event

    sr = 22050
    y = np.random.default_rng(1).standard_normal(sr * 20) * 0.01 + 0.15 * np.sin(2 * np.pi * 220 * np.arange(sr * 20) / sr)
    true = np.arange(0.25, 20, 0.5)
    for k, t in enumerate(true):
        i, n = int(t * sr), int(0.06 * sr)
        y[i:i + n] += (0.9 if k % 4 == 0 else 0.5) * np.sin(2 * np.pi * (110 if k % 2 == 0 else 880) * np.arange(n) / sr) * np.exp(-np.arange(n) / (0.015 * sr))
    mus = tmp_path / "musiqi.wav"  # yalnız test üçün sintez ritm
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-", str(mus)],
                   input=y.astype(np.float32).tobytes(), check=True)
    bt = event.beats(mus)
    assert abs(bt["tempo"] - 120) < 1.5
    assert all(min(abs(true - b)) < 0.02 for b in bt["beats"]), "vuruş zərbə ilə eyni anda (±20 ms, 30 fps-də kadrdan az)"

    pid = _fixture(tmp_path, monkeypatch)
    from montaj import server, session, store

    srcs = {"a_zal": "testsrc2", "b_sehne": "smptebars", "c_bulaniq": "testsrc2", "d_final": "testsrc"}
    for name, lav in srcs.items():
        f = tmp_path / f"{name}.mp4"
        vf = ["-vf", "boxblur=12:2"] if "bulaniq" in name else []
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"{lav}=s=640x360:r=25:d=6", "-f", "lavfi", "-i", "sine=f=300:d=6",
                        *vf, "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(f)], check=True)
        tmp = store.originals_dir(pid) / f".{name}.part"
        tmp.write_bytes(f.read_bytes())
        server._register(pid, tmp, f.name)
    p = store.load(pid)
    p["media"] = [m for m in p["media"] if m["name"] != "sinxron.mp4"]  # yalnız tədbir kadrları
    p["clips"] = []
    store.save(pid, p, p["revision"])
    session._save_draft(pid, {"generator": "rules", "subtitles": False, "candidates": {}, "cards": [], "frames": {}, "options": {}})
    assert session.main(["set-type", pid, "5"]) == 0
    assert session.main(["event-scan", pid, "--no-faces"]) == 0
    shots = json.loads((tmp_path / "out" / pid / "shots.json").read_text())
    blur = {s["media"] for s in shots if "bulanıq" in s["weak"]}
    assert len(blur) == 1
    assert session.main(["event-plan", pid, "--music", str(mus), "--target", "8", "--variants", "A"]) == 0
    plan = json.loads((tmp_path / "out" / pid / "event_A.json").read_text())
    cards = plan["storyboard"]["cards"]
    assert cards[0]["role"] == "açılış" and cards[-1]["role"] == "final" and not any(c["mediaId"] in blur for c in cards)
    assert session.main(["choose", pid, str(tmp_path / "out" / pid / "event_A.json")]) == 0
    q = store.load(pid)
    assert all(c["volume"] == 0 for c in q["clips"] if c["track"] == "a1"), "görüntünün öz səsi söndürülür"
    m1 = next(c for c in q["clips"] if c["track"] == "m1")
    assert abs(m1["srcIn"] - plan["music"]["from"]) < 0.01
    assert session.main(["render", pid]) == 0
    mp4 = sorted((tmp_path / "out" / pid).glob(f"{pid}_r*.mp4"))[-1]
    W, H = q["width"], q["height"]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-vf", "scale=64:112", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 112, 64).astype(float)
    fps = float(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", str(mp4)],
                               capture_output=True, text=True).stdout.strip().split("/")[0])
    cuts = [(i + 1) / fps for i in np.where(np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2)) > 25)[0]]
    beats_out = np.array(plan["music"]["from"] and [b - plan["music"]["from"] for b in bt["beats"]])
    assert len(cuts) == len(cards) - 1 and W and H
    assert all(min(abs(beats_out - c)) < 1.5 / fps for c in cuts), f"kəsimlər vuruşda: {cuts}"


def test_qa_fast_questions(tmp_path, monkeypatch):
    """M10: sual/cavab cütləri (sual işarəsi, sual sözü, ədat), ölü pauza çıxır, reaksiya qalır, B-də sual səsi yoxdur,
    sual yazısı danışıqdan; kadrarxası səs (ağız tərpənmir) sual tərəfinə düşür."""
    import numpy as np

    from montaj import qa

    assert qa.is_question("Ən sevdiyin yemək nədir") and qa.is_question("Sən heç Bakıya gəlmisənmi") and not qa.is_question("Plov.")
    assert not qa.is_question("Onun kimi") and not qa.is_question("Bu elmi") and qa.is_question("Hazırsan mı")

    def W(txt, t0, step=0.35):
        return [{"w": w, "s": round(t0 + i * step, 2), "e": round(t0 + i * step + 0.3, 2)} for i, w in enumerate(txt.split())]
    words = W("Ən sevdiyin yemək nədir?", 0.5) + W("Plov.", 2.6) + W("Çünki çox dadlıdır.", 4.6) + \
        W("Səhər nə vaxt durursan?", 6.4) + W("Heç vaxt.", 8.6) + W("Zarafat edirəm.", 9.6)
    rms = np.full(1200, 0.002)
    for w in words:
        rms[int(w["s"] * 100):int(w["e"] * 100)] = 0.1
    rms[300:440] = 0.08  # "Plov."-dan sonra gülüş (sözsüz səs)
    ss = __import__("montaj.quality", fromlist=["x"]).sentences(words, gap=0.5)
    assert qa.classify(ss) == ["q", "a", "a", "q", "a", "a"]
    assert qa.classify(ss, [3.0, 3.0, 3.0, 3.0, 0.2, 3.0]) == ["q", "a", "a", "q", "q", "a"], "ağız tərpənmir → kadrarxası"
    react = qa.reactions(words, rms)
    assert any(a <= 3.1 and b >= 4.4 for a, b in react)
    r = qa.plans(words, "m1", rms)
    assert r["pairs"] == 2
    A, B, C = (r["plans"][k] for k in "ABC")
    durA = sum(c["srcOut"] - c["srcIn"] for c in A["storyboard"]["cards"])
    durB = sum(c["srcOut"] - c["srcIn"] for c in B["storyboard"]["cards"])
    assert durB < durA, "B-də sual səsi çıxır"
    assert not any(c["srcIn"] < 2.0 for c in B["storyboard"]["cards"]), "B birinci sualın səsini saxlamır"
    assert any(c["srcIn"] <= 3.1 and c["srcOut"] >= 4.5 for c in A["storyboard"]["cards"]), "gülüş pauzası saxlanılır"
    assert [g["text"] for g in A["graphics"]] == ["Ən sevdiyin yemək nədir?", "Səhər nə vaxt durursan?"]
    assert A["zooms"] and A["sfx"] and not C["graphics"] and C["approach"] == "M01"

    pid = _fixture(tmp_path, monkeypatch)
    from montaj import analysis, session, store

    mid = _draft_and_analysis(pid)
    f = analysis.analysis_path(store.project_dir(pid), mid)
    f.write_text(json.dumps({"mediaId": mid, "words": words, "model": "test"}), encoding="utf-8")
    assert session.main(["qa-plan", pid, "--no-faces"]) == 0
    plan = tmp_path / "out" / pid / "qa_A.json"
    assert session.main(["choose", pid, str(plan)]) == 0
    q = store.load(pid)
    assert len([c for c in q["clips"] if c["track"] == "t1" and c.get("origin") == "plan"]) == 2
    assert session.main(["render", pid]) == 0


def test_duo_switch_split(tmp_path, monkeypatch):
    """Növ 11: növbələr (qısa növbə birləşir, uzun cümlə bölünür), kəsim boşluqda; bölünmüş ekran — yuxarı yarı soldakı,
    aşağı yarı sağdakı pəncərədən; kadrda iki nəfər yoxdursa aydın xəta."""
    import subprocess

    import numpy as np

    from montaj import duo, render

    def W(txt, t0):
        return [{"w": w, "s": round(t0 + i * 0.4, 2), "e": round(t0 + i * 0.4 + 0.3, 2)} for i, w in enumerate(txt.split())]
    words = W("bir iki üç dörd beş altı yeddi səkkiz", 0.0) + W("doqquz on", 3.5)
    ss = [{"s": words[0]["s"], "e": words[7]["e"], "words": words[:8], "text": ""},
          {"s": words[8]["s"], "e": words[9]["e"], "words": words[8:], "text": ""}]
    ch = duo.chunks(words, ss, 2.0)
    assert len(ch) == 3 and all(c["e"] - c["s"] <= 2.0 for c in ch)
    rs = duo.runs([{"s": 0, "e": 3}, {"s": 3.2, "e": 3.8}, {"s": 4, "e": 7}, {"s": 7.2, "e": 10}], [0, 1, 0, 1])
    assert [r["speaker"] for r in rs] == [0, 1] and rs[0]["e"] == 7, "qısa növbə (0.6 s) birləşir"
    assert duo.cut_points(rs) == [7.1]
    spec = duo.split_spec([{"cx": 0.7, "cy": 0.4, "w": 0.1}, {"cx": 0.3, "cy": 0.4, "w": 0.1}], 1920, 1080, 1080, 1920)
    assert spec["top"]["x"] < 0.3 < spec["bottom"]["x"], "yuxarıda soldakı şəxs"
    assert abs(spec["top"]["w"] * 1920 / (spec["top"]["h"] * 1080) - 1080 / 960) < 0.01

    src = tmp_path / "sol_sag.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=red:s=320x360", "-f", "lavfi", "-i", "color=blue:s=320x360",
                    "-filter_complex", "[0][1]hstack", "-frames:v", "1", str(src)], check=True)
    sp = {"top": {"x": 0.0, "y": 0.0, "w": 0.4, "h": 0.8}, "bottom": {"x": 0.6, "y": 0.0, "w": 0.4, "h": 0.8}}
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-filter_complex", f"[0:v]{render.split_graph(sp, 180, 320, 't')}",
                          "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(320, 180, 3).astype(int)
    assert fr[60, 90, 0] > 200 and fr[60, 90, 2] < 60, "yuxarı yarı — sol (qırmızı)"
    assert fr[260, 90, 2] > 200 and fr[260, 90, 0] < 60, "aşağı yarı — sağ (göy)"
    assert fr[160, 90].min() > 180, "ortada ayırıcı xətt"

    pid = _fixture(tmp_path, monkeypatch)
    from montaj import session

    assert session.main(["duo", pid, "--mode", "split"]) == 2, "üzsüz kadrda aydın xəta"


def test_virtual_multicam(tmp_path, monkeypatch, capsys):
    """Virtual multikamera: keyfiyyət ehtiyatına görə plan ölçüləri, cümlə sərhədində kəsim, eyni ölçü ardıcıl deyil,
    vurğuda yaxın plan; 1x ehtiyatda dürüst xəbərdarlıq; yavaş yaxınlaşma (push) render olunur."""
    from montaj import multicam, render

    assert list(multicam.tiers(2.0)) == ["wide", "medium", "close"] and multicam.tiers(2.0)["close"] == 2.0
    assert multicam.tiers(1.0) == {"wide": 1.0, "close": 1.12}
    assert multicam.tiers(0.56) == {"wide": 1.0}, "16:9 → 9:16 (artıq böyüdülür): yaxınlaşma yoxdur"
    sents = [{"s": i * 3.0, "e": i * 3.0 + 2.5, "text": t} for i, t in enumerate(
        ["Salam.", "Bu gün danışacağıq.", "Ən vacib qayda budur!", "Sonra davam edək.", "Və bitirək.", "Sağ olun.", "Görüşənədək."])]
    segs = multicam.segments(sents, 21.0, 5.0)
    assert segs[0]["a"] == 0 and segs[-1]["b"] == 21.0 and all(x["b"] == y["a"] for x, y in zip(segs, segs[1:]))
    names = multicam.assign(segs, multicam.tiers(2.0))
    assert names[0] == "wide" and all(x != y for x, y in zip(names, names[1:]))
    assert names[[i for i, g in enumerate(segs) if g["emph"]][0]] == "close"
    chain = render.video_chain({"srcIn": 0, "srcOut": 4, "frame": {"mode": "auto", "s": 0.5, "baseW": 1, "baseH": 1, "push": 1.08,
                                "keys": [{"t": 0, "cx": 0.5, "cy": 0.5}]}}, {"width": 1920, "height": 1080}, 540, 960, "30", False, 120)
    assert "eval=frame" in chain and "crop=960:540" in chain

    pid = _fixture(tmp_path, monkeypatch)
    from montaj import session, store

    _draft_and_analysis(pid)
    capsys.readouterr()
    assert session.main(["multicam", pid]) == 0
    out = capsys.readouterr().out
    assert "XƏBƏRDARLIQ" in out and "4K" in out, "1x ehtiyatda dürüst xəbərdarlıq"
    q, rep = session._apply_multicam(pid, session.node_tl("migrate", store.load(pid)), {"min_len": 2.0})  # qısa sınaq videosu
    vs = session.node_tl("videoClips", q)
    ss = [round(c["frame"]["s"], 3) for c in vs]
    pl = [n for _, _, n in rep["plans"]]
    assert len(pl) >= 2 and len(set(ss)) == 2 and all(x != y for x, y in zip(pl, pl[1:])), (pl, ss)
    assert abs(min(ss) - 1 / 1.123) < 0.01, "yaxın plan 1.12x (1x ehtiyat)"
    c = vs[0]
    c["frame"]["push"] = 1.06
    store.save(pid, q, q["revision"])
    assert session.main(["render", pid]) == 0


def test_background_replace(tmp_path, monkeypatch, capsys):
    """Arxa fon: seçimlərin yoxlanması, qradiyent, masa zolağı, birləşdirmə; tam emal — kadr sayı orijinalla eyni,
    insansız kadrda nəticə fon rəngidir; layihədə törəmə video, render onu götürür, --off geri qaytarır; önizləmə şəkli."""
    import subprocess

    import numpy as np

    from montaj import background

    with pytest.raises(ValueError):
        background.normalize({"mode": "color"})
    with pytest.raises(ValueError):
        background.normalize({"mode": "sky"})
    g = background._gradient({"color": "#FF0000", "color2": "#0000FF"}, 4, 10)
    assert g[0, 0, 0] == 255 and g[-1, 0, 2] == 255
    k = background.keep_mask(100, 10, 0.8)
    assert k[50, 0, 0] == 0 and k[99, 0, 0] == 1
    out = background.composite(np.full((2, 2, 3), 200, np.uint8), np.array([[[1.0], [0.0]], [[0.5], [0.0]]], np.float32),
                               np.zeros((2, 2, 3), np.float32), None)
    assert out[0, 0, 0] == 200 and out[0, 1, 0] == 0 and 99 <= out[1, 0, 0] <= 101
    try:
        background.model_path("fast")
    except Exception:  # noqa: BLE001
        pytest.skip("seqmentasiya modeli endirilmədi (şəbəkə)")

    pid = _fixture(tmp_path, monkeypatch)
    from montaj import session, store

    capsys.readouterr()
    assert session.main(["bg", pid, "--preview", "--spec", '{"mode":"blur","model":"fast"}',
                         "--spec", '{"mode":"color","color":"#10A040","model":"fast"}']) == 0
    assert (tmp_path / "out" / pid / "arxafon.jpg").stat().st_size > 5000
    assert store.load(pid).get("background") in (None, {}), "önizləmə layihəni dəyişmir"
    assert session.main(["bg", pid, "--mode", "color", "--color", "#10A040", "--fast"]) == 0
    q = store.load(pid)
    mid = q["media"][0]["id"]
    der = store.project_dir(pid) / q["background"][mid]["file"]
    cnt = lambda f: int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                                        "stream=nb_read_frames", "-of", "csv=p=0", str(f)], capture_output=True, text=True).stdout.strip())
    src = store.project_dir(pid) / q["media"][0]["file"]
    assert abs(cnt(der) - cnt(src)) <= 1, "kadr sayı orijinalla eyni (vaxt sürüşmür)"
    assert session.main(["render", pid]) == 0
    mp4 = sorted((tmp_path / "out" / pid).glob(f"{pid}_r*.mp4"))[-1]
    W, H = q["width"], q["height"]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "1.0", "-i", str(mp4), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    px = np.frombuffer(raw, np.uint8).reshape(H, W, 3)[H // 3, W // 2].astype(int)
    assert abs(px[0] - 0x10) < 40 and abs(px[1] - 0xA0) < 40 and abs(px[2] - 0x40) < 40, f"insansız kadr — fon rəngi: {px}"
    assert session.main(["bg", pid, "--off"]) == 0 and not store.load(pid)["background"]
