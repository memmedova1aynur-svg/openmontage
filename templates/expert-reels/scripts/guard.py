#!/usr/bin/env python3
"""Check that no overlay box covers the speaker's head, face or hands.

Usage: guard.py <project-id> [--fix]   (--fix writes the caption moves into spec.json as caption_shift)

1. The cut (assets/video/cut.mp4) is sampled 4x a second; MediaPipe's pose landmarker gives
   the head (from eyes/ears/nose/mouth, hair included) and both hands (wrist + finger points).
   The full-frame zoom (up to ~1.1 around the face point) is folded in by growing the boxes.
2. Every overlay is rendered alone over a black picture (captions and cutaway scenes off) at
   the moment it has settled, which gives its exact on-screen box.
3. An overlay that touches a head/hand box at any sample inside its in/out window is reported
   with the overlap and the free room above the head at that moment.

Models: $MP_MODELS (default ~/.cache/mp) holds pose_landmarker_full.task
(https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task).
Prints JSON-ish lines; exit code 1 when anything collides.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
proj = ROOT / "projects" / sys.argv[1]
WS = proj / "remotion"
MODELS = Path(os.environ.get("MP_MODELS", Path.home() / ".cache/mp"))
FACE = (540, 0.36 * 1920)  # zoom origin (index.tsx FACE)
PAD = 24


def zoomed(box, s):
    x0, y0, x1, y1 = box
    f = lambda x, y: (FACE[0] + (x - FACE[0]) * s, FACE[1] + (y - FACE[1]) * s)
    a, b = f(x0, y0), f(x1, y1)
    return a[0], a[1], b[0], b[1]


def union(a, b):
    return min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])


# ---------------------------------------------------------------- 1. speaker landmarks
opts = mp.tasks.vision.PoseLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=str(MODELS / "pose_landmarker_full.task")),
    running_mode=mp.tasks.vision.RunningMode.VIDEO)
det = mp.tasks.vision.PoseLandmarker.create_from_options(opts)
cap = cv2.VideoCapture(str(proj / "assets/video/cut.mp4"))
fps = cap.get(cv2.CAP_PROP_FPS)
samples = []  # (t, [boxes], head_top)
i = 0
while True:
    ok, fr = cap.read()
    if not ok:
        break
    if i % max(1, round(fps / 4)) == 0:
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
        r = det.detect_for_video(img, int(i * 1000 / fps))
        boxes = []
        top = None
        if r.pose_landmarks:
            L = [(p.x * 1080, p.y * 1920) for p in r.pose_landmarks[0]]
            ex = [L[k][0] for k in (7, 8)]
            hw = max(abs(ex[0] - ex[1]), 2.2 * abs(L[2][0] - L[5][0]), 120)
            cx = sum(L[k][0] for k in range(11)) / 11
            eye_y = min(L[2][1], L[5][1])
            mouth_y = max(L[9][1], L[10][1])
            head = (cx - 0.75 * hw, eye_y - 1.1 * hw, cx + 0.75 * hw, mouth_y + 0.55 * hw)
            boxes.append(("head", head))
            top = head[1]
            for name, ids in (("hand_l", (15, 17, 19, 21)), ("hand_r", (16, 18, 20, 22))):
                xs = [L[k][0] for k in ids]
                ys = [L[k][1] for k in ids]
                r_ = 0.45 * hw
                hb = (min(xs) - r_, min(ys) - r_, max(xs) + r_, max(ys) + r_)
                if hb[1] < 1920:
                    boxes.append((name, hb))
        # the push-in zoom (1.0 .. ~1.1) can move every point outward from FACE
        fr = json.load(open(WS / "public/edit.json")).get("frame") or {"s": 1, "y": 0}
        boxes = [(n, tuple(v + (fr["y"] if k % 2 else fr.get("x", 0)) for k, v in enumerate(zoomed(b, fr["s"])))) for n, b in boxes]  # reframing
        boxes = [(n, union(zoomed(b, 1.0), zoomed(b, 1.1))) for n, b in boxes]
        if top is not None:
            top = FACE[1] + (top - FACE[1]) * fr["s"] + fr["y"]
        samples.append((i / fps, boxes, None if top is None else min(zoomed((0, top, 0, top), 1.0)[1], zoomed((0, top, 0, top), 1.1)[1])))
    i += 1

# ---------------------------------------------------------------- 2. overlay boxes
edit_p = WS / "public/edit.json"
edit = json.load(open(edit_p))
shutil.copy(edit_p, proj / "artifacts/edit_guard_backup.json")
black = WS / "public/black.mp4"
if not black.exists():
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=black:s=1080x1920:r=30:d={edit['videoDur']}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(black)], check=True)
browser = next(iter(sorted(Path("/opt/pw-browsers").glob("chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell"))), None)
results = []
bad = 0
try:
    for o in edit["overlays"]:
        solo = {**edit, "video": "black.mp4", "pages": [], "cutaways": [], "overlays": [o], "plate": None}
        if solo["style"].get("captions") == "plate":
            solo["style"] = {**solo["style"], "captions": "stroke"}
        json.dump(solo, open(edit_p, "w"), ensure_ascii=False)
        t = min(o["in"] + 0.7, (o["in"] + o["out"]) / 2)
        if o.get("strike") is not None:
            t = max(t, min(o["strike"] + 0.3, o["out"] - 0.1))
        frame = int(t * 30)
        png = proj / f"artifacts/guard_{o['id']}.png"
        cmd = ["npx", "remotion", "still", "src/index.tsx", "Reel", str(png), f"--frame={frame}", "--log=error"]
        if browser:
            cmd.append(f"--browser-executable={browser}")
        subprocess.run(cmd, cwd=WS, check=True)
        im = cv2.imread(str(png))
        m = im.max(axis=2) > 24
        ys, xs = np.nonzero(m)
        if not len(xs):
            continue
        ob = (xs.min() - PAD, ys.min() - PAD, xs.max() + PAD, ys.max() + PAD)
        hits = []
        for st, boxes, top in samples:
            if not (o["in"] <= st < o["out"]):
                continue
            for name, b in boxes:
                ix = min(ob[2], b[2]) - max(ob[0], b[0])
                iy = min(ob[3], b[3]) - max(ob[1], b[1])
                if ix > 0 and iy > 0:
                    hits.append((round(st, 2), name, int(ix * iy)))
        tops = [top for st, _, top in samples if o["in"] <= st < o["out"] and top is not None]
        res = {"id": o["id"], "box": [int(v) for v in ob], "head_top_min": int(min(tops)) if tops else None,
               "hits": len(hits), "parts": sorted({h[1] for h in hits}), "worst": max(hits, key=lambda h: h[2]) if hits else None}
        bad += bool(hits)
        results.append(res)
        print(json.dumps(res, ensure_ascii=False), flush=True)
    # captions: the longest page alone over black gives the caption band (height, width per character)
    scenes = [(c["in"], c["out"]) for c in edit["cutaways"] if c["kind"] in ("scene", "split", "full")]
    pages = [p for p in edit["pages"] if not any(a <= p["start"] < b for a, b in scenes)]
    band = None
    if pages:
        longest = max(pages, key=lambda p: len(" ".join(w["w"] for w in p["words"])))
        solo = {**edit, "video": "black.mp4", "overlays": [], "cutaways": [], "captionShift": [], "pages": [longest]}
        json.dump(solo, open(edit_p, "w"), ensure_ascii=False)
        png = proj / "artifacts/guard_caption.png"
        cmd = ["npx", "remotion", "still", "src/index.tsx", "Reel", str(png), f"--frame={int((longest['end'] - 0.05) * 30)}", "--log=error"]
        if browser:
            cmd.append(f"--browser-executable={browser}")
        subprocess.run(cmd, cwd=WS, check=True)
        m = cv2.imread(str(png)).max(axis=2) > 24
        ys, xs = np.nonzero(m)
        if len(xs):
            chars = len(" ".join(w["w"] for w in longest["words"]))
            band = {"y0": int(ys.min()) - PAD, "y1": int(ys.max()) + PAD, "w_max": int(xs.max() - xs.min()), "per_char": (xs.max() - xs.min()) / max(1, chars)}
finally:
    shutil.copy(proj / "artifacts/edit_guard_backup.json", edit_p)

shift = []
residual = []  # caption pages that still touch a hand wherever they go
if band:
    head_bottom = lambda sts: max([b[3] for st in sts for n, b in st[1] if n == "head"], default=0)
    ok = []  # per page: (page, {(dy, dx): overlap with the hands/head})
    for p in pages:
        sts = [st for st in samples if p["start"] - 0.1 <= st[0] < p["end"] + 0.1]
        w = min(band["w_max"], band["per_char"] * len(" ".join(x["w"] for x in p["words"]))) + 2 * PAD
        lo = head_bottom(sts)
        # down at most to a band bottom of 1660 (Instagram's own caption text sits lower); up while it stays under
        # the chin; sideways (only when up/down cannot clear it) while the text stays inside the frame
        # CAP_UP=N: captions may rise at most N px (keeps them low on the body when the user asks for that)
        dys = [d for d in range(-int(os.environ.get("CAP_UP", 1200)), 1661 - band["y1"], 20) if band["y0"] + d > lo + 10]
        dxs = [d for d in range(-300, 301, 40) if 540 - w / 2 + d >= 20 and 540 + w / 2 + d <= 1060]

        def cover(dy, dx):  # overlap area summed over the samples
            x0, x1, y0, y1 = 540 - w / 2 + dx, 540 + w / 2 + dx, band["y0"] + dy, band["y1"] + dy
            return sum(max(0, min(x1, b[2]) - max(x0, b[0])) * max(0, min(y1, b[3]) - max(y0, b[1])) for st in sts for n, b in st[1])

        costs = {(dy, dx): cover(dy, dx) for dy in dys for dx in dxs}
        ok.append((p, costs))
    # Per page the spot with the least overlap, but every change of spot costs MOVE (so captions do not
    # hop): a Viterbi pass over the pages. Being off-centre / away from the usual line costs a little too.
    MOVE, N = 60000, len(ok)
    if N:
        keys = sorted(set().union(*[set(c) for _, c in ok]))
        INF = float("inf")
        place = lambda k: 4 * abs(k[1]) + 2 * abs(k[0])
        dp = [{k: ok[0][1].get(k, INF) + place(k) for k in keys}]
        back = [{}]
        for i in range(1, N):
            free = ok[i][0]["start"] - ok[i - 1][0]["end"] > 1.0  # after a scene or a long gap a new spot is free
            pk = min(dp[-1], key=dp[-1].get)
            cur, bk = {}, {}
            for k in keys:
                stay, jump = dp[-1][k], dp[-1][pk] + (0 if free else MOVE)
                cur[k] = ok[i][1].get(k, INF) + place(k) + min(stay, jump)
                bk[k] = k if stay <= jump else pk
            dp.append(cur)
            back.append(bk)
        k = min(dp[-1], key=dp[-1].get)
        path = [k]
        for i in range(N - 1, 0, -1):
            k = back[i][k]
            path.append(k)
        path.reverse()
        for (p, c), (dy, dx) in zip(ok, path):
            if c[(dy, dx)] > 0:
                residual.append(round(p["start"], 2))
            if (dy, dx) == (0, 0):
                continue
            if shift and shift[-1][2:] == [dy, dx] and p["start"] - shift[-1][1] < 1.0:
                shift[-1][1] = round(p["end"], 2)
            else:
                shift.append([round(p["start"], 2), round(p["end"], 2), dy, dx])
    base = 0
    print("caption band", {k: round(float(v), 1) for k, v in band.items()}, "base dy", base, "shifts:", json.dumps(shift))
    if residual:
        print(f"WARN: {len(residual)} caption page(s) still touch a hand at their best spot: {residual}")
if "--fix" in sys.argv:
    spec_p = proj / "spec.json"
    spec = json.load(open(spec_p))
    spec["caption_shift"] = shift
    json.dump(spec, open(spec_p, "w"), ensure_ascii=False, indent=1)
    print("caption_shift written to spec.json")
json.dump({"samples": [(t, b, top) for t, b, top in samples], "overlays": results, "captionShift": shift}, open(proj / "artifacts/guard.json", "w"))
print(f"{bad} overlay(s)/caption(s) touch the head/hands" if bad else "clear: no overlay touches the head or hands")
sys.exit(1 if bad else 0)
