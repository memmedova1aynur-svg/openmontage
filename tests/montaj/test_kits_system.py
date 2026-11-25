"""Üslub dəstləri, fərq yoxlayıcısı, təkrar əleyhinə yaddaş, bəzək rejimi və referans öyrənməsi."""

from __future__ import annotations

import itertools
import json
import shutil
import subprocess

import pytest

from montaj import difference, kits, memory, refstyle

CONTENT = {"hook": {"text": "Hər səhvə cəza düzgündürmü?", "short": "CƏZA?", "kicker": "TƏRBİYƏ", "start": 0.15, "dur": 4.5},
           "list": {"heading": "Nümunələr", "items": ["Televizor", "Həyətə düşmək", "Oyuncaq"], "times": [0.2, 1.0, 2.1], "start": 18.3, "dur": 4.2},
           "emphasis": [{"text": "Hər uşaq fərqlidir", "start": 28.4, "dur": 2.8}],
           "claim": {"text": "psixoloji vəziyyət", "kicker": "ƏSAS FİKİR", "start": 47.5, "dur": 4.0},
           "words": [{"w": "CƏZA", "s": 0.2}, {"w": "düzgündürmü?", "s": 1.5}], "duration": 56.4}
needs_node = pytest.mark.skipif(not (shutil.which("ffmpeg") and shutil.which("node")), reason="ffmpeg/node yoxdur")


def test_every_kit_builds_from_spoken_content_only():
    for k in kits.KITS:
        p = kits.build(k, CONTENT, {"primary": "#F2E4D6", "primaryDeep": "#C9577D"})
        assert p["kit"] == k and p["graphics"] and set(p["axes"]) >= set(difference.AXES)
        blob = json.dumps(p["graphics"], ensure_ascii=False).lower()
        for must in ("televizor", "oyuncaq"):
            assert must in blob, f"{k}: nümunə danışıqdan götürülməlidir"
        assert all(g["type"] in {"title", "list", "emphasis", "type", "block", "note", "bars", "veil", "frame"} for g in p["graphics"])
        assert all(z.get("scale", 1) <= 1.12 for z in p["zooms"]), "zoom hamar və ≤1.12"


def test_different_kits_pass_difference_check_same_kit_fails():
    plans = {n: kits.build(k, CONTENT) for n, k in zip("ABCD", ("editorial", "colorblock", "handnote", "kinetic"))}
    rep = difference.check(plans)
    assert rep["ok"], rep["problems"]
    assert all(p["diff"] >= 4 for p in rep["pairs"])
    same = {"A": kits.build("editorial", CONTENT), "B": kits.build("editorial", CONTENT)}
    assert not difference.check(same)["ok"]
    # köhnə (dəstsiz) plan classic sayılır və yalnız rəng/mətn fərqli plan fərqli sayılmır
    legacy = {"A": {"graphics": [{"type": "title"}], "variation": {"primary": "#111111"}}, "B": {"graphics": [{"type": "title"}], "variation": {"primary": "#999999"}}}
    assert not difference.check(legacy)["ok"]


def test_kit_axes_are_really_different_across_kits():
    # hər cüt dəst (classic daxil) ən azı 4 oxda fərqlənməlidir — "rəngdən başqa hər şey"
    for a, b in itertools.combinations(kits.KITS, 2):
        d = difference.check({"A": {"kit": a, "axes": kits.KITS[a]["axes"]}, "B": {"kit": b, "axes": kits.KITS[b]["axes"]}})
        assert d["pairs"][0]["diff"] >= 4, (a, b, d["pairs"])


def test_memory_blocks_recent_and_rejected_and_suggests_spread(tmp_path, monkeypatch):
    monkeypatch.setattr(memory, "GLOBAL", tmp_path / "yox.json")  # ümumi qərarlar bu testə təsir etməsin
    prof = {"history": [{"kit": "classic"}, {"kit": "editorial"}, {"kit": "handnote"}], "rejected": [{"kit": "kinetic"}]}
    assert memory.recent_kits(prof) == ["editorial", "handnote"]
    bl = memory.blocked(prof)
    assert set(bl) == {"editorial", "handnote", "kinetic"}
    sug = memory.suggest(prof, 3)
    assert not set(sug) & set(bl) and set(sug) == {"classic", "colorblock", "frame"}
    warn = memory.check_plans(prof, {"A": {"kit": "kinetic"}, "B": {"kit": "colorblock"}})
    assert len(warn) == 1 and "rədd" in warn[0]


def test_memory_apply_records_only_confirmed_decisions():
    prof: dict = {}
    memory.apply(prof, {"kit": "editorial", "video": "v1"}, ["kinetic", "kinetic", ""], "2026-11-25")
    assert prof["approved"] == [{"kit": "editorial", "video": "v1", "date": "2026-11-25"}]
    assert [r["kit"] for r in prof["rejected"]] == ["kinetic"], "təkrar yazılmır"


@needs_node
def test_new_graphic_types_rasterize_full_bleed(tmp_path):
    from montaj import graphics as G

    W, H = 360, 640
    theme = {"primary": "#C9577D", "primaryDeep": "#9E3D5E", "accentSoft": "#F2E4D6", "accent": "#C9577D", "text": "#FFFFFF"}
    items = []
    for n, k in enumerate(("editorial", "frame", "colorblock", "handnote", "kinetic")):
        for j, g in enumerate(kits.build(k, CONTENT, theme)["graphics"]):
            c = dict(g, id=f"{k}{j}", srcIn=0, srcOut=float(g["dur"]))
            items.append((f"{k}_{j}", c, min(1.0, float(g["dur"]) - 0.1)))
    rast = G.rasterize(items, W, H, theme, tmp_path)
    assert len(rast) == len(items)
    for name, info in rast.items():
        assert info["w"] > 20 and info["h"] > 10, name
        if name.startswith("colorblock"):
            assert info["w"] >= W - 4, "rəng bloku tam enlidir"
        if name.startswith("kinetic"):
            assert info["h"] >= H - 4, "sinema zolaqları tam kadrdır"
        if name.startswith("frame_0"):
            assert info["w"] >= W - 4 and info["h"] >= H - 4, "çərçivə tam kadrdır"


@needs_node
def test_atelier_renders_deterministic_scene_and_caches(tmp_path):
    from montaj import atelier, media
    from montaj.errors import UserError

    html = tmp_path / "s.html"
    html.write_text("<body style='margin:0'><div id=x style='width:50px;height:50px;background:red;position:absolute'></div>"
                    "<script>window.setTime=t=>{document.getElementById('x').style.left=(t*100)+'px'}</script></body>")
    out = atelier.render(html, 0.5, 160, 90, None, tmp_path / "o")
    assert media.probe(out)["duration"] > 0.4 and media.probe(out)["width"] == 160
    assert atelier.render(html, 0.5, 160, 90, None, tmp_path / "o") == out
    bad = tmp_path / "b.html"
    bad.write_text("<body>setTime yoxdur</body>")
    with pytest.raises(UserError):
        atelier.render(bad, 0.3, 160, 90, None, tmp_path / "o")


@needs_node
def test_reference_learning_extracts_rhythm_not_media(tmp_path, monkeypatch):
    monkeypatch.setattr(refstyle, "DIR", tmp_path / "refs")
    src = tmp_path / "ref.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=red:s=160x288:d=1.5:r=30", "-f", "lavfi", "-i", "color=c=blue:s=160x288:d=0.8:r=30",
                    "-f", "lavfi", "-i", "color=c=green:s=160x288:d=2.5:r=30", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-filter_complex",
                    "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]", "-map", "[v]", "-map", "3:a", "-t", "4.8", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(src)], check=True)
    r = refstyle.analyze(src, "t1", tmp_path / "sheets")
    assert r["rhythm"]["cuts"] == 2 and r["rhythm"]["shots"] == 3 and abs(r["rhythm"]["avg_shot_s"] - 1.6) < 0.1
    saved = json.loads((tmp_path / "refs" / "t1.json").read_text())
    assert "sheet" not in saved and saved["approved_by_user"] is False and "cut_times" in saved
    assert refstyle.approved_targets() == [], "təsdiqsiz fərziyyə qayda deyil"
    with pytest.raises(ValueError):
        refstyle.approve("t1")  # decisions boşdur
    refstyle.decide("t1", {"hook_method": "ilk saniyədə sürətli kəsim"})
    refstyle.approve("t1")
    assert refstyle.approved_targets()[0]["decisions"]["hook_method"].startswith("ilk")
    refstyle.decide("t1", {"typography": "böyük sans"})
    assert refstyle.approved_targets() == [], "dəyişən qərar yenidən təsdiq tələb edir"


def test_global_user_decisions_block_disliked_kits_and_prefer_liked():
    g = memory.global_decisions()
    assert {"colorblock", "kinetic", "handnote"} <= set(g["rejected"]), "istifadəçi bu üç dəsti bəyənməyib (2026-11-25)"
    assert "editorial" in g["liked"]
    sug = memory.suggest({}, 3)
    assert not {"colorblock", "kinetic", "handnote"} & set(sug) and sug[0] == "editorial"
    assert memory.check_plans({}, {"A": {"kit": "kinetic"}}), "variants rədd edilmiş dəsti dayandırır"


def test_text_without_background_gets_soft_veil_not_blob():
    for k in ("editorial", "handnote"):
        gs = kits.build(k, CONTENT)["graphics"]
        texts = [g for g in gs if g["type"] in ("type", "note")]
        assert texts and not any("scrim" in g for g in gs), "ləkə (scrim) yoxdur — istifadəçi bəyənmədi"
        for i, g in enumerate(gs):
            if g["type"] in ("type", "note"):
                v = gs[i - 1]
                assert v["type"] == "veil" and v["bleed"] and v["start"] == g["start"] and v["dur"] == g["dur"], "hər yazının ALTINDA eyni vaxtda veil"
                assert 0.25 <= v["a"] <= 0.5 and v["h"] <= 0.45


def test_serif_font_has_all_azerbaijani_letters():
    from fontTools.ttLib import TTFont

    from montaj import fonts

    faces = fonts.extra_font_faces()
    assert faces and {f["family"] for f in faces} == {"Lora"}
    for f in faces:
        cm = TTFont(f["path"]).getBestCmap()
        assert all(ord(c) in cm for c in "əƏğĞıİöÖüÜşŞçÇ"), f


def test_frame_kit_is_framed_centered_serif_and_differs_from_editorial():
    b = kits.build("frame", CONTENT, {"primary": "#C9577D"})
    assert b["graphics"][0]["type"] == "frame" and b["graphics"][0]["bleed"] and b["graphics"][0]["dur"] == CONTENT["duration"]
    texts = [g for g in b["graphics"] if g["type"] == "type"]
    assert texts and all(g["align"] == "center" and g["font"] == "serif" for g in texts)
    assert any(g.get("inline") and g.get("italic") for g in texts), "nümunələr bir sətirdə, nöqtə ilə, kursivlə"
    assert all(g["type"] != "veil" or g["a"] <= 0.45 for g in b["graphics"])
    d = difference.check({"A": kits.build("editorial", CONTENT), "B": b})
    assert d["ok"] and d["pairs"][0]["diff"] >= 4
    assert "frame" in memory.global_decisions()["liked"], "istifadəçi seçdi (2026-11-25)"
    assert memory.suggest({}, 3)[:2] == ["editorial", "frame"] or "frame" in memory.suggest({}, 3)


def test_editorial_scales_long_hook_instead_of_overflowing():
    long = {"hook": {"text": "Hər səhvə cəza düzgündürmü?", "start": 0.1, "dur": 3}}
    big = {"hook": {"text": "CƏZA?", "start": 0.1, "dur": 3}}
    s_long = [g for g in kits.build("editorial", long)["graphics"] if g["type"] == "type"][0]["size"]
    s_big = [g for g in kits.build("editorial", big)["graphics"] if g["type"] == "type"][0]["size"]
    assert s_long < s_big
