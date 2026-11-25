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
        assert all(g["type"] in {"title", "list", "emphasis", "type", "block", "note", "bars", "veil", "frame", "slate", "gcard", "gbanner", "gcaps", "pblur", "viewfinder"} for g in p["graphics"])
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
    # hər cüt dəst (classic daxil) ən azı 4 oxda fərqlənməlidir — "rəngdən başqa hər şey" (hook oxu build()-dən gəlir)
    built = {k: kits.build(k, {**CONTENT, "brand_name": "Sura Malik"}) for k in kits.KITS}
    for a, b in itertools.combinations(kits.KITS, 2):
        d = difference.check({"A": built[a], "B": built[b]})
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
    for n, k in enumerate(("editorial", "frame", "intertitle", "colorblock", "handnote", "kinetic", "milkglass", "notification", "glasscaps", "pblur")):
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
        if name.startswith("intertitle") and "slate" in json.dumps(info) or (name.startswith("intertitle") and info["w"] >= W - 4 and info["h"] >= H - 4):
            assert info["w"] >= W - 4 and info["h"] >= H - 4, "intertitle kartı tam kadrdır"
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
    assert {"colorblock", "kinetic", "handnote", "intertitle"} <= set(g["rejected"]), "istifadəçi bu dəstləri bəyənməyib (2026-11-25)"
    assert "editorial" in g["liked"]
    sug = memory.suggest({}, 3)
    assert not {"colorblock", "kinetic", "handnote", "intertitle"} & set(sug) and sug[0] == "editorial"
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
    assert {"Lora", "Work Sans"} <= {f["family"] for f in faces}
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
    assert "frame" not in memory.blocked({})


def test_editorial_scales_long_hook_instead_of_overflowing():
    long = {"hook": {"text": "Hər səhvə cəza düzgündürmü?", "start": 0.1, "dur": 3}}
    big = {"hook": {"text": "CƏZA?", "start": 0.1, "dur": 3}}
    s_long = [g for g in kits.build("editorial", long)["graphics"] if g["type"] == "type"][0]["size"]
    s_big = [g for g in kits.build("editorial", big)["graphics"] if g["type"] == "type"][0]["size"]
    assert s_long < s_big


def test_intertitle_kit_full_frame_cards_only_at_idea_boundaries():
    b = kits.build("intertitle", CONTENT, {"primary": "#C9577D", "primaryDeep": "#9E3D5E", "accentSoft": "#F2E4D6"})
    slates = [g for g in b["graphics"] if g["type"] == "slate"]
    assert len(slates) == 2 and all(g["bleed"] and g["dur"] >= 2.0 for g in slates), "kart ≥2 s və tam kadr (bleed)"
    assert not b["zooms"], "ekspert görünmədiyi kartda zoom yoxdur"
    assert slates[0]["items"] and slates[1]["big"] and slates[1]["bg"] == "#F2E4D6"
    # hook-da ekspert görünür (kart yox): yuxarıda mərkəzləşmiş yazı
    assert any(g["type"] == "type" and g["align"] == "center" for g in b["graphics"])
    for other in ("editorial", "frame", "classic"):
        d = difference.check({"A": b, "B": kits.build(other, CONTENT)})
        assert d["ok"] and d["pairs"][0]["diff"] >= 4, other


def test_viewfinder_hook_only_touches_top_corners_never_the_face(tmp_path):
    """Kamera vizörü (REC + taymkod): yalnız yuxarı küncləri tutur; mərkəzə/üzə toxunmur; REC yanıb-sönür, taymkod sayır."""
    if not (shutil.which("ffmpeg") and shutil.which("node")):
        pytest.skip("node yoxdur")
    import numpy as np
    from PIL import Image

    from montaj import graphics as G

    c = {**CONTENT, "hook": {**CONTENT["hook"], "viewfinder": True}}
    b = kits.build("frame", c)
    vf = [g for g in b["graphics"] if g["type"] == "viewfinder"]
    assert len(vf) == 1 and vf[0]["bleed"] and b["axes"]["hook"] == "viewfinder"
    clip = dict(vf[0], id="vf", srcIn=0, srcOut=float(vf[0]["dur"]))
    pts = G.state_points(clip)
    assert pts[:3] == [0.0, 0.5, 1.0] and pts[-1] < clip["srcOut"]
    W, H = 360, 640
    rast = G.rasterize([("vf0", clip, 0.1), ("vf1", clip, 0.6), ("vf2", clip, 3.2)], W, H, {}, tmp_path)
    boxes = []
    for n in ("vf0", "vf1", "vf2"):
        a = np.asarray(Image.open(rast[n]["file"]).convert("RGBA"))[..., 3]
        ys, xs = np.where(a > 12)
        assert len(ys), n
        boxes.append((xs.min() / a.shape[1], ys.min() / a.shape[0], xs.max() / a.shape[1], ys.max() / a.shape[0]))
        assert ys.max() / a.shape[0] < 0.14, f"{n}: yalnız yuxarı zolaq (üz/mərkəz toxunulmaz)"
        mid = a[:, int(a.shape[1] * 0.3): int(a.shape[1] * 0.7)]
        assert not (mid > 12).any(), f"{n}: orta hissə boşdur (üz üçün)"
    assert Image.open(rast["vf0"]["file"]).tobytes() != Image.open(rast["vf1"]["file"]).tobytes(), "REC yanıb-sönür"
    assert Image.open(rast["vf0"]["file"]).tobytes() != Image.open(rast["vf2"]["file"]).tobytes(), "taymkod sayır"


@needs_node
def test_glass_backdrop_blurs_only_inside_mask(tmp_path):
    """Şüşə zənciri: maskanın içində kadr bulanıqlaşır (detal azalır), kənarda dəyişmir; yalnız [a,b] müddətində."""
    import numpy as np
    from PIL import Image, ImageDraw

    from montaj import graphics as G

    W, H = 270, 480
    src = tmp_path / "src.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"nullsrc=s={W}x{H}:r=30:d=2,geq=lum='random(1)*255':cb=128:cr=128", "-pix_fmt", "yuv420p", "-crf", "10", str(src)], check=True)
    elem = {"w": 160, "h": 90}
    mimg = Image.new("RGBA", (160, 90), (0, 0, 0, 0))
    ImageDraw.Draw(mimg).rounded_rectangle((8, 8, 151, 81), radius=20, fill=(255, 255, 255, 255))
    mfile = tmp_path / "mask_el.png"
    mimg.save(mfile)
    c = {"id": "g1", "type": "gcard", "x": 0.5, "y": 0.3, "anim": {"in": "none", "out": "none"}}
    g = G.glass_prepare(c, elem, {"file": str(mfile)}, W, H, tmp_path, "t")
    chain = G.glass_chain(c, 0, 1, 0.5, 1.5, g, "30", 1, "base", "vout")
    out = tmp_path / "o.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-loop", "1", "-framerate", "30", "-t", "2", "-i", g["mask"], "-filter_complex",
                    f"[0:v]null[base];{chain}", "-map", "[vout]", "-t", "2", "-pix_fmt", "yuv420p", str(out)], check=True)

    def frame(path, t):
        f = tmp_path / f"{path.stem}_{t}.png"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", str(path), "-frames:v", "1", str(f)], check=True)
        return np.asarray(Image.open(f).convert("L")).astype(float)
    inner = (slice(int(H * 0.3) - 20, int(H * 0.3) + 20), slice(W // 2 - 50, W // 2 + 50))
    a_in, o_in = frame(src, 1.0)[inner], frame(out, 1.0)[inner]
    assert o_in.std() < 0.4 * a_in.std(), f"mask içində bulanıqlaşmalıdır ({o_in.std():.1f} vs {a_in.std():.1f})"
    assert frame(out, 1.0)[:60].std() > 0.8 * frame(src, 1.0)[:60].std(), "mask kənarında kadr bulanıqlaşmır"
    assert frame(out, 0.2)[inner].std() > 0.8 * frame(src, 0.2)[inner].std(), "[a,b] müddətindən kənarda effekt yoxdur"


@needs_node
def test_glass_kit_elements_rasterize_with_matching_masks(tmp_path):
    from PIL import Image

    from montaj import graphics as G

    W, H = 360, 640
    theme = {"primary": "#C9577D", "primaryDeep": "#9E3D5E"}
    clips = [{"id": "c", "type": "gcard", "icon": "drop", "text": "Hər səhvə cəza\ndüzgündürmü?", "y": 0.17},
             {"id": "n", "type": "gbanner", "title": "Sura Malik", "time": "indi", "text": "Bir fikir", "y": 0.12},
             {"id": "p", "type": "gcaps", "items": [{"text": "Televizor", "at": 0}, {"text": "Oyuncaq", "at": 0.5}], "y": 0.15},
             {"id": "b", "type": "pblur", "h": 0.4, "bleed": True, "y": 0.2}]
    items = []
    for c in clips:
        c = dict(c, srcIn=0, srcOut=2.0)
        items += [(f"{c['id']}", c, 1.0), (f"{c['id']}__m", {**c, "_mask": True}, 1.0)]
    rast = G.rasterize(items, W, H, theme, tmp_path)
    for c in clips:
        e, m = rast[c["id"]], rast[c["id"] + "__m"]
        assert (e["w"], e["h"]) == (m["w"], m["h"]), f"{c['id']}: maska və element eyni ölçüdə olmalıdır"
        mk = Image.open(m["file"]).convert("RGBA").getchannel("A")
        assert mk.getbbox() is not None and max(mk.getdata()) >= 250, f"{c['id']}: maska siluet verir"
        el = Image.open(e["file"]).convert("RGBA")
        assert el.getchannel("A").getbbox() is not None


def test_viewfinder_is_available_in_every_kit_when_requested():
    c = {**CONTENT, "hook": {**CONTENT["hook"], "viewfinder": True}, "brand_name": "Sura Malik"}
    for k in kits.KITS:
        b = kits.build(k, c)
        vf = [g for g in b["graphics"] if g["type"] == "viewfinder"]
        assert len(vf) == 1 and vf[0]["bleed"] and b["axes"]["hook"] == "viewfinder", k
        assert b["graphics"][-1]["type"] == "viewfinder", f"{k}: REC/taymkod hər şeyin üstündə"
        assert vf[0]["corners"] == (k != "frame"), "çərçivəsi olmayan dəstdə künc nişanları vizörün özündədir"
    assert not [g for g in kits.build("milkglass", CONTENT)["graphics"] if g["type"] == "viewfinder"], "xahiş olmadan vizör yoxdur"


def test_glass_kits_use_profile_name_and_do_not_invent_text():
    b = kits.build("notification", {**CONTENT, "brand_name": "Sura Malik"})
    ban = [g for g in b["graphics"] if g["type"] == "gbanner"]
    assert ban and all(g["title"] == "Sura Malik" and g["time"] == "indi" for g in ban)
    blob = json.dumps(ban, ensure_ascii=False).lower()
    assert "televizor" in blob and "psixoloji" in blob
    assert {"milkglass", "notification", "glasscaps", "pblur"} <= set(memory.global_decisions()["liked"])


def test_client_kit_preferences_restrict_suggestions_and_drive_glass_style():
    import json as _j
    from pathlib import Path

    prof = _j.loads((Path(__file__).resolve().parents[2] / "templates" / "expert-reels" / "experts" / "xeyyam-huseynov.json").read_text(encoding="utf-8"))
    pref = prof["kit_preferences"]
    assert pref["only"] and set(pref["preferred"]) == {"milkglass", "glasscaps", "pblur", "notification"}
    sug = memory.suggest(prof, 5)
    assert set(sug) <= set(pref["preferred"]) and len(sug) == 4, "Xəyyam üçün yalnız seçdiyi dəstlər (eskiz 1 və 4)"
    gl = memory.glass_defaults(prof)
    assert gl["tint"] == "#0F3B2E" and gl["ink"] == "#FFFFFF" and gl["accent"] == "#6CC57E" and gl["icon"] == "book"
    assert len(prof["cautions"]) == 1 and "laym" in prof["cautions"][0].lower(), "köhnə qaydalar silinib; yalnız 11-04 rəng qərarı"
    b = kits.build("milkglass", {**CONTENT, "glass": gl}, {"primaryDeep": "#0F3B2E"})
    g0 = [g for g in b["graphics"] if g["type"] == "gcard"][0]
    assert g0["tint"] == "#0F3B2E" and g0["ink"] == "#FFFFFF" and g0["icon"] == "book" and g0["ta"] == 0.6
    n = kits.build("notification", {**CONTENT, "glass": gl, "brand_name": "Xəyyam Həsənov"})
    assert all(g["icon"] == "book" and g["title"] == "Xəyyam Həsənov" for g in n["graphics"] if g["type"] == "gbanner")
    # 4 seçilmiş dəst bir-birindən fərqli variantlar verir
    built = {k: kits.build(k, {**CONTENT, "glass": gl, "brand_name": "Xəyyam Həsənov"}) for k in sug}
    assert difference.check(built)["ok"]
