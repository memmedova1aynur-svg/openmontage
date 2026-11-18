"""Hər video üçün ayrıca rəng analizi → ölçülü korreksiya (preset kor-koranə yox).

Ölçür (üz bölgəsi + bütün kadr, 8 nümunə kadr, HDR → SDR çevrildikdən sonra):
  üz parlaqlığı, kontrast diapazonu (p2/p98), ağ balansı (dəri olmayan neytral piksellər),
  dəri tonu (sarılıq), doyma, kəskinlik.
Çıxış: montaj.render.color_filters lüğəti ("look") + hazır ffmpeg filtr sətri ("vf") + yoxlama.

İstifadə:
  python3 color_auto.py <video> [--json out.json] [--sheet before_after.jpg]
  python3 color_auto.py --verify <hazır.mp4>      # renderdən sonra: dəri/ağ balansı/doyma normadadırmı
Qaydalar (istifadəqi rəyi): sarılıq yox, həddən artıq parlaq yox, plastik/smoothing yox, üz teksturası qorunur.
"""
import argparse, json, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import numpy as np

HDR_TRC = {"arib-std-b67": "arib-std-b67", "smpte2084": "smpte2084"}


def probe(path):
    o = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=color_transfer,color_primaries,width,height:format=duration", "-of", "json", str(path)],
                                  capture_output=True, text=True).stdout)
    s = o["streams"][0]; return s.get("color_transfer", ""), float(o["format"]["duration"])


def sdr_chain(trc):
    if trc in HDR_TRC:  # iPhone HLG / Dolby Vision (PQ) → BT.709; tin açıq verilir ki, metadata yoxdursa da düz çevrilsin
        return (f"zscale=tin={HDR_TRC[trc]}:t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,"
                "tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
    return ""


def frames(path, vf, n=8, w=360):
    _, dur = probe(path); out = []
    for k in range(n):
        t = dur * (k + 0.5) / n
        chain = ",".join(x for x in [vf, f"scale={w}:-2", "format=rgb24"] if x)
        p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(path), "-frames:v", "1", "-vf", chain,
                            "-f", "rawvideo", "-"], capture_output=True)
        if not p.stdout: continue
        h = len(p.stdout) // (w * 3); out.append(np.frombuffer(p.stdout[: w * h * 3], np.uint8).reshape(h, w, 3).astype(np.float32) / 255)
    return out


def face_box(img):
    import facedet
    f = facedet.faces(img)
    if not f: return None
    h, w = img.shape[:2]; x0, y0, x1, y1, _ = f[0]
    return int(x0 * w), int(y0 * h), int((x1 - x0) * w), int((y1 - y0) * h)


def stats(imgs):
    Y, P2, P98, SAT, SKIN, NEU, SH = [], [], [], [], [], [], []
    for im in imgs:
        y = im @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        P2.append(np.percentile(y, 2)); P98.append(np.percentile(y, 98))
        mx, mn = im.max(2), im.min(2); sat = (mx - mn) / (mx + 1e-4); SAT.append(float(np.median(sat)))
        fb = face_box(im); mask = np.zeros(y.shape, bool)
        if fb:
            x, yy, w, h = fb; cx0, cy0 = x + w // 4, yy + h // 4
            sk = im[cy0:cy0 + h // 2, cx0:cx0 + w // 2].reshape(-1, 3); SKIN.append(sk.mean(0)); Y.append(float((sk @ np.array([0.2126, 0.7152, 0.0722])).mean()))
            mask[yy:yy + h, x:x + w] = True
        neutral = (~mask) & (sat < 0.12) & (y > 0.15) & (y < 0.9)
        if neutral.sum() > 200: NEU.append(im[neutral].mean(0))
        import cv2
        SH.append(float(cv2.Laplacian((y * 255).astype(np.uint8), cv2.CV_64F).var()))
    r = dict(p2=float(np.median(P2)), p98=float(np.median(P98)), sat=float(np.median(SAT)), sharp=float(np.median(SH)))
    r["face_y"] = float(np.median(Y)) if Y else None
    r["skin"] = np.median(SKIN, 0).round(3).tolist() if SKIN else None
    r["neutral"] = np.median(NEU, 0).round(3).tolist() if NEU else None
    return r


def decide(st):
    """Ölçülərdən ölçülü düzəliş. Hər dəyər məhdudlaşdırılıb — "süni" görünüş olmasın."""
    # baza "premium" qat: yüngül dərinlik + canlılıq (istifadəçi: rəng korreksiyası HƏR videoda hiss olunmalıdır)
    look = {"contrast": 1.04, "brightness": 0.0, "saturation": 1.0, "vibrance": 0.08, "gamma": 1.0, "sharpen": 0.0, "highlights": 0.0, "shadows": 0.0, "depth": 0.6}
    why = []
    fy = st["face_y"] if st["face_y"] is not None else (st["p2"] + st["p98"]) / 2
    if fy < 0.42: look["gamma"] = round(min(1.18, 1 + (0.50 - fy) * 0.9), 3); why.append(f"üz qaranlıq ({fy:.2f}) → gamma {look['gamma']}")
    elif fy > 0.68: look["gamma"] = round(max(0.88, 1 - (fy - 0.62) * 0.8), 3); look["highlights"] = 0.5; why.append(f"üz çox işıqlı ({fy:.2f}) → gamma {look['gamma']}")
    spread = st["p98"] - st["p2"]
    if spread < 0.70: look["contrast"] = round(min(1.10, 1 + (0.80 - spread) * 0.35), 3); why.append(f"solğun (diapazon {spread:.2f}) → kontrast {look['contrast']}")
    elif spread > 0.92: look["shadows"] = 0.3; look["highlights"] = max(look["highlights"], 0.4); why.append("kontrast yüksək → kölgə/işıq yumşaldılır")
    if st["p98"] > 0.97: look["highlights"] = max(look["highlights"], 0.6); why.append("işıqlı yerlər yanır → highlights")
    if st["sat"] < 0.16: look["vibrance"] = 0.16; why.append(f"doyma az ({st['sat']:.2f}) → vibrance 0.16")
    elif st["sat"] < 0.24: look["vibrance"] = 0.11
    elif st["sat"] > 0.40: look["saturation"] = 0.93; look["vibrance"] = 0; why.append("doyma çox → saturation 0.93")
    # ağ balansı: neytral piksellərin R−B fərqi → rəng temperaturu (±700 K ilə məhdud)
    mix = None; cast = 0.0
    if st["neutral"]:
        r, g, b = st["neutral"]; cast = (r - b) / max(1e-3, (r + g + b) / 3)
        if abs(cast) > 0.035:
            gr, gg, gb = [round(float(np.clip(((r + g + b) / 3) / max(1e-3, c), 0.94, 1.06)), 3) for c in (r, g, b)]
            mix = (gr, gg, gb); why.append(f"ağ balansı {'isti/sarı' if cast > 0 else 'soyuq/göy'} ({cast:+.3f}) → kanal düzəlişi {mix}")
    if st["skin"]:
        r, g, b = st["skin"]
        if (r - b) / max(1e-3, r) > 0.42 and (g - b) / max(1e-3, g) > 0.33: why.append("dəri sarımtıl — ağ balansı ilə yumşaldılır")
    if st["sharp"] < 60: look["sharpen"] = 0.35; why.append("yumşaq kadr → yüngül kəskinlik 0.35")
    elif st["sharp"] < 160: look["sharpen"] = 0.22
    else: look["sharpen"] = 0.12
    look = {k: v for k, v in look.items() if (k in ("contrast", "saturation", "gamma") and abs(v - 1) > 1e-3) or (k not in ("contrast", "saturation", "gamma") and v)}
    return look, mix, why


def to_vf(look, mix, trc):
    f = [sdr_chain(trc)] if sdr_chain(trc) else []
    if mix: f.append(f"colorchannelmixer=rr={mix[0]}:gg={mix[1]}:bb={mix[2]}")
    eq = []
    for k, d in (("contrast", 1), ("brightness", 0), ("saturation", 1), ("gamma", 1)):
        if k in look: eq.append(f"{k}={look[k]}")
    if eq: f.append("eq=" + ":".join(eq))
    if look.get("highlights"): hl = look["highlights"]; f.append(f"curves=master='0/0 0.6/0.6 0.85/{0.85 - 0.03 * hl:.4f} 1/{1 - 0.07 * hl:.4f}'")
    if look.get("shadows"): sh = look["shadows"]; f.append(f"curves=master='0/0 0.12/{0.12 + 0.07 * sh:.4f} 0.35/{0.35 + 0.08 * sh:.4f} 1/1'")
    if look.get("depth"): d = min(look["depth"], 2); f.append(f"curves=master='0/0 0.05/{0.05 - 0.015 * d:.4f} 0.95/{0.95 + 0.015 * d:.4f} 1/1'")
    if look.get("vibrance"): f.append(f"vibrance=intensity={look['vibrance']}")
    if look.get("sharpen"): f.append(f"unsharp=5:5:{look['sharpen']}:5:5:0")  # yalnız parlaqlıq — üz teksturası, smoothing yox
    return ",".join(f)


def verify(path):
    """Renderdən sonra: yekun kadrlar normadadırmı (QA çağırır)."""
    st = stats(frames(path, "")); issues = []
    if st["face_y"] is not None and not (0.38 <= st["face_y"] <= 0.74): issues.append(f"üz parlaqlığı {st['face_y']:.2f} (norma 0.38–0.74)")
    if st["neutral"]:
        r, g, b = st["neutral"]; cast = (r - b) / max(1e-3, (r + g + b) / 3)
        if abs(cast) > 0.09: issues.append(f"rəng çalarlığı {'sarı' if cast > 0 else 'göy'} {cast:+.3f}")
    if st["sat"] > 0.48: issues.append(f"həddən artıq doyma {st['sat']:.2f}")
    if st["p98"] - st["p2"] < 0.55: issues.append("solğun/boz görüntü")
    return st, issues


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("--json"); ap.add_argument("--sheet"); ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.verify:
        st, iss = verify(a.video); print(json.dumps({"stats": st, "issues": iss}, ensure_ascii=False)); sys.exit(1 if iss else 0)
    trc, _ = probe(a.video); base = sdr_chain(trc)
    st = stats(frames(a.video, base)); look, mix, why = decide(st); vf = to_vf(look, mix, trc)
    res = {"hdr": trc if trc in HDR_TRC else None, "stats": st, "look": look, "mix": mix, "vf": vf, "why": why}
    after = stats(frames(a.video, vf)); res["after"] = {k: after[k] for k in ("face_y", "sat", "p2", "p98", "neutral")}
    if a.json: json.dump(res, open(a.json, "w"), ensure_ascii=False, indent=1)
    if a.sheet:
        from PIL import Image
        b = frames(a.video, base, 3, 300); c = frames(a.video, vf, 3, 300)
        h = b[0].shape[0]; S = Image.new("RGB", (300 * 3, h * 2))
        for i in range(3):
            S.paste(Image.fromarray((b[i] * 255).astype(np.uint8)), (i * 300, 0)); S.paste(Image.fromarray((c[i] * 255).astype(np.uint8)), (i * 300, h))
        S.save(a.sheet, quality=88)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
