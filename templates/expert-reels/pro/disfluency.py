"""Dəqiq kəsim planı: yarımçıq dubllar, təkrarlar, «ıı/ee» səsləri, çəkiliş söhbəti.

Niyə: VAD-lı ASR yarımçıq dubl ilə düzgün dublu bir cümlə kimi yazır və «ıı», «uşağınızı → övladınızı»
kimi düzəlişləri atır. Nəticədə hər iki dubl videoda qalırdı (real müştəri rəyi, noyabr 2026).
Bu alət VAD-sız, disfluency prompt-lu ASR ilə hər sözü və dayanmanı ayrıca tutur, şübhəli
hissələri təklif edir və hər kəsim sərhədini səs dalğası ilə yoxlayır (heca kəsilməsin).

İstifadə:
  python3 disfluency.py <video> [--out DIR] [--lang az]
Çıxış (DIR, default: videonun yanında <ad>_kesim/):
  words.json      — bütün sözlər: [s, e, söz, ehtimal]
  segments.json   — cümlələr + bayraqlar (restart / filler / chatter / lowconf)
  keep.json       — təklif olunan saxlanılan aralıqlar [[s, e], ...] (sərhədlər səs dalğası ilə yoxlanılıb)
  review.md       — Claude/insan üçün oxunaqlı siyahı: hər cümlə, bayraq, səbəb
Son qərar Claude-undur: review.md-ni oxu, lazım olsa keep.json-u düzəlt (məzmun/mövzu seçimi).
"""
import argparse, difflib, json, re, subprocess, sys, wave
from pathlib import Path
import numpy as np

FILLERS = {"ee", "eee", "əə", "əəə", "ıı", "ııı", "ıhı", "ıhıı", "hı", "hıhı", "hm", "hmm", "mm", "mhm", "aa", "aaa", "uu", "uuu", "eh", "ehh", "ah", "həhə", "hə-hə"}
# çəkiliş söhbəti işarələri (operatorla danışıq, texniki an) — yalnız TƏKLİF; qərar Claude-undur
CHATTER_STRONG = ["hicab", "mikrofon", "kamera", "səs gəlir", "başdan başla", "nə deyim", "telefon"]
# operatorun adı və s. şəxsi sözlər repoda saxlanmır: instagram-clients/_agency/qaydalar.json → "chatter_words"
try:
    _q = Path(__file__).resolve().parents[3] / "instagram-clients/_agency/qaydalar.json"
    CHATTER_STRONG += json.load(open(_q)).get("chatter_words", []) if _q.exists() else []
except Exception: pass
CHATTER_WEAK = ["geçək", "keçək", "geçik", "keçin", "geçin", "geçəyim", "keçəyim", "davam", "çəkək", "tamam", "okey", "bir də", "hazırsan", "olar?", "falan"]  # yalnız qısa cümlədə və ya 2+ işarə
PROMPT = "Ee... ıı... Birincisi, uşağınızı, yox, övladınızı... hmm, yəni, şey... Hə, davam edək."
norm = lambda w: re.sub(r"[^\wəğıöüşç]", "", w.lower().replace("İ", "i").replace("I", "ı"))


def asr(path, lang):
    from faster_whisper import WhisperModel
    a = audio(path, 16000)
    m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=4)
    segs, _ = m.transcribe(a, language=lang, word_timestamps=True, vad_filter=False, beam_size=5,
                           condition_on_previous_text=False, initial_prompt=PROMPT)
    return [dict(s=s.start, e=s.end, t=s.text.strip(), w=[[x.start, x.end, x.word.strip(), round(x.probability, 3)] for x in s.words]) for s in segs]


def audio(path, sr):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


class Wave:
    def __init__(self, path):
        self.sr = 16000; self.x = audio(path, self.sr)
        e = np.sqrt(np.convolve(self.x ** 2, np.ones(160) / 160, "same"))  # 10 ms RMS
        self.db = 20 * np.log10(e + 1e-9)
        self.speech = np.percentile(self.db[self.db > -60], 90) if (self.db > -60).any() else -20

    def at(self, t): return float(self.db[min(len(self.db) - 1, max(0, int(t * self.sr)))])

    def quietest(self, a, b):
        i0, i1 = int(max(0, a) * self.sr), int(max(a + 0.01, b) * self.sr)
        seg = self.db[i0:i1]
        return (i0 + int(np.argmin(seg))) / self.sr if len(seg) else a


def safe_out(wv, word_end, next_start, pad=0.10):
    """Saxlanılan hissənin SONU: sözün sonundan ən az `pad` sonra, növbəti sözə toxunmadan, ən sakit nöqtədə."""
    lo = word_end + min(pad, max(0.03, (next_start - word_end) * 0.45))
    hi = min(word_end + 0.30, next_start - 0.03)
    return round(wv.quietest(lo, hi) if hi > lo + 0.02 else lo, 3)


def safe_in(wv, word_start, prev_end, pad=0.08):
    """Saxlanılan hissənin BAŞI: sözün başından ən az `pad` əvvəl (partlayan samit qorunur), ən sakit nöqtədə."""
    hi = word_start - min(pad, max(0.03, (word_start - prev_end) * 0.45))
    lo = max(prev_end + 0.03, word_start - 0.30)
    return round(max(0.0, wv.quietest(lo, hi) if hi > lo + 0.02 else hi), 3)


def analyse(segs, gap_cut=0.6):
    W = [w for s in segs for w in s["w"]]
    for i, s in enumerate(segs):
        s["i"] = i; s["flags"] = []; s["n"] = [norm(w[2]) for w in s["w"] if norm(w[2]) and norm(w[2]) not in FILLERS]
        txt = s["t"].lower()
        raw = [norm(w[2]) for w in s["w"] if norm(w[2])]
        if raw and all(x in FILLERS for x in raw): s["flags"].append("filler")
        weak = [c for c in CHATTER_WEAK if c in txt]
        hits = [c for c in CHATTER_STRONG if c in txt] + (weak if len(s["n"]) <= 5 or len(weak) >= 2 else [])
        if not hits and len(s["n"]) <= 3 and s["t"].rstrip().endswith("?") and i > 0: hits = ["qısa-sual"]  # «Sonra nə?» — operatorun sualı
        if hits: s["flags"].append("chatter:" + ",".join(hits))
        lp = [w[3] for w in s["w"]]
        if lp and np.mean(lp) < 0.55: s["flags"].append("lowconf")
        if s["t"].rstrip().endswith(("...", "…")) or (s["w"] and s["w"][-1][2].endswith(("...", "…"))): s["flags"].append("incomplete")
    # yarımçıq dubl: növbəti 3 cümlədən biri eyni sözlərlə başlayır və ya çox oxşardır → əvvəlki atılır
    for i, a in enumerate(segs):
        if not a["n"]: continue
        for b in segs[i + 1:i + 4]:
            if not b["n"]: continue
            same_start = len(a["n"]) >= 1 and a["n"][:2] == b["n"][:2] and len(a["n"]) <= len(b["n"]) + 2
            ratio = difflib.SequenceMatcher(None, a["n"], b["n"][:len(a["n"]) + 3]).ratio()
            if same_start or ratio >= 0.62:
                a["flags"].append(f"restart→{b['i']}"); break
    # məzmundan əvvəl/sonra qısa söhbət (≤3 söz): çəkilişə hazırlıq, «əl, asın», «bəli»
    content = [s for s in segs if len(s["n"]) >= 4 and not s["flags"]]
    if content:
        for s in segs:
            if len(s["n"]) <= 3 and (s["e"] <= content[0]["s"] or s["s"] >= content[-1]["e"]) and not any(f.startswith(("restart", "filler", "chatter")) for f in s["flags"]):
                s["flags"].append("chatter:kənar")
    # cümlə içi yenidən başlama: A-nın son hissəsi B ilə eyni başlayır («…və uşağı … buraxmayın.» → «Və uşağı …»)
    real = [s for s in segs if not any(f.startswith(("filler", "chatter")) for f in s["flags"])]
    for a, b in zip(real, real[1:]):
        if any(f.startswith(("restart", "filler", "chatter")) for f in a["flags"]) or len(b["n"]) < 3: continue
        wn = [(k, norm(w[2])) for k, w in enumerate(a["w"]) if norm(w[2]) and norm(w[2]) not in FILLERS]
        for j in range(1, len(wn) - 1):
            tail = [x for _, x in wn[j:]]
            sim0 = difflib.SequenceMatcher(None, tail[0], b["n"][0]).ratio() >= 0.75 if b["n"] else False
            if sim0 and len(tail) >= 2 and tail[1] == b["n"][1] and difflib.SequenceMatcher(None, tail, b["n"][:len(tail) + 2]).ratio() >= 0.35:
                a["cut_from"] = wn[j][0]; a["flags"].append(f"tail-restart→{b['i']}"); break
    # cümlə içi «ıı/ee» sözləri
    for s in segs:
        s["fillers_in"] = [[w[0], w[1], w[2]] for w in s["w"] if norm(w[2]) in FILLERS]
    return W


def plan_keep(segs, wv, gap_cut=0.6):
    drop_flags = ("filler", "restart", "chatter")
    keep_w = []
    for s in segs:
        if any(f.startswith(drop_flags) for f in s["flags"]): continue
        ws = s["w"][:s["cut_from"]] if "cut_from" in s else s["w"]
        keep_w += [w for w in ws if norm(w[2]) and norm(w[2]) not in FILLERS]
    keep_w.sort(key=lambda w: w[0])
    allw = sorted([w for s in segs for w in s["w"]], key=lambda w: w[0])
    idx = {id(w): k for k, w in enumerate(allw)}
    # saxlanılan sözləri ardıcıl qruplara böl: arada atılan söz və ya uzun dayanma varsa — kəsim
    groups = []
    for w in keep_w:
        if groups:
            p = groups[-1][-1]; between = idx[id(w)] - idx[id(p)] > 1
            if not between and w[0] - p[1] <= gap_cut: groups[-1].append(w); continue
        groups.append([w])
    keep = []
    for g in groups:
        k0, k1 = idx[id(g[0])], idx[id(g[-1])]
        prev_end = allw[k0 - 1][1] if k0 > 0 else 0.0
        next_start = allw[k1 + 1][0] if k1 + 1 < len(allw) else g[-1][1] + 0.6
        keep.append([safe_in(wv, g[0][0], prev_end), safe_out(wv, g[-1][1], next_start)])
    return keep


def check_bounds(keep, wv):
    """Hər sərhəddə səs: -30 dB-dən ucadırsa — sözün ortası ola bilər (QA ilə eyni hədd)."""
    bad = []
    for a, b in keep:
        for t, side in ((a, "baş"), (b, "son")):
            if wv.at(t) > -30: bad.append({"t": t, "side": side, "db": round(wv.at(t), 1)})
    return bad


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("--out"); ap.add_argument("--lang", default="az")
    ap.add_argument("--gap", type=float, default=0.6, help="bu uzunluqdan böyük dayanma qısaldılır (təbii ritm üçün ≥0.5)")
    ap.add_argument("--reuse", action="store_true", help="words.json varsa ASR-i təkrarlama")
    ap.add_argument("--to-config", help="PRO vN.json: atılan aralıqları 'autoCut' kimi yaz (build.py tətbiq edir)")
    a = ap.parse_args()
    v = Path(a.video); out = Path(a.out) if a.out else v.parent / f"{v.stem}_kesim"; out.mkdir(parents=True, exist_ok=True)
    if a.reuse and (out / "segments_raw.json").exists(): segs = json.load(open(out / "segments_raw.json"))
    else:
        segs = asr(v, a.lang); json.dump(segs, open(out / "segments_raw.json", "w"), ensure_ascii=False)
    W = analyse(segs, a.gap); wv = Wave(v)
    keep = plan_keep(segs, wv, a.gap); bad = check_bounds(keep, wv)
    json.dump(W, open(out / "words.json", "w"), ensure_ascii=False)
    json.dump(segs, open(out / "segments.json", "w"), ensure_ascii=False, indent=0)
    json.dump({"keep": keep, "boundary_warn": bad}, open(out / "keep.json", "w"), ensure_ascii=False, indent=1)
    L = [f"# Kəsim planı: {v.name}", "", "Bayraqlı cümlələr atılır (restart = yarımçıq dubl, filler = ıı/ee, chatter = çəkiliş söhbəti).",
         "Claude: mövzuya aid olmayan, amma bayraqsız qalan hissələri də yoxla; keep.json-u lazım olsa düzəlt.", ""]
    for s in segs:
        fl = ",".join(s["flags"]) or "—"; mark = "✂" if any(f.startswith(("filler", "restart", "chatter")) for f in s["flags"]) else "✓"
        fi = f"  [ıı/ee: {len(s['fillers_in'])}]" if s["fillers_in"] else ""
        lowp = [w[2] for w in s["w"] if len(w) > 3 and w[3] < 0.45]
        if lowp: fi += f"  [şübhəli söz: {', '.join(lowp)}]"
        L.append(f"{mark} {s['i']:>3} {s['s']:7.2f}–{s['e']:7.2f}  [{fl}]{fi}  {s['t']}")
    tot = sum(b - a for a, b in keep)
    L += ["", f"Saxlanılan: {len(keep)} parça, {tot:.1f} s. Sərhəd xəbərdarlığı: {len(bad)}"]
    open(out / "review.md", "w").write("\n".join(L))
    if a.to_config:
        cfg = json.load(open(a.to_config)); cuts = [[round(keep[i][1], 3), round(keep[i + 1][0], 3)] for i in range(len(keep) - 1) if keep[i + 1][0] - keep[i][1] > 0.05]
        if keep and keep[0][0] > 0.3: cuts.insert(0, [0.0, keep[0][0]])
        cfg["autoCut"] = cuts; cfg["autoCutEnd"] = keep[-1][1] if keep else None
        json.dump(cfg, open(a.to_config, "w"), ensure_ascii=False, indent=1); L.append(f"autoCut → {a.to_config}: {len(cuts)} aralıq")
    print("\n".join(L[-40:])); print("→", out)


if __name__ == "__main__":
    main()
