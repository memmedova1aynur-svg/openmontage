"""Paylaşım paketi qaralaması: caption, hook və üz qabığı başlığı üçün material.

  python3 brief.py <video.json> <hazır.mp4>
Nəticə: <hazır>_paket.md — danışıq mətni, hook namizədləri (sual/rəqəm/güclü açılış cümlələri),
kartların başlıqları, brend qaydaları və ig-caption formatında boş şablon. Son mətni Claude
danışığa sadiq yazır (qiymət/tarix/vəd uydurulmur); bu fayl onun əsasıdır.
"""
import json, re, subprocess, sys
from pathlib import Path
import kit

CFG, B, _ = kit.load(sys.argv[1]); MP4 = Path(sys.argv[2])
d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(MP4)], capture_output=True, text=True).stdout)
text = CFG.get("text", "").strip()
sents = [s.strip() for s in re.split(r"(?<=[.?!])\s+", text) if len(s.split()) >= 3]
hooks = [s for s in sents if s.endswith("?")][:3] + [s for s in sents if re.search(r"\d", s)][:2] + sents[:2]
seen, H = set(), []
for h in hooks:
    if h not in seen: seen.add(h); H.append(h)
cards = []
for s in kit.scenes(CFG):
    p = s.get("p", {}); t = p.get("text") or p.get("title") or p.get("head") or p.get("word") or " ".join(p.get("lines", []) if isinstance(p.get("lines"), list) and p.get("lines") and isinstance(p["lines"][0], str) else [])
    if t: cards.append(f"- {s['t0']:5.1f}s · {s['kind']}: {re.sub('<[^>]+>', ' ', str(t)).replace(chr(10), ' ')}")
cta = "Direct-ə " + CFG["cta"] if CFG.get("cta") else ("reklam: Direct çağırışı" if CFG.get("ad") else "şərh / yadda saxla")
L = [f"# Paylaşım paketi — {CFG.get('title', '')}", "", f"- müddət: {d:.0f} s · növ: {'reklam' if CFG.get('ad') else 'danışıq'} · brend: {B.get('name', '—')}",
     f"- çağırış: {cta}", f"- hashtag bazası: {' '.join(B.get('hashtags', [])) or '—'}", "",
     "## Hook namizədləri (danışıqdan)", *[f"{i + 1}. {h}" for i, h in enumerate(H[:5])], "",
     "## Kartlar", *(cards or ["—"]), "",
     "## Danışıq mətni", text, "",
     "## Şablon (ig-caption, Job A — hook videodadır)", "```", "<1-ci sətir: çağırış, ≤125 simvol>", "", "<2–4 qısa abzas: danışığa sadiq, axtarış sözləri cümlə içində>", "",
     "<bir çağırış>", "", "<≤5 hashtag>", "```", "", "Qaydalar: qiymət/tarix/vəd uydurulmur; yalnız videoda deyilənlər."]
out = MP4.with_name(MP4.stem + "_paket.md"); out.write_text("\n".join(L), encoding="utf-8"); print(f"paket: {out.name}")
