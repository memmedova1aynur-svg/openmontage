"""Müştəri qovluğundan yalnız yeni videolar: profil `drive.folder` → `batch --new`, `--mark-seen`."""

from __future__ import annotations

import json

import pytest

FOLDER = "https://drive.google.com/drive/folders/" + "F" * 28


def _tree(items):
    return lambda link: [dict(i, link=f"https://drive.google.com/file/d/{i['id']}/view") for i in items]


@pytest.fixture()
def prof(tmp_path, monkeypatch):
    monkeypatch.setenv("MONTAJ_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("MONTAJ_OUT_DIR", str(tmp_path / "out"))
    pf = tmp_path / "aytan.json"
    pf.write_text(json.dumps({"name": "Aytən Cəlilova", "drive": {"folder": FOLDER}}, ensure_ascii=False), encoding="utf-8")
    from montaj import session

    monkeypatch.setattr(session, "profile_path", lambda name: pf)
    return pf


def test_new_takes_only_unseen_videos_and_remembers_them(prof):
    from montaj import batch
    from montaj.errors import UserError

    old = [{"id": "a" * 25, "name": "IMG_1.MOV", "folder": None}]
    batch.mark_seen("Aytən Cəlilova", lister=_tree(old))
    assert "a" * 25 in json.loads(prof.read_text(encoding="utf-8"))["drive"]["seen"]

    items = old + [{"id": "b" * 25, "name": "IMG_2.MOV", "folder": "2026-12-01"},
                   {"id": "c" * 25, "name": "IMG_3.mp4", "folder": "2026-12-01"},
                   {"id": "d" * 25, "name": "mövzular.pdf", "folder": "2026-12-01"}]
    m = batch.new_from_profile("Aytən Cəlilova", lister=_tree(items))
    assert m["date"] == "2026-12-01"  # tarix qovluğun adından
    assert [v["name"] for v in m["videos"]] == ["IMG_2.MOV", "IMG_3.mp4"]  # köhnə və pdf yoxdur
    assert m["videos"][0]["drive_id"] == "b" * 25

    seen = json.loads(prof.read_text(encoding="utf-8"))["drive"]["seen"]
    assert {"b" * 25, "c" * 25} <= set(seen)
    with pytest.raises(UserError, match="yeni video yoxdur"):
        batch.new_from_profile("Aytən Cəlilova", lister=_tree(items))


def test_new_without_folder_in_profile_explains(prof):
    from montaj import batch
    from montaj.errors import UserError

    prof.write_text(json.dumps({"name": "Aytən Cəlilova"}), encoding="utf-8")
    with pytest.raises(UserError, match="Drive qovluğu yoxdur"):
        batch.new_from_profile("Aytən Cəlilova", lister=_tree([]))


def test_list_tree_reads_date_subfolders_and_skips_ready(monkeypatch):
    from montaj import drive

    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setattr(drive, "_api_key", lambda: "")
    root, day, ready = "R" * 28, "D" * 28, "H" * 28

    def page(entries):
        rows = "".join(f'<div id="entry-{i}"><a href="https://drive.google.com/{"drive/folders" if f else "file/d"}/{i}">'
                       f'<div class="flip-entry-title">{n}</div></a></div>' for i, n, f in entries)
        return rows

    pages = {root: page([("r" * 25, "kök.mov", False), (day, "2026-12-01", True), (ready, "Hazır", True)]),
             day: page([("x" * 25, "IMG_9.MOV", False)]),
             ready: page([("z" * 25, "final.mp4", False)])}

    class R:
        status_code = 200

        def __init__(self, text):
            self.text = text

    class S:
        def get(self, url, params=None, timeout=None):
            return R(pages[params["id"]])

    out = drive.list_tree("https://drive.google.com/drive/folders/" + root, session=S())
    assert [(f["name"], f["folder"]) for f in out] == [("kök.mov", None), ("IMG_9.MOV", "2026-12-01")]


def test_folder_date_formats():
    from montaj.batch import folder_date

    assert folder_date("2026-11-24") == "2026-11-24"
    assert folder_date("24.11.2026") == "2026-11-24"
    assert folder_date("Çəkiliş 3.12.2026") == "2026-12-03"
    assert folder_date("Hazır") is None
    assert folder_date(None) is None
