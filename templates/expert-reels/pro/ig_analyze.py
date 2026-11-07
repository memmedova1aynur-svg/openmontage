"""Instagram linkindən səhifə analizi (giriş/parol/cookie YOX): Apify Instagram Scraper → media → transkript/OCR → icmal.

Addımlar:
  python3 ig_analyze.py fetch  https://www.instagram.com/<hesab>/ [--limit 30] [--max-usd 0.25]
  python3 ig_analyze.py media  <hesab> [--stt-min 10]       # Reels: transkript; şəkil/karusel: OCR
  python3 ig_analyze.py digest <hesab>                      # Claude-un oxuyacağı icmal (digest.md) + üz qabığı vərəqi
  python3 ig_analyze.py status <hesab>

Qaydalar:
- Yalnız açıq profil. Instagram parolu, cookie və ya hesab girişi istifadə olunmur; məlumatı Apify-ın açıq-profil skreperi toplayır.
- Keş: instagram-clients/_analysis/<hesab>/posts.json. Növbəti fetch yalnız ən son məlum tarixdən yeni paylaşımları götürür.
- Limit: ilk dəfə --limit (default 30, maks 50) nəticə və --max-usd (default $0.25) xərc tavanı (Apify maxTotalChargeUsd).
- Apify açarı: mühitin "network secret"-i (host api.apify.com) və ya APIFY_TOKEN mühit dəyişəni. Söhbətə yazılmır.
- Hər paylaşımda məlumat mənbəyi qeyd olunur: caption | transkript (scribe/whisper) | ocr. Əlçatan olmayan media "yalnız caption" kimi işarələnir.
"""
import json, os, re, sys, subprocess, time, hashlib, datetime
from pathlib import Path
A = Path(__file__).resolve().parent; sys.path.insert(0, str(A))
import avkit as K

ROOT = Path(os.environ.get("IG_ANALYSIS_DIR", str(A.parents[2] / "instagram-clients" / "_analysis")))
ACTOR = "apify~instagram-scraper"
arg = lambda name, d=None: (sys.argv[sys.argv.index(name) + 1] if name in sys.argv else d)


def handle_of(x):
    m = re.search(r"instagram\.com/([A-Za-z0-9_.]+)", x)
    h = (m.group(1) if m else x).strip("/@ ").lower()
    if h in ("p", "reel", "reels", "stories", "explore"): raise SystemExit("Profil linki lazımdır (instagram.com/<hesab>/), paylaşım linki yox.")
    return h


def load(h):
    d = ROOT / h; d.mkdir(parents=True, exist_ok=True); f = d / "posts.json"
    return d, (json.load(open(f)) if f.exists() else {"handle": h, "posts": {}, "runs": []})


def save(d, st): json.dump(st, open(d / "posts.json", "w"), ensure_ascii=False, indent=1)


def norm_post(it):
    """Apify elementindən lazım olan sahələr (adlar actor çıxışına görə; olmayan sahə None qalır)."""
    t = it.get("type") or ""
    kind = "reel" if (t == "Video" or it.get("productType") == "clips" or it.get("videoUrl")) else ("karusel" if t == "Sidecar" else "şəkil")
    imgs = [c.get("displayUrl") for c in (it.get("childPosts") or []) if c.get("displayUrl")] or list(it.get("images") or []) or ([it["displayUrl"]] if it.get("displayUrl") else [])
    return {"url": it.get("url") or (f"https://www.instagram.com/p/{it.get('shortCode')}/" if it.get("shortCode") else None),
            "shortCode": it.get("shortCode"), "tarix": it.get("timestamp"), "format": kind, "caption": it.get("caption") or "",
            "hashtags": it.get("hashtags") or [], "likes": it.get("likesCount"), "comments": it.get("commentsCount"),
            "views": it.get("videoViewCount") or it.get("videoPlayCount"), "videoUrl": it.get("videoUrl"), "images": imgs,
            "pinned": it.get("isPinned"), "mənbə": ["caption"] if it.get("caption") else []}


def cmd_fetch():
    url = sys.argv[2]; h = handle_of(url); d, st = load(h)
    limit = min(int(arg("--limit", 30)), 50); max_usd = float(arg("--max-usd", 0.25))
    newest = max((p["tarix"] for p in st["posts"].values() if p.get("tarix")), default=None)
    inp = {"directUrls": [f"https://www.instagram.com/{h}/"], "resultsType": "posts", "resultsLimit": limit, "addParentData": False}
    if newest: inp["onlyPostsNewerThan"] = newest[:10]  # yalnız yenilər (gün dəqiqliyi; təkrarlar shortCode ilə atılır)
    q = f"maxItems={limit}&maxTotalChargeUsd={max_usd}&timeout=240"
    hdr = ["-H", "Content-Type: application/json"]
    if os.environ.get("APIFY_TOKEN"): hdr += ["-H", f"Authorization: Bearer {os.environ['APIFY_TOKEN']}"]
    t0 = time.time()
    r = subprocess.run(["curl", "-sS", "-X", "POST", f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items?{q}", *hdr, "-d", json.dumps(inp)],
                       capture_output=True, text=True, timeout=300)
    try: items = json.loads(r.stdout)
    except Exception: raise SystemExit(f"Apify cavabı oxunmadı: {r.stdout[:300]} {r.stderr[:200]}")
    if isinstance(items, dict): raise SystemExit(f"Apify xətası: {json.dumps(items)[:400]}")
    new = 0
    for it in items:
        if it.get("error"): continue
        p = norm_post(it); k = p["shortCode"] or hashlib.md5(json.dumps(it, sort_keys=True).encode()).hexdigest()[:10]
        if k in st["posts"]: continue
        st["posts"][k] = p; new += 1
    st["runs"].append({"vaxt": datetime.datetime.now().isoformat(timespec="seconds"), "nəticə": len(items), "yeni": new, "limit": limit,
                       "max_usd": max_usd, "yalnız_yenilər": bool(newest), "san": round(time.time() - t0, 1)})
    save(d, st); print(f"{h}: {len(items)} nəticə, {new} yeni paylaşım, keşdə cəmi {len(st['posts'])}. Fayl: {d / 'posts.json'}")


def dl(url, out):
    if not url: return False
    if url.startswith("/") or url.startswith("file://"):
        src = url.replace("file://", ""); subprocess.run(["cp", src, str(out)]); return out.exists()
    r = subprocess.run(["curl", "-sSL", "--max-time", "120", "-o", str(out), "-w", "%{http_code}", url], capture_output=True, text=True)
    return r.stdout.strip() == "200" and out.exists() and out.stat().st_size > 1000


def ocr(img):
    """2 keçid (adi + böyüdülmüş/çevrilmiş), sətirləri birləşdir. Nəticə 'yoxlanmalı' sayılır."""
    tmp = Path(str(img) + ".inv.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(img), "-vf", "scale=iw*2:-1,format=gray,negate", str(tmp)])
    lines = []
    for f in (img, tmp):
        t = subprocess.run(["tesseract", str(f), "-", "-l", "aze+eng", "--psm", "3"], capture_output=True, text=True).stdout
        for ln in t.splitlines():
            ln = ln.strip()
            if len(re.sub(r"[^\wəğıöüşçƏĞİÖÜŞÇ]", "", ln)) >= 3 and ln not in lines: lines.append(ln)
    tmp.unlink(missing_ok=True); return "\n".join(lines)


def stt(media):
    """Əvvəl ElevenLabs Scribe (aze), alınmasa lokal whisper (zəif keyfiyyət işarəsi ilə)."""
    wav = Path(str(media) + ".wav"); K.run(["ffmpeg", "-v", "error", "-y", "-i", str(media), "-vn", "-ac", "1", "-ar", "16000", str(wav)])
    dur = K.probe_dur(wav)
    if os.environ.get("ELEVENLABS_API_KEY") and "--no-scribe" not in sys.argv:
        r = subprocess.run(["curl", "-sS", "-X", "POST", "https://api.elevenlabs.io/v1/speech-to-text", "-H", f"xi-api-key: {os.environ['ELEVENLABS_API_KEY']}",
                            "-F", "model_id=scribe_v1", "-F", "language_code=aze", "-F", f"file=@{wav}"], capture_output=True, text=True).stdout
        try:
            d = json.loads(r)
            if d.get("text"): return d["text"], "transkript (scribe)", dur
        except Exception: pass
    import numpy as np
    from faster_whisper import WhisperModel
    pcm = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout, np.float32)
    segs, _ = WhisperModel("small", compute_type="int8").transcribe(pcm, language="az")
    return " ".join(s.text.strip() for s in segs), "transkript (whisper, zəif keyfiyyət)", dur


def cmd_media():
    h = handle_of(sys.argv[2]); d, st = load(h); md = d / "media"; md.mkdir(exist_ok=True)
    budget = float(arg("--stt-min", 10)) * 60; used = 0.0
    for k, p in sorted(st["posts"].items(), key=lambda kv: kv[1].get("tarix") or "", reverse=True):
        if p.get("media_done"): continue  # əvvəl emal olunubsa təkrarlanmır
        notes = []
        if p["format"] == "reel":
            f = md / f"{k}.mp4"
            if used >= budget: notes.append("transkript büdcəsi bitdi")
            elif dl(p.get("videoUrl"), f):
                txt, src, dur = stt(f); used += dur
                if txt.strip(): p["transkript"] = txt; p["mənbə"].append(src)
                else: notes.append("danışıq tapılmadı")
            else: notes.append("video yüklənmədi (link vaxtı bitmiş ola bilər)")
        imgs = p.get("images") or []
        texts = []
        for j, u in enumerate(imgs[:10]):
            f = md / f"{k}_{j + 1}.jpg"
            if dl(u, f):
                t = ocr(f)
                if t: texts.append(f"[{j + 1}] {t}")
            else: notes.append(f"şəkil {j + 1} yüklənmədi")
        if texts: p["ocr"] = "\n".join(texts); p["mənbə"].append("ocr (yoxlanmalı)")
        if not set(p["mənbə"]) - {"caption"}: p["mənbə_qeyd"] = "YALNIZ CAPTION oxunub"
        p["qeyd"] = notes; p["media_done"] = True
        save(d, st); print(f"{k} {p['format']}: {', '.join(p['mənbə']) or '—'} {'; '.join(notes)}")
    print(f"transkript: {used / 60:.1f} dəq istifadə olundu (büdcə {budget / 60:.0f} dəq)")


def cmd_digest():
    h = handle_of(sys.argv[2]); d, st = load(h); n = int(arg("--last", 30))
    posts = sorted(st["posts"].items(), key=lambda kv: kv[1].get("tarix") or "", reverse=True)[:n]
    out = [f"# @{h}: son {len(posts)} paylaşım (icmal)", "", f"Toplanma: {st['runs'][-1]['vaxt'] if st['runs'] else '—'} · Mənbələr: caption / transkript / OCR (OCR yoxlanmalıdır)", ""]
    for i, (k, p) in enumerate(posts, 1):
        m = " · ".join(x for x in [p["format"], (p.get("tarix") or "")[:10], f"♥{p['likes']}" if p.get("likes") is not None else "",
                                   f"💬{p['comments']}" if p.get("comments") is not None else "", f"▶{p['views']}" if p.get("views") else ""] if x)
        out += [f"## {i}. {p['url']}", f"{m} · mənbə: {', '.join(p['mənbə']) or '—'}{' · ' + p['mənbə_qeyd'] if p.get('mənbə_qeyd') else ''}",
                f"**Caption:** {p['caption'][:1200] or '—'}"]
        if p.get("transkript"): out.append(f"**Transkript:** {p['transkript'][:1500]}")
        if p.get("ocr"): out.append(f"**Şəkil mətni (OCR):** {p['ocr'][:1500]}")
        if p.get("qeyd"): out.append(f"_Qeyd: {'; '.join(p['qeyd'])}_")
        out.append("")
    (d / "digest.md").write_text("\n".join(out))
    # üz qabığı vərəqi (vizual yoxlama üçün)
    from PIL import Image, ImageDraw, ImageFont
    th = [(i, d / "media" / f"{k}_1.jpg") for i, (k, p) in enumerate(posts, 1)]
    th = [(i, f) for i, f in th if f.exists()]
    if th:
        Wt, Ht, cols = 240, 300, 6; rows = (len(th) + cols - 1) // cols; sh = Image.new("RGB", (Wt * cols, Ht * rows), "white"); dr = ImageDraw.Draw(sh)
        fb = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 22)
        for j, (i, f) in enumerate(th):
            im = Image.open(f).convert("RGB"); im.thumbnail((Wt, Ht)); x, y = (j % cols) * Wt, (j // cols) * Ht; sh.paste(im, (x, y))
            dr.rectangle([x, y, x + 44, y + 30], fill="black"); dr.text((x + 6, y + 3), str(i), fill="white", font=fb)
        sh.save(d / "covers.jpg", quality=85)
    print(f"İcmal: {d / 'digest.md'}  ({len(posts)} paylaşım)")


def cmd_status():
    h = handle_of(sys.argv[2]); d, st = load(h); ps = st["posts"].values()
    from collections import Counter
    print(json.dumps({"hesab": h, "paylaşım": len(st["posts"]), "format": Counter(p["format"] for p in ps),
                      "media_emal": sum(1 for p in ps if p.get("media_done")), "yalnız_caption": sum(1 for p in ps if p.get("mənbə_qeyd")),
                      "son_run": st["runs"][-1] if st["runs"] else None}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    {"fetch": cmd_fetch, "media": cmd_media, "digest": cmd_digest, "status": cmd_status}[sys.argv[1]]()
