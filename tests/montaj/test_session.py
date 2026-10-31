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
