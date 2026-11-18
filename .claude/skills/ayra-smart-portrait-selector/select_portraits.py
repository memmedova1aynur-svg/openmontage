#!/usr/bin/env python3
"""Videodan cover üçün portret namizədləri seçir (MediaPipe Face Landmarker, yerli, API-siz).
  select_portraits.py <video> <çıxış_qovluğu> [--n 80] [--top 12] [--exclude 2.0,15.6] [--start 0 --end 0]
Çıxış: candidates.json (bütün ballar), top/<t>.png (tam kadrlar), contact_sheet.jpg (ən yaxşı 12, etiketli).
Ballar: gözlər açıq, ağız bağlı/yüngül təbəssüm, baş düz (yaw/pitch), baxış kameraya, fokus, işıq, üz ölçüsü.
Son seçimi İNSAN GÖZÜ ilə et: contact sheet-ə bax (Read)."""
import argparse, json, math, os, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
MODEL = "/root/montaj-data/models/face_landmarker.task"

def frame_at(video, t):
    out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    return cv2.cvtColor(cv2.imdecode(np.frombuffer(out, np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB) if out else None

def euler(m):
    r = np.array(m)[:3, :3]
    pitch = math.degrees(math.atan2(-r[1, 2], r[2, 2])); yaw = math.degrees(math.asin(max(-1, min(1, r[0, 2])))); roll = math.degrees(math.atan2(-r[0, 1], r[0, 0]))
    return yaw, pitch, roll

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("out")
    ap.add_argument("--n", type=int, default=0); ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--exclude", default=""); ap.add_argument("--start", type=float, default=0); ap.add_argument("--end", type=float, default=0)
    a = ap.parse_args(); os.makedirs(a.out + "/top", exist_ok=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.video], capture_output=True, text=True).stdout)
    end = a.end or dur - 0.3; n = a.n or int(min(100, max(30, (end - a.start) * 0.7)))
    excl = [float(x) for x in a.exclude.split(",") if x]
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision
    det = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(base_options=BaseOptions(model_asset_path=MODEL),
          output_face_blendshapes=True, output_facial_transformation_matrixes=True, num_faces=1))
    rows = []
    for t in np.linspace(a.start + 0.3, end, n):
        if any(abs(t - e) < 1.0 for e in excl): continue
        rgb = frame_at(a.video, t)
        if rgb is None: continue
        h, w = rgb.shape[:2]; r = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb)))
        if not r.face_landmarks: continue
        bs = {b.category_name: b.score for b in r.face_blendshapes[0]}
        yaw, pitch, roll = euler(r.facial_transformation_matrixes[0])
        pts = np.array([(p.x * w, p.y * h) for p in r.face_landmarks[0]]); x0, y0 = pts.min(0); x1, y1 = pts.max(0)
        face = cv2.cvtColor(rgb[int(max(0, y0)):int(y1), int(max(0, x0)):int(x1)], cv2.COLOR_RGB2GRAY)
        sharp = float(cv2.Laplacian(face, cv2.CV_64F).var()); lum = float(face.mean() / 255)
        blink = (bs["eyeBlinkLeft"] + bs["eyeBlinkRight"]) / 2; jaw = bs["jawOpen"]; smile = (bs["mouthSmileLeft"] + bs["mouthSmileRight"]) / 2
        pucker = max(bs.get("mouthPucker", 0), bs.get("mouthFunnel", 0))
        gaze = max(bs["eyeLookDownLeft"], bs["eyeLookDownRight"], bs["eyeLookOutLeft"], bs["eyeLookOutRight"], bs["eyeLookUpLeft"], bs["eyeLookUpRight"])
        brow = max(bs.get("browDownLeft", 0), bs.get("browDownRight", 0), bs.get("browInnerUp", 0))
        s = {"eyes": 1 - min(1, blink / 0.45), "mouth": 1 - min(1, max(0, jaw - 0.05) / 0.3) - 0.6 * min(1, pucker / 0.4),
             "smile": min(1, smile / 0.35), "pose": 1 - min(1, (abs(yaw) + abs(pitch) * 0.8 + abs(roll) * 0.5) / 25),
             "gaze": 1 - min(1, max(0, gaze - 0.25) / 0.4), "calm": 1 - min(1, max(0, brow - 0.35) / 0.4),
             "sharp": min(1, sharp / 250), "light": 1 - min(1, abs(lum - 0.55) / 0.3)}
        W = {"eyes": 3, "mouth": 3, "smile": 1.2, "pose": 2, "gaze": 2, "calm": 1, "sharp": 1.5, "light": 0.8}
        score = sum(W[k] * v for k, v in s.items()) / sum(W.values())
        if blink > 0.5 or jaw > 0.45: score *= 0.4   # sərt filtr
        rows.append({"t": round(float(t), 2), "score": round(score, 3), **{k: round(v, 2) for k, v in s.items()},
                     "blink": round(blink, 2), "jaw": round(jaw, 2), "smileRaw": round(smile, 2), "yaw": round(yaw, 1), "pitch": round(pitch, 1),
                     "sharpRaw": round(sharp), "face": [int(x0), int(y0), int(x1), int(y1)]})
    rows.sort(key=lambda r: -r["score"]); pick = []
    for r in rows:   # oxşarları at: 1.5 s-dən yaxın olanlar
        if all(abs(r["t"] - p["t"]) > 1.5 for p in pick): pick.append(r)
        if len(pick) == a.top: break
    json.dump({"video": a.video, "sampled": n, "faces": len(rows), "ranked": rows, "top": pick}, open(a.out + "/candidates.json", "w"), indent=1)
    cw, ch = 300, 400; S = Image.new("RGB", (4 * cw, ((len(pick) + 3) // 4) * (ch + 60)), "white"); d = ImageDraw.Draw(S)
    for i, r in enumerate(pick):
        rgb = frame_at(a.video, r["t"]); Image.fromarray(rgb).save(f"{a.out}/top/{r['t']:.2f}.png")
        x0, y0, x1, y1 = r["face"]; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; fh = (y1 - y0) * 2.6
        box = (int(cx - fh * .375), int(cy - fh * .42), int(cx + fh * .375), int(cy + fh * .58))
        tile = Image.fromarray(rgb).crop(box).resize((cw - 6, ch - 6)); x, y = (i % 4) * cw, (i // 4) * (ch + 60)
        S.paste(tile, (x + 3, y + 3)); d.text((x + 6, y + ch + 2), f"#{i+1} t={r['t']}s  bal={r['score']}", fill="black")
        d.text((x + 6, y + ch + 20), f"göz {r['eyes']} ağız {r['mouth']} təbəs {r['smile']} poz {r['pose']} fokus {r['sharp']}", fill=(90, 90, 90))
    S.save(a.out + "/contact_sheet.jpg", quality=90)
    print(f"{n} kadr, {len(rows)} üz, top {len(pick)} → {a.out}/contact_sheet.jpg")

main()
