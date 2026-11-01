"""Video növləri və montaj yanaşmalarının reyestri — sistemin vahid mənbəyi.

`templates/expert-reels/VIDEO_TYPES.md` insan üçün izahdır; bu fayl isə mühərrikin oxuduğu formadır:
sorğu (`types --survey`), layihənin növü (`new --type`, `set-type`), storyboard variantları (`types <N>`),
yekun yoxlamanın növ qaydaları (`verify`) və müştəri tarixçəsi (`choose`) buradan qurulur.

Status: "ready" — mühərrikdə tam; "partial" — əsas hissə var, `gaps`-da çatışmayan; "missing" — əl ilə/ümumi alətlərlə,
xüsusi alət yoxdur; "planned" — material (məs. loqo) gələndə. Olmayan imkanı istifadəçiyə hazır kimi təqdim etmə.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Montaj yanaşmaları (M01–M14)
# ---------------------------------------------------------------------------

APPROACHES: dict[str, dict[str, Any]] = {
    "M01": {"name": "Təmiz ekspert montajı", "what": "lazımsız hissələr çıxır, altyazı, rəng, səs; effekt minimal",
            "engine": ["storyboard", "cut", "retakes", "plan: captions, look"], "status": "ready"},
    "M02": {"name": "Tipoqrafik vurğu", "what": "əsas söz və fikirlər ekranda yazı ilə (pops, başlıq, siyahı)",
            "engine": ["plan: graphics emphasis/title/list/section", "zooms"], "status": "ready"},
    "M03": {"name": "Ekspert + qrafik izah", "what": "sxem, rəqəm, addım qrafikası; ekspert dairədə və ya yanda",
            "engine": ["scenes", "mg-scan", "make-broll", "broll cover_pip"], "status": "ready"},
    "M04": {"name": "Danışıq + tam ekran əlavə görüntü", "what": "danışıq davam edir, ekranı əlavə görüntü tutur",
            "engine": ["add-broll", "broll cover/insert"], "status": "ready"},
    "M05": {"name": "Material əsasdır, ekspert kiçik pəncərədə", "what": "ekran/sənəd/fəaliyyət tam kadr, ekspert pəncərədə",
            "engine": ["add-broll", "broll pip"], "status": "partial", "gaps": "pəncərənin materialı örtməməsi avtomatik yoxlanmır"},
    "M06": {"name": "Müqayisəli montaj", "what": "iki variant/fikir yan-yana və ya ardıcıl qarşılaşdırılır",
            "engine": ["scenes: mg_compare"], "status": "partial", "gaps": "iki videonun bölünmüş ekranı yoxdur"},
    "M07": {"name": "Hekayə və çıxış montajı", "what": "intonasiya, pauza və jest qorunur; ritm yavaş, kəsim az",
            "engine": ["cut (səssiz sərhəd)", "highlights"], "status": "ready"},
    "M08": {"name": "Praktik nümayiş montajı", "what": "addımlar ardıcıl görünür, danışıq hərəkətlə üst-üstə düşür",
            "engine": ["add-broll", "broll insert/pip", "graphics list"], "status": "partial",
            "gaps": "addım nömrələri əl ilə; hərəkət–danışıq uyğunluğu Claude-un yoxlamasıdır"},
    "M09": {"name": "Tədbir və proses montajı", "what": "görüntülər musiqi ilə: açılış → inkişaf → tamamlanma",
            "engine": ["event-scan", "event-plan", "variants", "choose"], "status": "partial",
            "gaps": "yavaşlatma yoxdur (sürət dəyişməsi dəstəklənmir); şəkillər hərəkətsizdir; açılış/final xronologiya və "
                    "ümumi plana görə seçilir — Claude variant şəklində yoxlayır"},
    "M10": {"name": "Yumorlu sual-cavab montajı", "what": "sürətli ritm, sual ekranda, reaksiya anları saxlanılır",
            "engine": ["cut", "sfx", "graphics title"], "status": "missing", "gaps": "sual/cavab bölgüsü və sürətli ritm şablonu yoxdur"},
    "M11": {"name": "Səsləndirməli vizual hekayə", "what": "səsləndirmə əsasdır, görüntülər onun ardınca düzülür",
            "engine": ["add-broll", "broll cover"], "status": "partial", "gaps": "səsə görə kadrların avtomatik düzülməsi yoxdur"},
    "M12": {"name": "Nağıl və animasiya", "what": "cizgi obrazları və səhnələr səsləndirmə ilə", "engine": ["tale-plan", "scenes: tale_*"],
            "status": "ready"},
    "M13": {"name": "Hərəkətli kartlar", "what": "səhifə-səhifə mətn/qrafika; video-karusel", "engine": ["carousel-plan", "carousel"],
            "status": "partial", "gaps": "ekspertsiz (yalnız kart) səhifələr ayrıca alət deyil"},
    "M14": {"name": "Təlim dərsi montajı", "what": "üfüqi, sakit; dərsin məntiqi ardıcıllığı; Reels ritmi yoxdur",
            "engine": ["new --aspect 16:9", "cut", "plan: captions, section"], "status": "partial",
            "gaps": "kursun bölümləri arasında eyni üslubun avtomatik ötürülməsi yoxdur"},
}

# ---------------------------------------------------------------------------
# Video növləri
# ---------------------------------------------------------------------------
# variants: 3 storyboard (A/B/C) üçün yanaşma birləşmələri; Claude materiala görə uyğunlaşdırır.
# rules: maşın yoxlaması olan qaydalar (RULES), notes: Claude-un özünün yoxladığı qaydalar.

TYPES: dict[int, dict[str, Any]] = {
    1: {"name": "Birbaşa kameraya ekspert danışığı", "short": "Kameraya danışıq", "family": "danisiq",
        "approaches": ["M01", "M02", "M03"], "status": "ready",
        "variants": [("M01", "Təmiz: altyazı + rəng, effekt az"), ("M01+M02", "Vurğulu yazılar və seçilmiş zoom"),
                     ("M01+M03", "Qrafik izah (sxem/rəqəm) ekspert dairədə")],
        "commands": ["storyboard", "retakes", "framefix", "voice-clean", "looks", "variants", "choose", "render", "verify"],
        "notes": ["Hook, B-roll və hər cümləyə effekt avtomatik deyil", "Teleprompter ayrıca növ deyil"]},
    2: {"name": "Kadrarxası sual-cavab", "short": "Sual-cavab (kadrarxası)", "family": "danisiq",
        "approaches": ["M01", "M02"], "status": "partial", "gaps": "kadrarxası sual avtomatik ayrılmır — Claude transkriptdən tapır",
        "variants": [("M01", "Sual səsi qalır, cavab təmiz"), ("M01+M02", "Sual ekranda yazı ilə, səsi çıxır"),
                     ("M01", "Yalnız cavab (tək başına anlaşılırsa)")],
        "commands": ["storyboard", "retakes", "cut", "variants", "choose", "render", "verify"],
        "notes": ["Sual çıxarılırsa, cavabın tək başına anlaşıldığını yoxla"]},
    3: {"name": "Hazır mətnli reklam və xidmət təqdimatı", "short": "Reklam (hazır mətn)", "family": "reklam",
        "approaches": ["M01", "M02", "M03", "M04"], "status": "ready",
        "variants": [("M01+M02", "Danışıq + qiymət/çağırış kartları"), ("M03", "Təklif qrafika ilə açılır"),
                     ("M04", "Danışıq + tam ekran əlavə görüntü")],
        "commands": ["storyboard", "ad-scan", "ad-plan", "variants", "choose", "render", "verify"],
        "rules": ["source_order", "graphic_numbers_spoken"],
        "notes": ["Mətnin ardıcıllığı qorunur, hook əvvələ çəkilmir", "Qiymət, tarix, fayda, nəticə, çağırış uydurulmur"]},
    4: {"name": "Seminardan ekspert çıxarışı", "short": "Seminardan çıxarış", "family": "seminar",
        "approaches": ["M01", "M03", "M07", "M08"], "status": "ready",
        "subtypes": ["izah/mikrodərs", "motivasiyaedici çıxış", "hadisə/hekayə", "auditoriya ilə sual-cavab", "praktik nümayiş"],
        "variants": [("M01", "Təmiz çıxarış"), ("M03", "Qrafik izahla"), ("M07", "Çıxış ritmi (pauza, jest qorunur)")],
        "commands": ["highlights", "extract", "framefix", "storyboard", "variants", "choose", "render", "verify"],
        "notes": ["Hissə kontekstsiz də anlaşılmalıdır", "Səbəb əlaqəsi təhrif olunmur, fikir yarımçıq kəsilmir"]},
    5: {"name": "Seminar və tədbir icmalı", "short": "Tədbir icmalı", "family": "seminar",
        "approaches": ["M09"], "status": "partial", "gaps": "yavaşlatma yoxdur; şəkillər hərəkətsiz; real səs (alqış) əl ilə seçilir",
        "variants": [("M09", "Xronoloji: açılış → inkişaf → final"), ("M09", "Ritmik: musiqi vuruşuna kəsim"),
                     ("M09", "Qısa dəvət (15–20 s)")],
        "commands": ["new --type 5", "storyboard", "event-scan", "event-plan --music", "variants", "choose", "render", "verify"],
        "notes": ["Açılış, inkişaf və tamamlanma olmalıdır", "Yavaşlatma yalnız material imkan verəndə (hazırda yoxdur — iddia etmə)",
                  "Musiqi yalnız Freesound CC0"]},
    6: {"name": "Praktik fəaliyyət və ekspert səsləndirməsi", "short": "Fəaliyyət + ekspert səsi", "family": "seminar",
        "approaches": ["M08", "M05"], "status": "partial", "gaps": "addımların görüntü ilə avtomatik eşləşməsi yoxdur",
        "variants": [("M08", "Addım-addım nümayiş"), ("M08+M05", "Fəaliyyət tam kadr, ekspert pəncərədə"),
                     ("M08+M02", "Nümayiş + addım yazıları")],
        "commands": ["add-broll", "storyboard", "variants", "choose", "render", "verify"],
        "notes": ["Danışıq görüntüdəki konkret fəaliyyətlə üst-üstə düşür", "Vacib addım gizlədilmir"]},
    7: {"name": "İş prosesi və kameraarxası", "short": "Kameraarxası", "family": "seminar",
        "approaches": ["M09", "M11"], "status": "partial", "gaps": "səsləndirməli variant (M11) üçün səsə görə kadr düzümü yoxdur",
        "variants": [("M09", "Musiqi ilə proses"), ("M09+M11", "Proses + səsləndirmə"), ("M09", "Qısa (10–15 s)")],
        "commands": ["new --type 7", "storyboard", "event-scan", "event-plan --music", "variants", "choose", "render", "verify"],
        "notes": ["Real proses göstərilir, səhnələşdirilmiş nəticə kimi təqdim edilmir"]},
    8: {"name": "Görüntülər üzərindən səsləndirməli hekayə/reklam", "short": "Səsləndirməli hekayə", "family": "reklam",
        "approaches": ["M11", "M04"], "status": "partial", "gaps": "səsə görə kadrların avtomatik düzülməsi yoxdur (M11)",
        "variants": [("M11", "Səsləndirmə + görüntülər"), ("M11+M04", "Ekspert + tam ekran görüntülər"),
                     ("M11+M02", "Səsləndirmə + əsas fikir yazıları")],
        "commands": ["add-broll", "storyboard", "plan: broll", "render", "verify"],
        "rules": ["source_order", "graphic_numbers_spoken"],
        "notes": ["Təsdiqlənmiş səsləndirmə yenidən sıralanmır", "Stock görüntü sübut kimi təqdim edilmir"]},
    9: {"name": "Nağıl və animasiyalı hekayə", "short": "Nağıl, cizgi", "family": "qrafika",
        "approaches": ["M12"], "status": "ready",
        "variants": [("M12", "Nağıl səhnəsi tam kadr, danışan dairədə"), ("M12", "Yalnız nağıl səhnələri"),
                     ("M12", "Real video + şəffaf obraz (sticker)")],
        "commands": ["tale-plan", "plan", "render", "verify"],
        "notes": ["Obrazlar ardıcıl qalır", "Kitabxanada olmayan obraz uydurulmur", "Üslub storyboardda təsdiqlənir"]},
    10: {"name": "Sürətli, əyləncəli sual-cavab", "short": "Yumorlu sual-cavab", "family": "danisiq",
         "approaches": ["M10"], "status": "missing", "gaps": "M10 şablonu yoxdur — cut + sfx + başlıq ilə əl ilə",
         "variants": [("M10", "Yüngül yumor, sürətli ritm"), ("M10+M02", "Sual ekranda + reaksiya vurğusu"), ("M01", "Sakit")],
         "commands": ["storyboard", "cut", "plan: graphics, sfx", "render", "verify"],
         "notes": ["Tərəddüd, pauza, gülüş məna daşıyır", "Ekspert alçaldılmır, demədiyi fikir yaradılmır"]},
    11: {"name": "İki ekspertin söhbəti", "short": "İki nəfərlik söhbət", "family": "danisiq",
         "approaches": ["M01", "M06"], "status": "partial", "gaps": "bölünmüş ekran yoxdur; kadraj danışana keçir (framefix)",
         "variants": [("M01", "Kadraj danışana keçir"), ("M01+M06", "Fikirlərin qarşılaşdırılması"), ("M01", "Geniş kadr")],
         "commands": ["highlights", "extract", "framefix", "storyboard", "variants", "choose", "render", "verify"],
         "notes": ["Hər iki danışanın konteksti qorunur"]},
    12: {"name": "Hərəkətli kartlar və video-karusel", "short": "Video-karusel, kartlar", "family": "qrafika",
         "approaches": ["M13"], "status": "partial", "gaps": "ekspertsiz kart səhifələri ayrıca alət deyil",
         "variants": [("M13", "Video-karusel (fikir slaydları)"), ("M13", "Bir videoda səhifələr"), ("M13+M03", "Səhifələr + qrafika")],
         "commands": ["carousel-plan", "carousel", "verify"],
         "notes": ["Bir səhifədə bir fikir; oxuma vaxtı verilir"]},
    13: {"name": "Material və ekran üzərində izah", "short": "Ekran/material izahı", "family": "qrafika",
         "approaches": ["M05", "M03"], "status": "partial", "gaps": "pəncərənin materialı örtməməsi avtomatik yoxlanmır",
         "variants": [("M05", "Material tam kadr, ekspert pəncərədə"), ("M05+M03", "Material + izah qrafikası"),
                      ("M04", "Ekspert + tam ekran material")],
         "commands": ["add-broll", "storyboard", "plan: broll pip", "render", "verify"],
         "notes": ["Pəncərə materialı örtmür"]},
    14: {"name": "İştirakçı rəyi və təcrübəsi", "short": "Müştəri rəyi", "family": "reklam",
         "approaches": ["M01"], "status": "ready",
         "variants": [("M01", "Təmiz rəy"), ("M01+M02", "Rəy + əsas fikir yazısı"), ("M01+M04", "Rəy + təlim/xidmət görüntüləri")],
         "commands": ["storyboard", "retakes", "variants", "choose", "render", "verify"],
         "rules": ["graphic_numbers_spoken"],
         "notes": ["Demədiyi nəticə montajla yaradılmır", "Rəyin konteksti qorunur"]},
    15: {"name": "Saytda yerləşdirilən modul təlim dərsi", "short": "Modul təlim dərsi (üfüqi)", "family": "seminar",
         "approaches": ["M14", "M03"], "status": "partial", "gaps": "bölümlər arası eyni üslub avtomatik ötürülmür", "aspect": "16:9",
         "variants": [("M14", "Sakit dərs: başlıq + altyazı"), ("M14+M03", "Dərs + izah qrafikası"), ("M14", "Minimal (altyazısız)")],
         "commands": ["new --aspect 16:9", "storyboard", "retakes", "cut", "plan", "render", "verify"],
         "rules": ["source_order", "horizontal"],
         "notes": ["Hook yoxdur, Reels ritmi tətbiq edilmir", "Üfüqi dərs şaquliyə çevrilmir"]},
    16: {"name": "Qrafika ağırlıqlı izah (motion graphics)", "short": "Motion graphics (data, IT)", "family": "qrafika",
         "approaches": ["M03", "M01"], "status": "ready",
         "variants": [("M03", "Qrafika tam kadr, danışan dairədə"), ("M03", "Qrafika kart kimi danışanın yanında"),
                      ("M01+M03", "Yüngül: yalnız əsas rəqəmlər")],
         "commands": ["mg-scan", "scenes", "plan: broll make", "render", "verify"],
         "rules": ["graphic_numbers_spoken"],
         "notes": ["Qrafikada yalnız danışıqda deyilən rəqəmlər"]},
    17: {"name": "Loqo animasiyası", "short": "Loqo animasiyası", "family": "qrafika",
         "approaches": [], "status": "planned", "gaps": "müştərinin loqo faylı (PNG şəffaf / SVG) gələndə qurulacaq",
         "variants": [], "commands": [], "notes": ["Loqo faylı olmadan loqo çəkilmir/uydurulmur"]},
}

FAMILIES: dict[str, dict[str, Any]] = {
    "danisiq": {"label": "Danışıq videosu", "desc": "kameraya danışıq, sual-cavab, söhbət", "types": [1, 2, 10, 11]},
    "reklam": {"label": "Reklam və rəy", "desc": "hazır mətnli reklam, səsləndirməli reklam, müştəri rəyi", "types": [3, 8, 14]},
    "seminar": {"label": "Seminar, tədbir, dərs", "desc": "seminardan çıxarış, tədbir icmalı, təlim dərsi, proses",
                "types": [4, 5, 15, 7, 6]},
    "qrafika": {"label": "Qrafika və animasiya", "desc": "motion graphics, karusel, nağıl, ekran izahı",
                "types": [16, 12, 9, 13, 17]},
}

GOALS = ["maarifləndirmə", "reklam/satış", "atmosfer", "dəvət/qeydiyyat"]

STATUS_LABEL = {"ready": "hazır", "partial": "qismən", "missing": "alət yoxdur", "planned": "planlaşdırılıb"}


def get(n: int | str) -> dict[str, Any]:
    try:
        return TYPES[int(n)]
    except (KeyError, ValueError):
        raise KeyError(f"naməlum video növü: {n} (1–{max(TYPES)})") from None


def parse_approaches(s: str) -> list[str]:
    out = [x.strip().upper() for x in re.split(r"[+,\s]+", s or "") if x.strip()]
    for x in out:
        if x not in APPROACHES:
            raise KeyError(f"naməlum yanaşma: {x} (M01–M14)")
    return out


def record(n: int, extra: list[int] | None = None, goal: str = "", approaches: list[str] | None = None,
           subtype: str = "", uncertain: str = "") -> dict[str, Any]:
    """Layihədə saxlanan növ qeydi (VIDEO_TYPES.md "Qeyd forması")."""
    t = get(n)
    for e in extra or []:
        get(e)
    return {"type": int(n), "name": t["name"], "extra": [int(e) for e in extra or []], "goal": goal,
            "subtype": subtype, "approaches": approaches or list(t["approaches"][:1]), "uncertain": uncertain}


def rules_for(vt: dict[str, Any] | None) -> list[str]:
    """Növ (+ əlavə növlər) üçün maşın yoxlamaları; rəqəm qaydası hər növdə qüvvədədir."""
    ids = ["graphic_numbers_spoken"]
    if vt:
        for n in [vt["type"], *vt.get("extra", [])]:
            ids += TYPES[n].get("rules", [])
    return list(dict.fromkeys(ids))


def survey() -> dict[str, Any]:
    """Sorğu sualları (AskUserQuestion: sual başına 2–4 seçim + "Other"). Ailə → növ (yalnız lazım olanda) → məqsəd."""
    fam = [{"label": f["label"], "description": f["desc"]} for f in FAMILIES.values()]
    sub = {}
    for k, f in FAMILIES.items():
        opts = [{"label": TYPES[n]["short"], "description": TYPES[n]["name"] + (" — " + STATUS_LABEL[TYPES[n]["status"]]
                                                                                if TYPES[n]["status"] != "ready" else ""), "type": n}
                for n in f["types"] if TYPES[n]["status"] != "planned"]
        sub[f["label"]] = opts[:4]  # 4-dən çoxdursa qalanı "Other" ilə yazılır
    return {"family": fam, "type_by_family": sub, "goal": [{"label": g} for g in GOALS]}


# ---------------------------------------------------------------------------
# Maşın yoxlamaları (verify)
# ---------------------------------------------------------------------------

_NUM = re.compile(r"\d+(?:[ .,]\d{3})*(?:[.,]\d+)?")


def _numbers(text: str) -> set[int]:
    out = set()
    for m in _NUM.finditer(text or ""):
        s = m.group(0).replace(" ", "")
        s = re.sub(r"[.,](?=\d{3}\b)", "", s)
        try:
            out.add(int(float(s.replace(",", "."))))
        except ValueError:
            pass
    return out


def check(rule: str, project: dict[str, Any], video_clips: list[dict[str, Any]], spoken: set[int]) -> tuple[bool, str]:
    """(keçdi?, izah). video_clips — v1 klipləri zaman xətti sırası ilə; spoken — danışıqdakı rəqəmlər."""
    if rule == "source_order":
        last: dict[str, float] = {}
        for c in video_clips:
            if c.get("broll"):
                continue
            m = c.get("media")
            if m in last and c["srcIn"] < last[m] - 0.05:
                return False, "mətnin ardıcıllığı dəyişib (klip əvvəlki hissədən sonra gəlir) — bu növdə hook əvvələ çəkilmir"
            last[m] = float(c["srcOut"])
        return True, "mətnin ardıcıllığı qorunub"
    if rule == "horizontal":
        w, h = project.get("width") or 0, project.get("height") or 0
        return (w > h, f"çıxış üfüqidir ({w}x{h})" if w > h else f"təlim dərsi üfüqi olmalıdır, çıxış {w}x{h}")
    if rule == "graphic_numbers_spoken":
        bad = []
        for c in project.get("clips", []):
            if c.get("track") != "t1":
                continue
            items = c.get("items") or []
            txt = " ".join(str(c.get(k) or "") for k in ("text", "heading", "price", "oldPrice", "note", "keyword", "sub"))
            txt += " " + " ".join(x if isinstance(x, str) else str((x or {}).get("text", "")) for x in items)
            txt = re.sub(r"\b\d{1,2}\s*/\s*\d{1,2}\b", " ", txt)  # slayd sayğacı "2/5" rəqəm iddiası deyil
            bad += [n for n in _numbers(txt) if n not in spoken]
        bad = sorted(set(bad))
        return (not bad, "qrafikadakı rəqəmlər danışıqda var" if not bad
                else f"qrafikada danışıqda olmayan rəqəm(lər): {', '.join(map(str, bad))} — uydurma olmamalıdır")
    raise KeyError(rule)
