"""Adaptive Crystal Clear Natural Look: qərar məntiqi (sintetik ölçülər, ffmpeg/video tələb etmir) + sintetik klipdə yoxlama."""
import numpy as np

from montaj import crystal


def _m(**kw):
    base = {"mean_luma": 118.0, "sharp": 6.58, "noise": 0.628, "chroma_noise": 0.53, "sat": 0.107, "clip_hi": 0.0, "skin_luma": 105.0,
            "skin_frac": 0.15, "cast_rg": 1.0, "cast_bg": 0.98, "probe": {"hdr": False}}
    base.update(kw)
    return base


def test_reference_scene_gives_v3():
    d = crystal.decide(_m())
    P = d["params"]
    assert abs(P["sharpen"] - 0.14) < 0.01 and abs(P["micro"] - 0.09) < 0.01 and abs(P["lift"] - 1.0) < 0.05
    assert abs(P["vibrance"] - 0.012) < 1e-6 and abs(P["chroma_denoise"] - 1.6) < 0.1


def test_good_parameters_untouched():
    d = crystal.decide(_m(sharp=12.0, noise=0.2, chroma_noise=0.05, mean_luma=140, sat=0.45, skin_luma=140))
    assert d["mode"] == "asis" and all(v == 0 for v in d["params"].values())


def test_dark_soft_noisy_gets_more_but_capped():
    P = crystal.decide(_m(mean_luma=70, sharp=4.0, noise=3.0, skin_luma=60))["params"]
    assert 0 < P["lift"] <= 1.6 and P["sharpen"] <= 0.14 * 1.6 + 1e-9 and P["luma_denoise"] <= 1.2 and P["chroma_denoise"] <= 4.0


def test_no_extra_light_when_highlights_clipped():
    assert crystal.decide(_m(clip_hi=5.0))["params"]["lift"] == 0


def test_hdr_skipped_and_wb_never_auto_changed():
    assert crystal.decide(_m(probe={"hdr": True}))["mode"] == "skip"
    d = crystal.decide(_m(cast_bg=0.85))
    assert any("ağ balansı" in n for n in d["notes"]) and "temperature" not in crystal.chain(d["params"])


def test_chain_has_no_forbidden_filters():
    c = crystal.chain(crystal.V3_PARAMS)
    for bad in ("colortemperature", "selectivecolor", "eq=", "colorbalance", "hue="):
        assert bad not in c
    assert crystal.chain({k: 0.0 for k in crystal.V3_PARAMS}) == "null"


def test_check_flags_shift_and_sharpening():
    b = {"mean_luma": 100, "skin_rg": 1.4, "cast_bg": 1.0, "sat": 0.2, "clip_hi": 0, "sharp": 6, "noise": 0.6}
    assert crystal.check(b, dict(b)) == []
    assert "lift" in crystal.check(b, {**b, "mean_luma": 110})
    assert "sharpen" in crystal.check(b, {**b, "sharp": 9})
    assert "vibrance" in crystal.check(b, {**b, "skin_rg": 1.5})


def test_measure_and_apply_on_synthetic_frame():
    rng = np.random.default_rng(1)
    f = np.clip(rng.normal(120, 6, (320, 180, 3)) + np.array([8, 0, -6]), 0, 255).astype(np.uint8)
    m = crystal.measure(f)
    assert 100 < m["mean_luma"] < 140 and m["noise"] > 0
    g = crystal._apply(f, crystal.V3_PARAMS)
    assert g.shape == f.shape and abs(crystal.measure(g, like=f)["mean_luma"] - m["mean_luma"]) < 4
