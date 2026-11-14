"""Montaj engine v3 — bir talking-head videosu üçün tam zəncir, hər mərhələnin vaxtı ölçülür.

Mərhələlər (hər biri ayrıca modul, uğursuz olsa video problem siyahısına düşür, digərləri davam edir):
  1 plan      disfluency.py  — VAD-sız ASR + yarımçıq dubl/ıı/söhbət + MMS dəqiq sərhəd  (keş: <iş>/kesim)
  2 color     color_auto.py  — bu videonun ölçülmüş rəng korreksiyası (HDR → SDR daxil)
  3 cut       ffmpeg         — saxlanılan parçalar, kadraj (yaxınlaşdırma/baş üstü), rəng; parça sərhədində 15 ms səs keçidi
  4 audio     audio_pro.py   — ölçülmüş küy təmizləmə + EQ/kompressor/de-esser + −14 LUFS
  5 subs      ASS altyazı    — MMS ilə oturdulmuş sözlər, 3–4 sözlük oxunaqlı hissələr, brend rəngi
  6 motion    motion.py      — ad lövhəsi (və istəyə görə başlıq) şəffaf overlay
  7 compose   ffmpeg         — clean (qrafikasız) + final
  8 qc        qc_render.py   — kadraj, qrafika-üz, rəng, səs, export; keçməsə FINAL-a düşmür
  9 timeline  timeline_export.py — .otio + Premiere XML + Resolve FCPXML
İstifadə: python3 engine.py <video> --client <müştəri> --name 01_movzu [--title "Sətir1|Sətir2"] [--work DIR] [--zoom 1.12 --cy 0.6]
"""
import argparse, json, os, subprocess, sys, time
from pathlib import Path
A = Path(__file__).resolve().parent; sys.path.insert(0, str(A))
ROOT = A.parents[2]


def run(a, **k):
    r = subprocess.run(a, capture_output=True, text=True, **k)
    if r.returncode: raise RuntimeError(" ".join(map(str, a[:3])) + ": " + (r.stderr or r.stdout)[-600:])
    return r


def ass_time(t): h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60; return f"{h}:{m:02d}:{s:05.2f}"


def write_ass(words, path, brand, W=1080, H=1920):
    pal = brand.get("palette") or {}
    hi = pal.get("acc2") or pal.get("acc") or "#F2AAB9"
    bgr = lambda h: "&H00" + h[5:7] + h[3:5] + h[1:3]
    L = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "", "[V4+ Styles]",
         "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
         f"Style: Cap,Montserrat,76,&H00FFFFFF,{bgr(hi)},&H64000000,&H00000000,-1,0,0,0,100,100,0,0,1,5,0,2,90,90,330,1", "",
         "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    chunk = []
    def flush():
        if not chunk: return
        a, b = chunk[0][0], chunk[-1][1] + 0.12
        for k, (s, e, w) in enumerate(chunk):  # aktiv söz brend rəngində
            txt = " ".join((r"{\c" + bgr(hi) + "&}" + x + r"{\c&H00FFFFFF&}") if j == k else x for j, (_, _, x) in enumerate(chunk))
            nb = chunk[k + 1][0] if k + 1 < len(chunk) else b
            L.append(f"Dialogue: 0,{ass_time(s if k else a)},{ass_time(nb)},Cap,,0,0,0,,{txt}")
        chunk.clear()
    for s, e, w in words:
        if chunk and (len(" ".join(x for *_, x in chunk) + w) > 24 or len(chunk) >= 4 or s - chunk[-1][1] > 0.4): flush()
        chunk.append((s, e, w))
        if w.endswith((".", "?", "!")): flush()
    flush(); open(path, "w").write("\n".join(L))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("--client", required=True); ap.add_argument("--name", required=True)
    ap.add_argument("--title"); ap.add_argument("--work"); ap.add_argument("--zoom", type=float, default=1.12); ap.add_argument("--cy", type=float, default=0.6)
    ap.add_argument("--no-motion", action="store_true")
    a = ap.parse_args(); src = Path(a.video).resolve()
    W_ = Path(a.work or Path(os.environ.get("MONTAJ_DATA_DIR", "/root/montaj-data")) / "engine" / a.client / a.name); W_.mkdir(parents=True, exist_ok=True)
    brand = json.load(open(ROOT / "instagram-clients" / a.client / "brand_kit.json")) if (ROOT / "instagram-clients" / a.client / "brand_kit.json").exists() else {}
    T = {}; t0 = time.time()
    def tick(k):
        nonlocal t0; T[k] = round(time.time() - t0, 1); t0 = time.time(); print(f"  {k}: {T[k]} s", flush=True)
    # 1 plan
    kd = W_ / "kesim"
    if not (kd / "keep.json").exists(): run([sys.executable, str(A / "disfluency.py"), str(src), "--out", str(kd)])
    keep = json.load(open(kd / "keep.json"))["keep"]; segs = json.load(open(kd / "segments.json")); tick("1_plan")
    # 2 color
    import color_auto
    trc, _ = color_auto.probe(src); st = color_auto.stats(color_auto.frames(src, color_auto.sdr_chain(trc)))
    look, mix, why = color_auto.decide(st); vf_color = color_auto.to_vf(look, mix, trc); json.dump({"vf": vf_color, "why": why}, open(W_ / "color.json", "w"), ensure_ascii=False); tick("2_color")
    # 3 cut — yalnız SƏS çıxarılır (sürətli); görüntü 7-ci mərhələdə tək keçiddə kodlanır
    parts = []; cur = 0.0; words = []
    kept_w = [w for s in segs for w in s["w"] if not any(f.startswith(("filler", "restart", "chatter")) for f in s["flags"])]
    for i, (s, e) in enumerate(keep):
        nf = round((e - s) * 30)
        for w in kept_w:
            if s - 0.01 <= w[0] and w[1] <= e + 0.01: words.append((round(cur + w[0] - s, 3), round(cur + w[1] - s, 3), w[2].strip()))
        parts.append((i, s, e, cur, nf)); cur += nf / 30
    ain = []; afc = []
    for i, s, e, at, nf in parts:
        ain += ["-ss", f"{s:.3f}", "-t", f"{nf / 30 + 0.1:.3f}", "-i", str(src)]
        afc.append(f"[{i}:a]aresample=48000,apad,atrim=0:{nf / 30:.4f},asetpts=N/SR/TB,afade=t=in:d=0.015,afade=t=out:st={max(0, nf / 30 - 0.015):.4f}:d=0.015[a{i}]")
    run(["ffmpeg", "-v", "error", "-y", *ain, "-filter_complex", ";".join(afc) + ";" + "".join(f"[a{i}]" for i, *_ in parts) + f"concat=n={len(parts)}:v=0:a=1[a]",
         "-map", "[a]", "-ac", "1", "-ar", "48000", str(W_ / "_cut.wav")])
    tick("3_cut")
    # 4 audio
    import audio_pro
    rep = audio_pro.process(W_ / "_cut.wav", W_ / "_voice.wav"); json.dump(rep, open(W_ / "audio.json", "w")); tick("4_audio")
    # 5 subs
    gl = json.load(open(A / "glossary_az.json")); fix = lambda w: next((v for k, v in gl.items() if w.lower().strip(".,?!") == k), w)
    words = [[s, e, fix(w)] for s, e, w in words if w]
    for k, v in gl.items():  # çoxsözlü düzəlişlər: «anı olsaydım» → «ana olsaydım»
        ks, vs = k.split(), v.split()
        if len(ks) < 2: continue
        for i in range(len(words) - len(ks) + 1):
            if [w[2].lower().strip(".,?!") for w in words[i:i + len(ks)]] == ks and len(vs) == len(ks):
                for j in range(len(ks)): words[i + j][2] = vs[j] + (words[i + j][2][-1] if words[i + j][2][-1] in ".,?!" else "")
    words = [tuple(w) for w in words]
    write_ass(words, W_ / "subs.ass", brand); json.dump(words, open(W_ / "subs.json", "w"), ensure_ascii=False); tick("5_subs")
    # 6 motion
    ov = []
    if not a.no_motion:
        import motion
        nm = (brand.get("profile") or {}).get("decisions", [])
        lt = next((d.split("«")[1].split("»")[0] for d in nm if d.startswith("Ad lövhəsi")), None)
        if lt and "·" in lt:
            n_, r_ = [x.strip() for x in lt.split("·", 1)]; ov.append((motion.render("LowerThird", {"name": n_, "role": r_, "y": 1300}, a.client), 2.0))
        if a.title: ov.append((motion.render("TitleReveal", {"lines": a.title.split("|"), "italic": [len(a.title.split("|")) - 1]}, a.client, 75), 0.0))
    tick("6_motion")
    # 7 tək keçidli render: hər parça öz -ss girişi ilə → kadraj (kəsimdə cüzi plan dəyişməsi) → concat → rəng → altyazı → motion
    #   eyni qrafdan iki çıxış: final (1080x1920) + clean (540x960, qrafikasız — QC üz yoxlaması üçün)
    fdir = Path(os.environ.get("MONTAJ_DATA_DIR", "/root/montaj-data")) / "fonts"
    vin = []; vfc = []
    for i, s, e, at, nf in parts:
        z = a.zoom * (1.06 if i % 2 else 1.0)
        vin += ["-ss", f"{s:.3f}", "-t", f"{nf / 30 + 0.1:.3f}", "-i", str(src)]
        vfc.append(f"[{i}:v]{vf_color + ',' if vf_color else ''}scale={int(1080 * z) // 2 * 2}:{int(1920 * z) // 2 * 2}:flags=lanczos,"
                   f"crop=1080:1920:(iw-1080)/2:(ih-1920)*{a.cy},fps=30,setpts=N/30/TB,trim=end_frame={nf},setpts=PTS-STARTPTS,format=yuv420p,setsar=1[v{i}]")
    n = len(parts); k0 = n
    fc = ";".join(vfc) + ";" + "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[cat];[cat]split=2[c0][c1];[c1]scale=540:960[clean];"
    fc += f"[c0]subtitles={W_ / 'subs.ass'}:fontsdir={fdir}[s0]"; last = "s0"; ins = list(vin)
    for k, (m, at) in enumerate(ov):
        ins += ["-i", str(m)]; fc += f";[{k0 + k}:v]setpts=PTS+{at}/TB[m{k}];[{last}][m{k}]overlay=0:0:eof_action=pass[s{k + 1}]"; last = f"s{k + 1}"
    ins += ["-i", str(W_ / "_voice.wav")]; ai = k0 + len(ov)
    final = W_ / f"{a.name}.mp4"
    run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc,
         "-map", f"[{last}]", "-map", f"{ai}:a", "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-shortest", "-movflags", "+faststart", str(final),
         "-map", "[clean]", "-map", f"{ai}:a", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-c:a", "aac", "-b:a", "96k", "-shortest", str(W_ / "clean.mp4")])
    tick("7_render")
    # 8 qc
    qc = subprocess.run([sys.executable, str(A / "qc_render.py"), str(final), "--clean", str(W_ / "clean.mp4"), "--subs", str(W_ / "subs.json"), "--out", str(W_ / "QC")], capture_output=True, text=True)
    qc_ok = qc.returncode == 0; tick("8_qc")
    # 9 timeline
    import timeline_export as TE
    tl = {"name": a.name, "fps": 30, "tracks": [
        {"kind": "video", "name": "V1 Danışan", "clips": [{"src": str(src), "in": s, "out": s + nf / 30, "at": at} for _, s, e, at, nf in parts]},
        {"kind": "video", "name": "V2 Qrafika", "clips": [{"src": str(m), "in": 0, "out": TE.media_dur(str(m)), "at": at} for m, at in ov]},
        {"kind": "audio", "name": "A1 Danışıq", "clips": [{"src": str(src), "in": s, "out": s + nf / 30, "at": at} for _, s, e, at, nf in parts]}],
        "markers": [{"t": 0, "name": "rəng: " + ("; ".join(why) or "baza")}]}
    TE.export(tl, W_ / "timeline"); tick("9_timeline")
    res = {"video": a.name, "qc": "KEÇDİ" if qc_ok else "KEÇMƏDİ", "qc_line": (qc.stdout.strip().splitlines() or [""])[-1][:400], "times": T,
           "total_s": round(sum(T.values()), 1), "out_dur": round(cur, 1), "final": str(final), "audio": rep["after"], "color": why}
    json.dump(res, open(W_ / "engine.json", "w"), ensure_ascii=False, indent=1); print(json.dumps(res, ensure_ascii=False)[:900])
    sys.exit(0 if qc_ok else 3)


if __name__ == "__main__":
    main()
