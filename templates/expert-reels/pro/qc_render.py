"""Render-dən SONRA yekun videonun keyfiyyət yoxlaması (hər pipeline üçün: PRO, talk, xüsusi skriptlər).

İstifadə:
  python3 qc_render.py <final.mp4> [--clean base.mp4] [--caption caption.txt] [--subs subs.json] [--out DIR]
    --clean   eyni zaman xəttində qrafikasız versiya (varsa): qrafika üzü örtürmü — piksel fərqi ilə dəqiq ölçülür
    --caption Instagram caption mətni (yazılış yoxlaması)
    --subs    altyazı sözləri [[s,e,söz],...] (yazılış + oxuma sürəti)
Çıxış: DIR/qc.json, DIR/qc_sheet.jpg (12 kadr — Claude MÜTLƏQ baxır), çıxış kodu 0 KEÇDİ / 3 KEÇMƏDİ.

Yoxlamalar (hamısı istifadəçinin real düzəlişlərindən):
  export   fayl açılır, 1080x1920, səs=görüntü uzunluğu
  black    qara kadr                                    FAIL
  freeze   ≥1.5 s donma (tam ekran kart deyilsə)        WARN
  loud     LUFS −18…−11, pik ≤ −1 dBFS, klik            FAIL
  frame    baş üstü boşluq / üz mərkəzi / üz ölçüsü     FAIL (kadrların 30%-dən çoxu norma xaricində)
  overlay  qrafika üzü örtür (--clean ilə)              FAIL
  color    üz parlaqlığı, sarılıq/göy çalar, doyma      FAIL
  text     məlum səhv yazılışlar (glossary_az.json), sürət > 17 simvol/san  WARN/FAIL
"""
import argparse, json, os, re, subprocess, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
A = Path(__file__).resolve().parent


def sh(a): return subprocess.run(a, capture_output=True, text=True)


def grab(path, t, w=360):
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(path), "-frames:v", "1", "-vf", f"scale={w}:-2", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    if not p.stdout: return None
    h = len(p.stdout) // (w * 3); return np.frombuffer(p.stdout[: w * h * 3], np.uint8).reshape(h, w, 3)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("mp4"); ap.add_argument("--clean"); ap.add_argument("--caption"); ap.add_argument("--subs"); ap.add_argument("--out")
    ap.add_argument("--full", default="", help="tam ekran kart aralıqları 'a-b,c-d' (üz yoxlanmır)")
    a = ap.parse_args(); mp4 = Path(a.mp4); out = Path(a.out) if a.out else mp4.parent / f"{mp4.stem}_QC"; out.mkdir(parents=True, exist_ok=True)
    R = {"fail": [], "warn": [], "info": {}}
    full = [tuple(map(float, x.split("-"))) for x in a.full.split(",") if x]
    in_full = lambda t: any(x <= t <= y for x, y in full)
    # export
    pr = json.loads(sh(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,duration:format=duration", "-of", "json", str(mp4)]).stdout or "{}")
    st = pr.get("streams", []); v = next((s for s in st if s["codec_type"] == "video"), None); au = next((s for s in st if s["codec_type"] == "audio"), None)
    if not v or not au: R["fail"].append({"export": "video və ya səs axını yoxdur"})
    else:
        dv, da = float(v.get("duration", 0)), float(au.get("duration", 0)); R["info"].update(w=v["width"], h=v["height"], dur=round(dv, 2))
        if (v["width"], v["height"]) != (1080, 1920): R["warn"].append({"export": f"ölçü {v['width']}x{v['height']}"})
        if abs(dv - da) > 0.12: R["fail"].append({"export": f"səs {da:.2f}s ≠ görüntü {dv:.2f}s"})
    dur = float(pr.get("format", {}).get("duration", 0))
    # black / freeze
    e = sh(["ffmpeg", "-v", "info", "-i", str(mp4), "-vf", "blackdetect=d=0.15:pix_th=0.06,freezedetect=n=0.002:d=1.5", "-an", "-f", "null", "-"]).stderr
    blacks = [round(float(x), 2) for x in re.findall(r"black_start:([0-9.]+)", e)]
    blacks = [b for b in blacks if not in_full(b)]
    if blacks: R["fail"].append({"black": blacks})
    fr = [round(float(x), 2) for x in re.findall(r"freeze_start: ([0-9.]+)", e)]
    fr = [f for f in fr if not in_full(f + 0.3)]
    if fr: R["warn"].append({"freeze": fr})
    # loud
    ln = sh(["ffmpeg", "-v", "info", "-i", str(mp4), "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    try:
        I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", ln)[-1]); pk = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", ln)[-1]); R["info"].update(lufs=I, peak=pk)
        if not (-18 <= I <= -11) or pk > -1.0: R["fail"].append({"loud": [I, pk]})
    except IndexError: R["fail"].append({"loud": "ölçülmədi"})
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-ac", "1", "-ar", "48000", "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    if len(x):  # klik = ətrafındakı siqnaldan 10 dəfə kəskin tək sıçrayış (yüksək səviyyəli «s» səsləri klik sayılmır)
        d = np.abs(np.diff(x)); k = np.convolve(d, np.ones(480) / 480, "same") + 1e-6
        ck = np.where((d > 0.25) & (d > 10 * k))[0]
        if len(ck) > 3: R["fail"].append({"click": (ck[:10] / 48000).round(2).tolist()})
        elif len(ck): R["warn"].append({"click": (ck / 48000).round(2).tolist()})
    # kadraj + üz örtülməsi
    import facedet
    ts = [t for t in np.arange(0.5, max(0.6, dur - 0.3), float(os.environ.get("QC_STEP", "2.0")))]  # hər 2 s (sürət); QC_STEP=1 dəqiq
    bad_frame, bad_overlay, n_face, n_chk = [], [], 0, 0
    for t in ts:
        if in_full(t): continue
        f = grab(mp4, t)
        if f is None: continue
        c = grab(a.clean, t) if a.clean else None
        if c is not None and c.shape != f.shape:  # clean kiçik ölçüdə render olunur
            from PIL import Image as _I; c = np.asarray(_I.fromarray(c).resize((f.shape[1], f.shape[0])))
        ref = c if c is not None else f
        fs = facedet.faces(ref)
        if not fs: continue
        n_chk += 1
        x0, y0, x1, y1, _ = fs[0]; fh = y1 - y0; cx = (x0 + x1) / 2
        # baş üstü: BlazeFace qutusu alından başlayır → başın üstü ≈ y0 − 0.35·fh
        head_top = y0 - 0.35 * fh
        # hədlər istifadəçi rəyindən kalibrlənib (noyabr 2026): baş üstü 0.37–0.41 = «yuxarıda çox boşluq» (rədd),
        # 0.25–0.33 = təsdiqlənmiş; üz hündürlüyü > 0.30 = «çox yaxın»
        if not (0.04 <= head_top <= 0.36) or not (0.25 <= cx <= 0.75) or not (0.07 <= fh <= 0.30):
            bad_frame.append({"t": round(t, 1), "head_top": round(head_top, 2), "cx": round(cx, 2), "face_h": round(fh, 2)})
        if c is not None:
            n_face += 1
            H, W_ = f.shape[:2]
            X0, Y0, X1, Y1 = int(max(0, x0 - 0.1 * (x1 - x0)) * W_), int(max(0, y0 - 0.25 * fh) * H), int(min(1, x1 + 0.1 * (x1 - x0)) * W_), int(min(1, y1 + 0.05 * fh) * H)
            d = np.abs(f[Y0:Y1, X0:X1].astype(np.int16) - c[Y0:Y1, X0:X1].astype(np.int16)).max(2)
            cov = float((d > 40).mean())
            if cov > 0.10: bad_overlay.append({"t": round(t, 1), "covered": round(cov, 2)})
    R["info"]["frames_checked"] = n_chk
    if n_chk and len(bad_frame) / n_chk > 0.30: R["fail"].append({"frame": bad_frame[:8], "share": round(len(bad_frame) / n_chk, 2)})
    elif bad_frame: R["warn"].append({"frame": bad_frame[:6]})
    if bad_overlay: R["fail"].append({"overlay_face": bad_overlay})
    if not a.clean: R["warn"].append({"overlay_face": "yoxlanmadı (--clean yoxdur) — qc_sheet.jpg-yə gözlə bax"})
    # rəng
    import color_auto
    cst, ciss = color_auto.verify(mp4); R["info"]["color"] = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in cst.items() if k in ("face_y", "sat", "neutral")}
    if ciss: R["fail"].append({"color": ciss})
    # mətn
    gl = json.load(open(A / "glossary_az.json")) if (A / "glossary_az.json").exists() else {}
    def spell(txt, where):
        hits = []
        for wrong, right in gl.items():
            if re.search(r"(?<![\wəğıöüşç])" + re.escape(wrong) + r"(?![\wəğıöüşç])", txt, re.I): hits.append(f"{wrong}→{right}")
        if hits: R["fail"].append({f"spell_{where}": hits})
    if a.caption: spell(open(a.caption).read(), "caption")
    if a.subs:
        W = json.load(open(a.subs)); spell(" ".join(w[2] for w in W), "subs")
        fast = [round(w[0], 1) for w in W if (w[1] - w[0]) > 0 and len(w[2]) / max(0.05, w[1] - w[0]) > 40]
        if len(fast) > 3: R["warn"].append({"subs_fast_words": fast[:10]})
    # kontakt vərəqi
    from PIL import Image
    pts = np.linspace(0.3, max(0.4, dur - 0.3), 12); fr_ = [grab(mp4, t, 240) for t in pts]; fr_ = [f for f in fr_ if f is not None]
    if fr_:
        h = fr_[0].shape[0]; S = Image.new("RGB", (240 * 6, h * 2), "white")
        for i, f in enumerate(fr_[:12]): S.paste(Image.fromarray(f), ((i % 6) * 240, (i // 6) * h))
        S.save(out / "qc_sheet.jpg", quality=85)
    json.dump(R, open(out / "qc.json", "w"), ensure_ascii=False, indent=1)
    ok = not R["fail"]
    print(("QC KEÇDİ" if ok else "QC KEÇMƏDİ") + f": {mp4.name} | " + json.dumps(R, ensure_ascii=False)[:1500])
    sys.exit(0 if ok else 3)


if __name__ == "__main__":
    main()
