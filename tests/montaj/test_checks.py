import numpy as np

from montaj import checks


def _fake_plan(monkeypatch, clips):
    vids, t = [], 0.0
    for c in clips:
        d = c["srcOut"] - c["srcIn"]
        vids.append({"clip": c, "start": t, "dur": d})
        t += d
    monkeypatch.setattr("montaj.render.render_plan", lambda p: {"video": vids})
    monkeypatch.setattr("montaj.render._continuous", lambda a, b: a["srcOut"] == b["srcIn"] and a["media"] == b["media"])


WORDS = {"m": {"words": [{"w": "salam", "s": 0.15, "e": 0.50}, {"w": "dostlar", "s": 0.60, "e": 1.20}, {"w": "bu", "s": 1.30, "e": 1.50}, {"w": "gün", "s": 1.60, "e": 1.90}]}}


def test_cut_inside_word_is_bad(monkeypatch):
    _fake_plan(monkeypatch, [{"media": "m", "srcIn": 0.0, "srcOut": 0.9}, {"media": "m", "srcIn": 1.3, "srcOut": 2.0}])
    r = checks.cut_boundaries({}, WORDS)
    assert r["status"] == "bad" and "dostlar" in r["items"][0]


def test_cut_in_gap_is_ok(monkeypatch):
    _fake_plan(monkeypatch, [{"media": "m", "srcIn": 0.0, "srcOut": 0.56}, {"media": "m", "srcIn": 1.25, "srcOut": 2.0}])
    assert checks.cut_boundaries({}, WORDS)["status"] == "ok"


def test_cut_right_after_word_end_warns(monkeypatch):
    _fake_plan(monkeypatch, [{"media": "m", "srcIn": 0.0, "srcOut": 0.51}, {"media": "m", "srcIn": 1.25, "srcOut": 2.0}])
    assert checks.cut_boundaries({}, WORDS)["status"] == "warn"


def test_muffled_has_lower_hf_ratio():
    sr = 16000
    t = np.arange(sr * 2) / sr
    rng = np.random.default_rng(0)
    bright = 0.3 * np.sin(2 * np.pi * 500 * t) + 0.2 * rng.standard_normal(len(t)) * np.sin(2 * np.pi * 3 * t) ** 2
    # low-pass by moving average = muffled
    muffled = np.convolve(bright, np.ones(16) / 16, mode="same")
    r0, fr = checks.band_ratio_db(bright.astype(np.float32))
    r1, _ = checks.band_ratio_db(muffled.astype(np.float32), fr)
    assert r1 - r0 < checks.HF_DROP_BAD


def test_framing_centered_ok_and_offcenter_bad():
    good = [{"x": 0.4, "y": 0.2, "w": 0.2, "h": 0.2}]
    off = [{"x": 0.1, "y": 0.2, "w": 0.2, "h": 0.2}]
    assert checks.framing([good], ["a"])["status"] == "ok"
    r = checks.framing([off], ["a"])
    assert r["status"] == "bad" and r["mean_dx"] < -0.25
    assert checks.framing([[]], ["a"])["status"] == "skip"


def test_framing_head_room_and_small_face():
    assert checks.framing([[{"x": 0.45, "y": 0.0, "w": 0.1, "h": 0.2}]], ["a"])["status"] == "bad"
    assert checks.framing([[{"x": 0.47, "y": 0.2, "w": 0.06, "h": 0.06}]], ["a"])["status"] == "bad"


def _frame(rgb):
    return np.full((100, 100, 3), rgb, dtype=np.uint8)


def test_skin_tone():
    f = {"x": 0.3, "y": 0.2, "w": 0.4, "h": 0.4}
    assert checks.skin_ok(_frame((210, 160, 130)), f)[0]
    assert not checks.skin_ok(_frame((230, 190, 60)), f)[0]   # sarı
    assert not checks.skin_ok(_frame((255, 60, 60)), f)[0]    # qırmızı
    assert not checks.skin_ok(_frame((190, 185, 180)), f)[0]  # solğun


def test_adjust_limits():
    p = {"clips": [{"id": "c1", "track": "v1", "adjust": {"saturation": 1.3, "contrast": 1.02}}, {"id": "c2", "track": "v1", "adjust": {"sharpen": 0.2}}]}
    out = checks.adjust_limits(p)
    assert len(out) == 1 and "saturation" in out[0]


def test_recenter_shifts_keys():
    p = {"clips": [{"track": "v1", "frame": {"mode": "auto", "baseW": 0.5, "s": 1, "keys": [{"t": 0, "cx": 0.5, "cy": 0.4}]}}]}
    q = checks.recenter(p, -0.1)
    assert q["clips"][0]["frame"]["keys"][0]["cx"] == 0.45
    assert p["clips"][0]["frame"]["keys"][0]["cx"] == 0.5


def _burst_signal(spec, total, sr=16000):
    """spec: [(başla, bitir)] saniyə — bu aralıqlarda səs-küy, qalanı sakitlik."""
    rng = np.random.default_rng(1)
    x = np.zeros(int(total * sr), dtype=np.float32)
    for a, b in spec:
        i0, i1 = int(round(a * sr)), int(round(b * sr))
        x[i0:i1] = 0.2 * rng.standard_normal(i1 - i0)
    return x


def test_scan_edge_flags_stray_burst_at_start():
    x = _burst_signal([(0.4, 0.58), (1.05, 1.9)], 2.2)  # 0.18 s kənar səs, 0.47 s sakitlik, sonra real söz
    assert any("təcrid" in p for p in checks.scan_edge(x, 0.3, "in"))


def test_scan_edge_clean_start_and_end():
    x = _burst_signal([(0.5, 1.4)], 2.0)
    assert checks.scan_edge(x, 0.3, "in") == []
    assert checks.scan_edge(x, 1.7, "out") == []


def test_scan_edge_flags_cut_inside_speech():
    x = _burst_signal([(0.2, 1.8)], 2.2)
    assert any("içindədir" in p for p in checks.scan_edge(x, 1.0, "out"))
    assert any("içindədir" in p for p in checks.scan_edge(x, 1.0, "in"))


def test_scan_edge_flags_stray_tail():
    x = _burst_signal([(0.2, 1.0), (1.5, 1.68)], 2.2)  # söz bitir, 0.5 s sakitlik, qısa kənar səs
    assert any("təcrid" in p for p in checks.scan_edge(x, 2.0, "out"))


def test_tail_after_last_word():
    x = _burst_signal([(0.2, 1.4)], 2.0)
    assert abs(checks.tail_after_last_word(x, 1.9) - 0.5) < 0.1
    assert checks.tail_after_last_word(x, 1.5) < 0.2


def test_captionqa_flags_word_not_heard():
    from montaj import captionqa
    from montaj.transcribe import fold

    cues = [(0.0, 2.0, "Bağça müəllimi dərs keçir")]
    heard = {"a": [(fold("baxça"), 0.0, 0.5), (fold("müəllimi"), 0.5, 1.0), (fold("dəst"), 1.0, 1.4), (fold("keçir"), 1.5, 2.0)]}
    bad = captionqa.compare(cues, heard)
    assert [x["caption"] for x in bad] == ["dərs"]  # "baxça"≡"bağça" hərf qarışıqlığıdır — problem deyil


def test_snap_glossary_exact_fold_only():
    from montaj import transcribe

    w, ch = transcribe.snap_glossary([{"w": "baxça"}, {"w": "oyunlar"}, {"w": "Baxçada."}], ["bağça", "bağçada", "oyunları"])
    assert [x["w"] for x in w] == ["bağça", "oyunlar", "Bağçada."]
