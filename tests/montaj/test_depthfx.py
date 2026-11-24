"""Dərinlik effektləri (montaj/depthfx.py): sintetik "insan" (məlum maska) üzərində hər effektin həndəsəsi.

MediaPipe real insan tələb edir, ona görə seqmentator məlum siluetlə əvəz olunur — burada effektlərin kompozisiyası,
vaxt pəncərələri və video emalı yoxlanılır.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image, ImageDraw

from montaj import background, depthfx

W, H, FPS = 540, 960, 30
TH = {"primary": "#C9577D", "primaryDeep": "#5A1E3C"}


def person_mask(t: float) -> np.ndarray:
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    cx = W / 2 + 20 * np.sin(t * 1.5)
    d.ellipse([cx - 85, 260, cx + 85, 465], fill=255)
    d.rectangle([cx - 35, 450, cx + 35, 530], fill=255)
    d.rounded_rectangle([cx - 210, 510, cx + 210, H + 25], radius=110, fill=255)
    return np.asarray(im, np.float32) / 255


def frame(t: float) -> np.ndarray:
    y = np.linspace(0, 1, H)[:, None, None]
    x = np.linspace(0, 1, W)[None, :, None]
    bg = np.broadcast_to(np.array([196, 178, 160]) * (1 - y) + np.array([120, 100, 86]) * y + 25 * np.sin(x * 18), (H, W, 3)).copy()
    cv2.rectangle(bg, (40, 150), (165, 350), (90, 120, 150), -1)
    m = person_mask(t)[..., None]
    pers = np.where(np.arange(H)[:, None, None] < 500, np.array([225, 180, 150]), np.array([40, 60, 90]))
    return (bg * (1 - m) + pers * m).clip(0, 255).astype(np.uint8)


class FakeSeg:
    def __init__(self, *a):
        self.i = 0

    def person(self, small):
        m = person_mask(self.i / FPS)
        self.i += 1
        return cv2.resize(m, (small.shape[1], small.shape[0]))

    def close(self):
        pass


@pytest.fixture()
def fake_seg(monkeypatch):
    monkeypatch.setattr(background, "Segmenter", FakeSeg)


def run_frame(e: dict, t_local: float, t_frame: float = 0.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    e = depthfx.normalize(e, TH)
    f8 = frame(t_frame)
    m = person_mask(t_frame)
    out = depthfx.apply_frame(f8, m, [e], [e["start"] + t_local], [{}])
    return f8, m, out


def test_normalize_validates():
    with pytest.raises(ValueError):
        depthfx.normalize({"type": "nope", "start": 0, "dur": 1})
    with pytest.raises(ValueError):
        depthfx.normalize({"type": "behind", "start": 0, "dur": 1})  # text yoxdur
    e = depthfx.normalize({"type": "behind", "text": "x", "start": 1, "dur": 0.5}, TH)
    assert e["fadeIn"] <= 0.25 and e["color"] == TH["primary"]


def test_az_upper():
    assert depthfx.az_upper("inkişaf ılıq") == "İNKİŞAF ILIQ"


def test_envelope_window():
    e = depthfx.normalize({"type": "focus", "start": 2, "dur": 2}, TH)
    assert depthfx.envelope(e, 1.9) == 0 and depthfx.envelope(e, 3.0) == 1 and depthfx.envelope(e, 4.1) == 0


def test_behind_text_never_covers_person():
    f8, m, out = run_frame({"type": "behind", "text": "İNKİŞAF", "start": 0, "dur": 3, "y": 0.33}, 1.0)
    person = m > 0.99
    diff = np.abs(out.astype(int) - f8.astype(int)).sum(axis=2)
    assert diff[person].max() <= 3  # insan toxunulmaz
    assert (diff[~person] > 40).sum() > 2000  # yazı fonda görünür


def test_text3d_front_and_behind():
    f8, m, out = run_frame({"type": "text3d", "text": "3 SİRR", "start": 0, "dur": 3, "behind": True}, 1.5)
    diff = np.abs(out.astype(int) - f8.astype(int)).sum(axis=2)
    assert diff[m > 0.99].max() <= 3 and (diff > 40).sum() > 1500
    _, _, out2 = run_frame({"type": "text3d", "text": "3 SİRR", "start": 0, "dur": 3, "behind": False, "y": 0.4}, 1.5)
    assert (np.abs(out2.astype(int) - f8.astype(int)).sum(axis=2)[m > 0.99] > 40).sum() > 200  # önündə — insanı örtür


def test_sticker_outline_and_no_wraparound():
    f8, m, out = run_frame({"type": "sticker", "start": 0, "dur": 3, "lift": 0}, 1.0)
    ring = (depthfx._dilate(m, int(W * 0.012) - 1) > 0.9) & (m < 0.01)
    assert out[ring].mean() > 200  # ağ kontur
    assert out[:3].mean() > 0.3 * f8[:3].mean()  # kölgə aşağı kənardan yuxarı keçmir
    assert np.abs(out[m > 0.99].astype(int) - f8[m > 0.99].astype(int)).max() <= 3


def test_focus_changes_only_background():
    f8, m, out = run_frame({"type": "focus", "bg": "gray", "amount": 0.8, "start": 0, "dur": 3}, 1.5)
    assert np.abs(out[m > 0.99].astype(int) - f8[m > 0.99].astype(int)).max() <= 3
    bgpx = out[m < 0.01].astype(int)
    assert np.abs(bgpx[:, 0] - bgpx[:, 2]).mean() < 6  # fon boz


def test_popout_head_breaks_out_of_card():
    f8, m, out = run_frame({"type": "popout", "start": 0, "dur": 3}, 1.5)
    assert np.abs(out[5, 5].astype(int) - np.array([201, 87, 125])).sum() < 60  # künc — brend fonu
    # başın üst hissəsi kartın üst kənarından yuxarıdadır, amma görünür (fon rəngi deyil)
    col = out[:, W // 2].astype(int)
    canvas = np.abs(col - col[5]).sum(axis=1) < 30
    first_person = np.argmax(~canvas[10:]) + 10
    edge_left = out[:, int(W * 0.16)].astype(int)
    card_top = np.argmax(np.abs(edge_left - edge_left[5]).sum(axis=1) > 60)
    assert first_person < card_top


def test_process_video(tmp_path, fake_seg):
    src = tmp_path / "src.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(src)], stdin=subprocess.PIPE)
    for i in range(60):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close()
    p.wait()
    fx = [depthfx.normalize(e, TH) for e in [{"type": "behind", "text": "SİRR", "start": 0.5, "dur": 0.6},
                                             {"type": "parallax", "start": 1.2, "dur": 0.6}]]
    # klip mənbənin 0.0–2.0 hissəsidir, zaman xəttində 0-dan başlayır
    info = depthfx.process(src, tmp_path / "out.mp4", fx, [(0.0, 2.0, 0.0)])
    assert info["frames"] == 60
    assert 30 <= info["touched"] <= 40  # yalnız pəncərələr (0.5–1.1, 1.2–1.8)
    assert background.probe(tmp_path / "out.mp4")["w"] == W


def test_sticker_lift_enlarges_person():
    f8, m, out = run_frame({"type": "sticker", "start": 0, "dur": 3, "lift": 0.05, "bg": "color", "bgColor": "#000000"}, 1.0)
    skin = (np.abs(out.astype(int) - np.array([225, 180, 150])).sum(axis=2) < 20).sum()
    skin0 = (np.abs(f8.astype(int) - np.array([225, 180, 150])).sum(axis=2) < 20).sum()
    assert skin > skin0 * 1.05  # insan bir az böyüyüb ("qalxır")


def test_stagger_letters_enter_one_by_one():
    e = {"type": "behind", "text": "ABCDEF", "start": 0, "dur": 3, "y": 0.15, "integrate": 0}
    _, _, early = run_frame(e, 0.08)
    f8, _, late = run_frame(e, 1.0)
    d_early = (np.abs(early.astype(int) - f8.astype(int)).sum(axis=2) > 40).sum()
    d_late = (np.abs(late.astype(int) - f8.astype(int)).sum(axis=2) > 40).sum()
    assert 0 < d_early < d_late * 0.5  # əvvəl yalnız ilk hərflər


def test_popout_transition_has_no_ghost():
    """Keçidin ortasında kadr kiçilir — iki kadrın yarımşəffaf qarışığı (xəyalət) olmamalıdır."""
    e = depthfx.normalize({"type": "popout", "start": 0, "dur": 3}, TH)
    f8, m = frame(0), person_mask(0)
    out = depthfx.apply_frame(f8, m, [e], [e["fadeIn"] * 0.5], [{}])
    canvas_top = np.abs(out[3, 3].astype(int) - np.array([201, 87, 125])).sum()
    assert canvas_top < 80  # künc — təmiz brend fonu, orijinal kadrla qarışıq deyil


def test_sfx_cues_follow_effects():
    fx = [depthfx.normalize(e, TH) for e in [{"type": "behind", "text": "x", "start": 2, "dur": 2},
                                             {"type": "text3d", "text": "y", "start": 5, "dur": 2},
                                             {"type": "sticker", "start": 8, "dur": 1}]]
    cues = depthfx.sfx_cues(fx, {"fx_whoosh_soft": 0.1, "fx_whoosh": 0.15})
    kinds = [c["kind"] for c in cues]
    assert kinds == ["fx_whoosh_soft", "fx_whoosh", "fx_hit", "fx_pop"]
    assert abs(cues[0]["t"] - 2.12) < 1e-6 and cues[2]["t"] > cues[1]["t"]
