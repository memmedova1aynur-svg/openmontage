"""P1 (creative editing intelligence): nisbi səs balansı, _latest_render, preflight kontrastı."""

from __future__ import annotations

import numpy as np

from montaj import premix, preflight


def test_gain_matches_manual_tuning():
    # Sura sınağı: danışıq −34.7 LUFS, musiqi −11.3 LUFS → əl ilə tapılan 0.012 (15 LU) / hesablanan 16 LU ≈ 0.0107
    g = premix.gain(-34.7 - premix.MUSIC_UNDER_LU, -11.3)
    assert 0.009 < g < 0.013
    # SFX pik −0.9 dBFS, danışıq piki −14.8 dBFS → 12 dB aşağı ≈ 0.05
    assert 0.045 < premix.gain(-14.8 - premix.SFX_UNDER_DB, -0.9) < 0.056


def test_gain_clamped():
    assert premix.gain(-80, 0) == premix.MIN_GAIN
    assert premix.gain(10, -40) == premix.MAX_GAIN


def test_auto_detection():
    assert premix._is_auto(None) and premix._is_auto("auto") and premix._is_auto(" AUTO ")
    assert not premix._is_auto(0.12) and not premix._is_auto(0)


def test_explicit_volume_kept(tmp_path):
    out = premix.resolve({"media": [], "clips": [], "tracks": []}, tmp_path,
                         [{"file": "x.mp3", "volume": 0.12}], [{"kind": "pop", "vol": 0.2}], {})
    assert out["music"][0]["volume"] == 0.12 and out["sfx"][0]["vol"] == 0.2 and out["report"]["speech"] is None


def test_latest_render_ignores_ig_copy(tmp_path, monkeypatch):
    from montaj import session

    monkeypatch.setattr(session, "out_dir", lambda pid: tmp_path)
    for n in ("p_r3.mp4", "p_r10.mp4", "p_r10_ig.mp4", "p_r10_yoxlama.json"):
        (tmp_path / n).write_bytes(b"x")
    assert session._latest_render("p").name == "p_r10.mp4"


def _frame(rgb, w=360, h=640):
    return np.full((h, w, 3), rgb, dtype=np.uint8)


def test_caption_contrast_stroke_on_beige_is_low():
    clip = {"color": "#C9577D", "activeColor": "#C9577D", "bg": "none"}  # çəhrayı mətn, bej fon (sınaqdakı hal)
    r = preflight.caption_contrast(_frame((225, 205, 185)), clip)
    assert not r["ok"] and r["mode"] == "stroke"


def test_caption_contrast_white_on_dark_ok():
    r = preflight.caption_contrast(_frame((30, 30, 40)), {"color": "#FFFFFF", "bg": "none"})
    assert r["ok"]


def test_caption_contrast_box_ok():
    r = preflight.caption_contrast(_frame((225, 205, 185)), {"color": "#9E3D5E", "activeColor": "#C9577D", "bg": "#F2E4D6@0.85"})
    assert r["mode"] == "box" and r["ok"]
