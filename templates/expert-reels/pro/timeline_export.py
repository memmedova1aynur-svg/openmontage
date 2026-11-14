"""Montaj qərarlarını NLE layihəsi kimi saxlamaq: OpenTimelineIO → Premiere Pro (FCP7 XML), DaVinci Resolve / Final Cut (FCPXML), .otio.

Niyə: yalnız yekun MP4 olanda bir düzəliş üçün bütün video yenidən qurulurdu. Timeline faylı ilə
(1) bizim render yalnız dəyişən hissəni yenidən qurur, (2) lazım olsa layihə Premiere/Resolve-da açılır.

Giriş: timeline.json
{"name": "...", "fps": 30, "width": 1080, "height": 1920,
 "tracks": [{"kind": "video"|"audio", "name": "V1 Danışan", "clips": [{"src": "/abs/fayl", "in": 0.0, "out": 3.2, "at": 0.0, "name": "..."}]}],
 "markers": [{"t": 3.4, "name": "Kart: ...", "color": "RED"}]}
İstifadə: python3 timeline_export.py timeline.json <çıxış_qovluğu>  → <ad>.otio, <ad>_premiere.xml, <ad>_resolve.fcpxml
"""
import json, sys
from pathlib import Path
import opentimelineio as otio


def rt(sec, fps): return otio.opentime.RationalTime(round(sec * fps), fps)


_DUR = {}
def media_dur(p):
    if p not in _DUR:
        import subprocess
        _DUR[p] = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout or 0)
    return _DUR[p]


def build(tl_json):
    fps = tl_json.get("fps", 30); T = otio.schema.Timeline(name=tl_json.get("name", "montaj"))
    T.global_start_time = rt(0, fps)
    for tr in tl_json["tracks"]:
        kind = otio.schema.TrackKind.Video if tr["kind"] == "video" else otio.schema.TrackKind.Audio
        track = otio.schema.Track(name=tr["name"], kind=kind); cur = 0.0
        for c in sorted(tr["clips"], key=lambda c: c["at"]):
            if c["at"] - cur > 1e-3: track.append(otio.schema.Gap(source_range=otio.opentime.TimeRange(rt(0, fps), rt(c["at"] - cur, fps))))
            ref = otio.schema.ExternalReference(target_url=Path(c["src"]).resolve().as_uri(),
                                                available_range=otio.opentime.TimeRange(rt(0, fps), rt(media_dur(str(c["src"])), fps)))
            dur = c["out"] - c["in"]
            clip = otio.schema.Clip(name=c.get("name") or Path(c["src"]).stem, media_reference=ref,
                                    source_range=otio.opentime.TimeRange(rt(c["in"], fps), rt(dur, fps)))
            if c.get("meta"): clip.metadata["montaj"] = c["meta"]
            track.append(clip); cur = c["at"] + dur
        T.tracks.append(track)
    for m in tl_json.get("markers", []):
        T.tracks[0].markers.append(otio.schema.Marker(name=m["name"], marked_range=otio.opentime.TimeRange(rt(m["t"], fps), rt(0, fps)),
                                                      color=m.get("color", "RED")))
    return T


def export(tl_json, out_dir):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True); T = build(tl_json); name = tl_json.get("name", "montaj")
    paths = {"otio": out / f"{name}.otio", "premiere": out / f"{name}_premiere.xml", "resolve": out / f"{name}_resolve.fcpxml"}
    otio.adapters.write_to_file(T, str(paths["otio"]))
    otio.adapters.write_to_file(T, str(paths["premiere"]), adapter_name="fcp_xml")
    try: otio.adapters.write_to_file(T, str(paths["resolve"]), adapter_name="fcpx_xml")
    except Exception as e: paths.pop("resolve"); print("FCPXML yazılmadı:", e)
    # yoxlama: yazılan fayllar geri oxunur, klip sayı uyğun gəlir
    n = sum(len([c for c in tr if isinstance(c, otio.schema.Clip)]) for tr in T.tracks)
    back = otio.adapters.read_from_file(str(paths["premiere"]), adapter_name="fcp_xml")
    nb = sum(len([c for c in tr if isinstance(c, otio.schema.Clip)]) for tr in back.tracks)
    return {k: str(v) for k, v in paths.items()}, n, nb


if __name__ == "__main__":
    tl = json.load(open(sys.argv[1])); p, n, nb = export(tl, sys.argv[2]); print(json.dumps({"files": p, "clips": n, "premiere_reread_clips": nb}, ensure_ascii=False))
