"""disfluency.py: yarımçıq dubl, cümlə içi təkrar, operator sualı və «ıı» aşkarlanır; kəsim sərhədi sözə toxunmur."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "templates/expert-reels/pro"))
import disfluency as D


def seg(s, words):
    w, t = [], s
    for x in words.split():
        w.append([t, t + 0.4, x, 0.9]); t += 0.45
    return {"s": s, "e": t, "t": words, "w": w}


class FakeWave:
    def __init__(self, segs):
        self.sr = 16000; n = int((max(s["e"] for s in segs) + 2) * self.sr); self.db = np.full(n, -60.0)
        for s in segs:
            for a, b, *_ in s["w"]: self.db[int(a * self.sr):int(b * self.sr)] = -15
    at = D.Wave.at
    quietest = D.Wave.quietest


def test_flags_and_keep():
    segs = [seg(1, "Hər valideynin bilməli olduğu üç qayda."),
            seg(4, "Birincisi, uşağınızı heç bir uşaqla..."),
            seg(8, "Birincisi, övladınızı heç bir uşaqla müqayisə etməyin."),
            seg(13, "Sonra nə?"),
            seg(15, "ıı"),
            seg(16, "Hər uşaq fərqlidir və özlərini hörmət etməyi öyrənsinlər"),
            seg(22, "özlərinə hörmət etməyi, sosiallaşmağı öyrənsinlər.")]
    D.analyse(segs)
    fl = {s["i"]: s["flags"] for s in segs}
    assert any(f.startswith("restart") for f in fl[1])
    assert any(f.startswith("chatter") for f in fl[3])
    assert "filler" in fl[4]
    assert any(f.startswith("tail-restart") for f in fl[5])
    wv = FakeWave(segs); keep = D.plan_keep(segs, wv)
    kept = [w for s in segs for w in s["w"] if any(a <= w[0] and w[1] <= b for a, b in keep)]
    txt = " ".join(w[2] for w in kept)
    assert "uşağınızı" not in txt and "Sonra" not in txt and "övladınızı" in txt
    for a, b in keep:  # sərhəd sözün içinə düşmür
        assert wv.at(a) < -30 and wv.at(b) < -30
