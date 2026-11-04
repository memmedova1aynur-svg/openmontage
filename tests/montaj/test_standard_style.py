"""Standart üslub əlavələri: sarı işıq düzəlişi (look N), danışıq aydınlığı, pauza aşkarı,
kadr şəbəkəsinə uyğunlaşma, sərt kəsimin yumşaldılması, B-roll zamanı altyazının qalxması."""
import numpy as np

from montaj import quality, render, session


def test_look_n_warmfix_filter():
    assert "N" in session.LOOKS and "N" in session.LOOK_LABELS
    assert "warmFix" in session.LOOK_KEYS
    f = render.color_filters(session.LOOKS["N"])
    assert any(x.startswith("colorbalance=") for x in f)
    assert not any(x.startswith("colorbalance=") for x in render.color_filters(session.LOOKS["C"]))


def test_voice_polish_chain_is_valid_text():
    assert "highpass" in render.VOICE_POLISH and "acompressor" in render.VOICE_POLISH


def test_silent_pauses_detects_gap():
    n = int(3.0 / quality.HOP)
    rms = 0.1 + 0.02 * np.random.default_rng(0).random(n)  # danışıq (səviyyə bir az dəyişir)
    a, b = int(1.0 / quality.HOP), int(1.8 / quality.HOP)
    rms[a:b] = 0.001  # 0.8 s sükut
    out = session.silent_pauses(rms, -16.0, 0.45)
    assert len(out) == 1
    s0, e0 = out[0]
    assert abs(s0 - 1.0) < 0.1 and abs(e0 - 1.8) < 0.1
    assert session.silent_pauses(rms, -16.0, 1.0) == []


def test_snap_to_frames_only_main_speech():
    q = {"fps": 30, "clips": [
        {"id": "v", "track": "v1", "media": "m1", "srcIn": 1.0166, "srcOut": 2.0499},
        {"id": "b", "track": "v1", "media": "m2", "srcIn": 0.0166, "srcOut": 1.0499, "broll": True},
        {"id": "s", "track": "s1", "media": "sfx_pop", "srcIn": 0.0166, "srcOut": 0.5},
    ]}
    session._snap_to_frames(q)
    v = q["clips"][0]
    assert abs(v["srcIn"] * 30 - round(v["srcIn"] * 30)) < 1e-3
    assert abs(v["srcOut"] * 30 - round(v["srcOut"] * 30)) < 1e-3
    assert q["clips"][1]["srcIn"] == 0.0166 and q["clips"][2]["srcIn"] == 0.0166


def test_captions_above_broll():
    q = {"subtitles": {"style": {"font": "Montserrat", "y": 0.8, "position": "bottom"}}, "clips": [
        {"id": "p", "track": "v2", "start": 2.0, "srcIn": 0, "srcOut": 3.0, "pip": {"y": 0.72}},
        {"id": "c_in", "track": "c1", "start": 2.5, "srcIn": 0, "srcOut": 1.0},
        {"id": "c_out", "track": "c1", "start": 6.0, "srcIn": 0, "srcOut": 1.0},
    ]}
    session._captions_above_broll(q, {"y": 0.17})
    cin = q["clips"][1]
    cout = q["clips"][2]
    assert cin["y"] == 0.17 and cin["position"] == "top" and cin["manual"] and cin["font"] == "Montserrat"
    assert "y" not in cout
