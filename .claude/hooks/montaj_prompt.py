#!/usr/bin/env python3
"""UserPromptSubmit hook: video/montaj tapşırığında məcburi AYRA montaj axınını və müştərinin brend fayllarını
kontekstə əlavə edir. Müştəri adları kodda yoxdur — instagram-clients/ qovluqlarından oxunur."""
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CL = ROOT / "instagram-clients"
KEYS = r"montaj|video|reels?|rils|render|kəs(?:im|in)?\b|edit|çəkiliş|cekilis|klip|kadraj|subtitr|altyazı|drive\.google\.com/.*(?:folders|file)"


def norm(s: str) -> str:
    s = s.lower().translate(str.maketrans("əıöüşçğ", "eiousch"))
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    p = data.get("prompt", "")
    words = set(re.findall(r"[a-z]+", norm(p)))
    hits = []
    if CL.is_dir():
        for d in sorted(CL.iterdir()):
            if not d.is_dir() or d.name.startswith(("_", ".")):
                continue
            first = d.name.split("-")[0]
            if any(w == first or (len(first) >= 4 and w.startswith(first)) for w in words):
                hits.append(d)
    if not re.search(KEYS, p, re.I):
        # montaj deyil, amma müştəri adı keçir → əvvəl müştərinin master faylı
        for d in hits:
            m = sorted(d.glob("*_MASTER.md")) + [d / "MASTER_BRAND_FILE.md"]
            m = [str(x.relative_to(ROOT)) for x in m if x.exists()]
            if m:
                print(f"AYRA müştəri qaydası (avtomatik hook): {d.name} üçün işə başlamazdan əvvəl oxu: {', '.join(m)}. "
                      "Təsdiqlənmiş dizayn sistemi kilidlidir; tamamlanmış mərhələlər agentlik istəmədən yenidən açılmır.")
        return
    lines = [
        "AYRA MONTAJ DARVAZASI (avtomatik hook — məcburidir):",
        "Bu mesaj video/montaj tapşırığına bənzəyir. Montaja başlamazdan əvvəl ardıcıllıq dəyişmir:",
        "1) müştərini müəyyən et → 2) `python -m montaj.gate start <müştəri> <video_id> --type N [--approach Mxx]` "
        "(MASTER_BRAND_FILE + editing-dna + brand_kit-i çap edir və oxunmasını qeyd edir) → 3) növü `python -m montaj.session types` "
        "ilə seç; növsüz başlama, bir şablonu bütün formatlara tətbiq etmə → 4) ayra-creative-video-director: concept.md → "
        "5) ayra-senior-video-editor: templates/expert-reels/pro (disfluency, engine, color_auto, audio_pro), cut_report.md → "
        "6) render final.mp4 + clean.mp4 → 7) qc_render.py + qc_sheet.jpg-yə gözlə baxış → QC/visual_review.md → "
        "8) `python -m montaj.gate deliver ... --to paketler/yekun/<ad>.mp4`.",
        "Darvazadan keçməyən video FINAL/YEKUN adlandırılmır. yekun/, gonder/, final/ qovluqlarına birbaşa yazma bloklanır.",
        "Bir videoya deyilən düzəliş başqa videoya özbaşına tətbiq olunmur.",
        "İş axını: montaj/IS_AXINI.md · skill-lər: .claude/skills/AYRA_SKILLS.md",
    ]
    if hits:
        for d in hits:
            fs = [str((d / f).relative_to(ROOT)) for f in [x.name for x in sorted(d.glob("*_MASTER.md"))] + ["MASTER_BRAND_FILE.md", "editing-dna.md", "brand_kit.json", "brand_profile.md"] if (d / f).exists()]
            lines.append(f"Müştəri qovluğu: {d.relative_to(ROOT)} — montajdan əvvəl oxu: {', '.join(fs)}")
    else:
        lines.append("Müştəri mesajdan təyin olunmadı: konteksdən təyin et və ya soruş; təxmin etmə.")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
