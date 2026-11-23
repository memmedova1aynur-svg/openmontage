"""Çəkiliş paketi: qovluq → hər video ayrıca layihə, davam etdirilə bilən addımlar, xəta digərlərini dayandırmır."""

from __future__ import annotations

import shutil

import pytest

pytestmark = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg yoxdur")

from tests.montaj.test_montaj import make_silence_source


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("MONTAJ_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("MONTAJ_OUT_DIR", str(tmp_path / "out"))
    a = make_silence_source(tmp_path / "v01.mp4")
    b = shutil.copyfile(a, tmp_path / "v02.mp4")
    return [str(a), str(b)]


def test_batch_creates_project_per_video_and_resumes(env):
    from montaj import batch, session, store

    assert session.main(["batch", "--client", "Lamiyə", "--date", "2026-12-01", "--file", env[0], "--file", env[1],
                         "--steps", "new"]) == 0
    m = batch.load("lamiye-2026-12-01")
    assert [v["pid"] for v in m["videos"]] == ["lamiye-2026-12-01-01", "lamiye-2026-12-01-02"]
    assert all(v["steps"] == {"new": "ok"} for v in m["videos"])
    assert store.load("lamiye-2026-12-01-01")["brand"]["name"] == "Lamiyə"

    # təkrar işə salma: bitmiş addım təkrarlanmır, yeni layihə yaranmır
    assert session.main(["batch", "--id", "lamiye-2026-12-01", "--steps", "new"]) == 0
    assert not (store.projects_dir() / "lamiye-2026-12-01-01-2").exists()


def test_batch_error_does_not_stop_other_videos(env, monkeypatch):
    from montaj import batch

    m = batch.create("Lamiyə", "2026-12-02", files=env)
    real = batch._run

    def fake(argv):
        if argv[0] == "storyboard" and argv[1].endswith("-01"):
            return 2, "XƏTA: transkripsiya alınmadı\nNƏ ETMƏLİ: ..."
        if argv[0] == "storyboard":
            return 0, "ok"
        return real(argv)

    monkeypatch.setattr(batch, "_run", fake)
    m = batch.run(m, steps=["new", "storyboard"], log=lambda s: None)
    assert m["videos"][0]["steps"]["storyboard"] == "xəta: transkripsiya alınmadı"
    assert m["videos"][1]["steps"] == {"new": "ok", "storyboard": "ok"}
    text = batch.summary(m)
    assert "hazır: 1" in text and "transkripsiya alınmadı" in text
    assert (batch.out_root() / "batches" / "lamiye-2026-12-02.md").is_file()


def test_batch_review_collects_plans(env):
    import json

    from montaj import batch

    m = batch.create("Lamiyə", "2026-12-03", files=env)
    m = batch.run(m, steps=["new"], log=lambda s: None)
    p = batch.plan_path(m["videos"][0]["pid"])
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"summary": "Sınaq", "before": 60, "after": 42, "cuts": [{"at": "0:12", "len": 1.5, "why": "təkrar"}],
                             "extra": "yox"}), encoding="utf-8")
    out = batch.write_review([m["id"]], batch.out_root() / "review" / "plans.json")
    d = json.loads(out.read_text())
    v1, v2 = d["batches"][0]["videos"]
    assert v1["plan"]["cuts"][0]["why"] == "təkrar" and "extra" not in v1["plan"]
    assert v2["plan"] is None


def test_schedule_spreads_over_period():
    from montaj import batch

    s = batch.schedule(10, "2026-12-01")
    assert s[0] == ("2026-12-01", "19:00") and s[-1][0] == "2026-12-14"
    assert len({d for d, _ in s}) == 10, "hər paylaşım ayrı gündə"


def test_batch_pack_builds_calendar(env):
    import json
    import shutil as sh

    from montaj import batch

    m = batch.create("Lamiyə", "2026-12-04", files=env)
    m = batch.run(m, steps=["new"], log=lambda s: None)
    pid = m["videos"][0]["pid"]
    sh.copyfile(env[0], batch.out_root() / pid / f"{pid}_r3.mp4")
    (batch.out_root() / pid / "caption.json").write_text(json.dumps({"caption": "Birinci sətir\nikinci", "hashtags": ["#uşaq"]}))
    r = batch.pack(m["id"], "2026-12-02")
    d = batch.out_root() / "batches" / f"{m['id']}_paket"
    assert [x["file"] for x in r["rows"]] == ["01_2026-12-02_19-00.mp4"] and r["missing"] == [2]
    assert (d / "01_2026-12-02_19-00_caption.txt").read_text().endswith("#uşaq\n")
    assert (d / "teqvim.csv").is_file() and "Birinci sətir" in (d / "teqvim.md").read_text()
