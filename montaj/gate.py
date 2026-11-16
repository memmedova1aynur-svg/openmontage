"""Montaj darvazası — AYRA istehsal qaydalarını kodla məcbur edir.

Heç bir video bu darvazadan keçmədən YEKUN sayılmır və təhvil qovluğuna (yekun/, gonder/, final/) yazılmır.
.claude/hooks/montaj_guard.py həmin qovluqlara birbaşa yazmanı bloklayır; yeganə yol `deliver`-dir.

  python -m montaj.gate start   <müştəri> <video_id> --type N [--approach M02] [--source fayl] [--goal maarif]
  python -m montaj.gate reread  <müştəri> <video_id>        # brend/DNA faylı dəyişəndə yenidən oxu
  python -m montaj.gate check   <müştəri> <video_id>
  python -m montaj.gate deliver <müştəri> <video_id> --to paketler/yekun/Ad.mp4

İş qovluğu: instagram-clients/<müştəri>/montaj/<video_id>/
  job.json          müştəri, növ, yanaşma, mənbə, oxunmuş brend fayllarının sha256-ı
  concept.md        konsept kartı (ayra-creative-video-director) — şablon `start` ilə yaranır
  cut_report.md     kəsim hesabatı (ayra-senior-video-editor)
  final.mp4         render
  clean.mp4         eyni zaman xəttində qrafikasız versiya (üz örtülməsi yoxlaması üçün)
  QC/qc.json        templates/expert-reels/pro/qc_render.py nəticəsi
  QC/visual_review.md  qc_sheet.jpg-yə gözlə baxışın qeydi, «NƏTİCƏ: KEÇDİ» sətri ilə
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENTS = ROOT / "instagram-clients"
QC_RENDER = ROOT / "templates/expert-reels/pro/qc_render.py"
BRAND_FILES = ["MASTER_BRAND_FILE.md", "editing-dna.md", "brand_kit.json", "montage_rules.json"]  # bu sıra ilə oxunur
RULES = "montage_rules.json"


def brand_files(cd: Path) -> list[str]:
    """<MÜŞTƏRİ>_MASTER.md (giriş nöqtəsi) birinci, sonra standart brend faylları."""
    return sorted(p.name for p in cd.glob("*_MASTER.md")) + BRAND_FILES  # müştərinin kadraj hədləri (qc_render --rules)
REQUIRED_DNA = "editing-dna.md"
CONCEPT_HEADS = ["Növ", "Məqsəd", "Hook", "Montaj üslubu", "Kadraj", "Vizual cihazlar", "Rəng", "Səs", "Subtitr", "İstifadə etmə"]
DELIVERY_DIRS = ("yekun", "gonder", "final")


class GateError(SystemExit):
    pass


def die(msg: str) -> None:
    print(f"DARVAZA BAĞLIDIR: {msg}", file=sys.stderr)
    raise GateError(3)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def client_dir(c: str) -> Path:
    d = CLIENTS / c
    if not d.is_dir():
        have = sorted(x.name for x in CLIENTS.iterdir() if x.is_dir() and not x.name.startswith(("_", "."))) if CLIENTS.is_dir() else []
        die(f"müştəri qovluğu yoxdur: {d}. Mövcud: {', '.join(have) or '—'}")
    return d


def job_dir(c: str, vid: str) -> Path:
    return client_dir(c) / "montaj" / vid


def load_job(c: str, vid: str) -> dict:
    p = job_dir(c, vid) / "job.json"
    if not p.exists():
        die(f"iş qeydi yoxdur. Əvvəl: python -m montaj.gate start {c} {vid} --type N")
    return json.loads(p.read_text())


def read_brand(c: str) -> dict[str, str]:
    d = client_dir(c)
    if not (d / REQUIRED_DNA).exists():
        die(f"{d / REQUIRED_DNA} yoxdur — montajdan əvvəl müştərinin Editing DNA faylı yaradılmalıdır.")
    seen = {}
    for name in brand_files(d):
        p = d / name
        if p.exists():
            seen[name] = sha(p)
            print(f"\n======== {p.relative_to(ROOT)} ========")
            print(p.read_text()[:20000])
    return seen


CONCEPT_TPL = """# Konsept kartı — {vid}
_Doldurulmamış «…» sətri qalsa darvaza bağlı qalır._

- **Növ:** {tnum}. {tname}{appr}
- **Məqsəd:** …
- **Hook (ilk 2 s):** …
- **Montaj üslubu:** …
- **Kadraj:** … (Editing DNA: baş üstü boşluq, zoom həddi)
- **Vizual cihazlar (≤3):** …
- **Rəng:** color_auto, təbii dəri (DNA)
- **Səs:** audio_pro; musiqi …
- **Subtitr:** …
- **İstifadə etmə:** … (DNA qadağaları + son 3 videoda işlənmiş cihazlar)
- **Bu videoya aid düzəlişlər (başqasına keçmir):** —
"""


def cmd_start(a) -> None:
    from montaj import types
    try:
        t = types.get(a.type)
        appr = types.parse_approaches(a.approach) if a.approach else []
    except KeyError as e:
        die(f"{e}. Siyahı: python -m montaj.session types")
    d = job_dir(a.client, a.video)
    d.mkdir(parents=True, exist_ok=True)
    (d / "QC").mkdir(exist_ok=True)
    brand = read_brand(a.client)
    job = {"client": a.client, "video": a.video, "type": int(a.type), "type_name": t["name"], "approaches": appr,
           "goal": a.goal or "", "source": a.source or "", "brand_read": brand,
           "started": dt.datetime.now().isoformat(timespec="seconds"), "delivered": []}
    jp = d / "job.json"
    if jp.exists():
        old = json.loads(jp.read_text()); job["delivered"] = old.get("delivered", []); job["started"] = old.get("started", job["started"])
    jp.write_text(json.dumps(job, ensure_ascii=False, indent=1))
    cp = d / "concept.md"
    if not cp.exists():
        an = (" · yanaşma " + "+".join(f"{k} {types.APPROACHES[k]['name']}" for k in appr)) if appr else ""
        cp.write_text(CONCEPT_TPL.format(vid=a.video, tnum=a.type, tname=t["name"], appr=an))
    print(f"\nİŞ AÇILDI: {d.relative_to(ROOT)} · növ {a.type}. {t['name']} · oxunan brend faylları: {', '.join(brand)}")
    print("Növbəti: concept.md doldur → cut_report.md → render final.mp4 (+clean.mp4) → qc_render → QC/visual_review.md → gate deliver")


def cmd_reread(a) -> None:
    job = load_job(a.client, a.video)
    job["brand_read"] = read_brand(a.client)
    (job_dir(a.client, a.video) / "job.json").write_text(json.dumps(job, ensure_ascii=False, indent=1))
    print("\nBrend faylları yenidən oxundu.")


def recent_concepts(c: str, vid: str, n: int = 3) -> list[tuple[str, str]]:
    base = client_dir(c) / "montaj"
    jobs = []
    for jp in base.glob("*/job.json"):
        j = json.loads(jp.read_text())
        if j.get("video") != vid and j.get("delivered"):
            jobs.append((j["delivered"][-1]["at"], jp.parent))
    out = []
    for _, d in sorted(jobs, reverse=True)[:n]:
        cp = d / "concept.md"
        if cp.exists():
            out.append((d.name, cp.read_text()))
    return out


def field(txt: str, head: str) -> str:
    m = re.search(rf"\*\*{re.escape(head)}[^*]*:\*\*\s*(.+)", txt)
    return m.group(1).strip() if m else ""


def probe(p: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(p)], capture_output=True, text=True)
    return json.loads(r.stdout or "{}")


def check(c: str, vid: str) -> list[str]:
    errs: list[str] = []
    job = load_job(c, vid)
    d = job_dir(c, vid)
    cd = client_dir(c)
    # 1. brend faylları oxunub və o vaxtdan dəyişməyib
    for name in brand_files(cd):
        p = cd / name
        if p.exists() and job["brand_read"].get(name) != sha(p):
            errs.append(f"{name} oxunduqdan sonra dəyişib və ya oxunmayıb → python -m montaj.gate reread {c} {vid}")
    # 2. konsept kartı
    cp = d / "concept.md"
    if not cp.exists():
        errs.append("concept.md yoxdur")
    else:
        txt = cp.read_text()
        for h in CONCEPT_HEADS:
            v = field(txt, h)
            if not v or v.startswith("…"):
                errs.append(f"concept.md: «{h}» doldurulmayıb")
        hook = field(txt, "Hook").lower()
        style = field(txt, "Montaj üslubu").lower()
        for name, other in recent_concepts(c, vid):
            if hook and hook == field(other, "Hook").lower():
                errs.append(f"concept.md: hook {name} videosu ilə eynidir (dəyişkənlik qaydası)")
            if style and style == field(other, "Montaj üslubu").lower():
                errs.append(f"concept.md: montaj üslubu {name} videosu ilə eynidir (hər videonun öz üslubu)")
    # 3. kəsim hesabatı
    cr = d / "cut_report.md"
    if not cr.exists() or len(cr.read_text().strip()) < 80:
        errs.append("cut_report.md yoxdur və ya boşdur")
    # 4. render + texniki parametrlər
    fm = d / "final.mp4"
    if not fm.exists():
        errs.append("final.mp4 yoxdur")
        return errs
    st = probe(fm).get("streams", [])
    v = next((s for s in st if s.get("codec_type") == "video"), {})
    au = next((s for s in st if s.get("codec_type") == "audio"), {})
    if (v.get("width"), v.get("height")) != (1080, 1920):
        errs.append(f"ölçü {v.get('width')}x{v.get('height')} (1080x1920 olmalıdır)")
    if v.get("codec_name") != "h264" or au.get("codec_name") != "aac":
        errs.append(f"kodek {v.get('codec_name')}/{au.get('codec_name')} (h264/aac olmalıdır)")
    # 5. avtomatik QC (qc_render.py) — final-dan yeni olmalıdır, fail boş
    qj = d / "QC" / "qc.json"
    if not qj.exists() or qj.stat().st_mtime < fm.stat().st_mtime:
        rr = f" --rules {(cd / RULES).relative_to(ROOT)}" if (cd / RULES).exists() else ""
        errs.append(f"QC final.mp4-dən sonra işlədilməyib → python3 {QC_RENDER.relative_to(ROOT)} {fm.relative_to(ROOT)} --clean {(d / 'clean.mp4').relative_to(ROOT)} --out {(d / 'QC').relative_to(ROOT)}{rr}")
    else:
        q = json.loads(qj.read_text())
        rp = cd / RULES
        if rp.exists() and (q.get("info", {}).get("rules") or {}).get("sha") != hashlib.sha256(rp.read_bytes()).hexdigest()[:16]:
            errs.append(f"QC müştərinin kadraj hədləri ilə işlədilməyib → qc_render.py ... --rules {rp.relative_to(ROOT)}")
        for f in q.get("fail", []):
            errs.append(f"qc_render FAIL: {json.dumps(f, ensure_ascii=False)[:300]}")
        if not q.get("info", {}).get("frames_checked"):
            errs.append("qc_render heç bir üz kadrını yoxlamayıb (kadraj/zoom ölçülməyib)")
        ecj = json.loads((d / "QC" / "edit_checks.json").read_text()) if (d / "QC" / "edit_checks.json").exists() else {}
        if ecj.get("overlay_face_bad"):
            errs.append(f"qrafika üzü örtür (render zamanı ölçülüb): {ecj['overlay_face_bad'][:5]}")
        if not job.get("no_graphics") and not ecj.get("overlay_face_checked") and any("overlay_face" in w and isinstance(w["overlay_face"], str) for w in q.get("warn", [])):
            errs.append("üz örtülməsi yoxlanmayıb: clean.mp4 (qrafikasız) render et və qc_render-ə --clean ver")
    # 5b. montaj yoxlamaları (müştəri qaydası tələb edirsə məcburi): söz içində kəsim yox, qatlar kadr daxilində
    ec = d / "QC" / "edit_checks.json"
    need = (cd / RULES).exists() and json.loads((cd / RULES).read_text()).get("require_edit_checks")
    if ec.exists():
        e = json.loads(ec.read_text())
        if ec.stat().st_mtime < fm.stat().st_mtime - 600:
            errs.append("edit_checks.json final.mp4-dən köhnədir")
        if e.get("spoken_not_in_subtitle"):
            errs.append(f"danışıqdakı söz subtitrdə yoxdur — subtitri danışığa uyğunlaşdır: {e['spoken_not_in_subtitle'][:5]}")
        if e.get("missing_spec_words"):
            errs.append(f"mətndəki söz səsdə yoxdur (artıq kəsilib, məzmun itib): {e['missing_spec_words'][:5]}")
        if e.get("missing_anchors"):
            errs.append(f"qrafika hadisəsi sözə bağlanmayıb (yanlış vaxtda çıxır): {e['missing_anchors'][:5]}")
        if e.get("extra_spoken_words"):
            errs.append(f"səsdə mətndə olmayan söz qalıb (təkrar/yarımçıq dubl): {e['extra_spoken_words'][:5]}")
        if e.get("cuts_inside_words"):
            errs.append(f"söz ortasından kəsim: {e['cuts_inside_words'][:8]} (yarımçıq söz)")
        if e.get("layers_out_of_frame"):
            errs.append(f"qrafika/ikon kadrdan çıxır: {e['layers_out_of_frame'][:5]}")
    elif need:
        errs.append("QC/edit_checks.json yoxdur (müştəri qaydası: söz-sərhəd və qat-kadr yoxlaması məcburidir)")
    # 6. gözlə baxış
    vr = d / "QC" / "visual_review.md"
    sheet = d / "QC" / "qc_sheet.jpg"
    if not vr.exists() or (sheet.exists() and vr.stat().st_mtime < sheet.stat().st_mtime):
        errs.append("QC/visual_review.md yoxdur və ya qc_sheet.jpg-dən köhnədir (12 kadra baxış qeyd olunmalıdır)")
    elif not re.search(r"NƏTİCƏ:\s*KEÇDİ", vr.read_text()):
        errs.append("visual_review.md-də «NƏTİCƏ: KEÇDİ» yoxdur")
    return errs


def cmd_check(a) -> None:
    errs = check(a.client, a.video)
    if errs:
        print("DARVAZA BAĞLIDIR — " + a.video, file=sys.stderr)
        for e in errs:
            print("  ✗ " + e, file=sys.stderr)
        raise GateError(3)
    print(f"DARVAZA AÇIQDIR — {a.video}: bütün yoxlamalar keçdi")


def cmd_deliver(a) -> None:
    errs = check(a.client, a.video)
    if errs:
        print("TƏHVİL BLOKLANDI — " + a.video, file=sys.stderr)
        for e in errs:
            print("  ✗ " + e, file=sys.stderr)
        raise GateError(3)
    cd = client_dir(a.client)
    dest = (cd / a.to).resolve()
    if cd.resolve() not in dest.parents:
        die("təhvil yeri müştəri qovluğunun içində olmalıdır")
    dest.parent.mkdir(parents=True, exist_ok=True)
    src = job_dir(a.client, a.video) / "final.mp4"
    shutil.copy2(src, dest)
    job = load_job(a.client, a.video)
    rec = {"at": dt.datetime.now().isoformat(timespec="seconds"), "to": str(dest.relative_to(ROOT)), "sha": sha(src)}
    job["delivered"].append(rec)
    (job_dir(a.client, a.video) / "job.json").write_text(json.dumps(job, ensure_ascii=False, indent=1))
    log = cd / "montaj" / "DELIVERIES.md"
    with log.open("a") as f:
        f.write(f"- {rec['at']} · {a.video} · növ {job['type']} · {rec['to']} · sha {rec['sha']}\n")
    print(f"TƏHVİL: {rec['to']} (darvaza keçdi)")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="python -m montaj.gate")
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("start"); s.add_argument("client"); s.add_argument("video"); s.add_argument("--type", required=True)
    s.add_argument("--approach"); s.add_argument("--source"); s.add_argument("--goal")
    for n in ("reread", "check"):
        x = sp.add_parser(n); x.add_argument("client"); x.add_argument("video")
    x = sp.add_parser("deliver"); x.add_argument("client"); x.add_argument("video"); x.add_argument("--to", required=True)
    a = ap.parse_args(argv)
    {"start": cmd_start, "reread": cmd_reread, "check": cmd_check, "deliver": cmd_deliver}[a.cmd](a)


if __name__ == "__main__":
    main()
