# OpenMontage

**MANDATORY: Read [`AGENT_GUIDE.md`](AGENT_GUIDE.md) before responding to ANY user message.**

Do not act on the user's request until you have read AGENT_GUIDE.md.
It contains routing rules that determine your first action based on what the user asked.
Skipping it WILL cause you to take the wrong action.

There are no instructions in this file. All instructions are in AGENT_GUIDE.md.

## AYRA Studio — daimi qayda (Montaj darvazası)

Hər video/montaj tapşırığı `montaj/IS_AXINI.md` → «Montaj darvazası» ilə gedir: müştəri → brend faylları (`python -m montaj.gate start`) → video növü → analiz → `concept.md` → plan → `templates/expert-reels/pro` ilə icra → render → `qc_render --rules` + gözlə baxış → `gate deliver`. Növsüz başlanmır, bir şablon bütün formatlara tətbiq edilmir, darvazadan keçməyən video FINAL adlandırılmır. `.claude/settings.json` hook-ları bunu avtomatik xatırladır (UserPromptSubmit) və təhvil qovluqlarına birbaşa yazmanı bloklayır (PreToolUse).

## AYRA Studio — daimi qayda (Real Visual Asset System)

AYRA Studio üçün hər kreativ dizayn tapşırığında `ayra-visual-research` iş axını (`.claude/skills/ayra-visual-research/SKILL.md`) tətbiq edilməlidir. Mövzu real vizual material tələb edirsə, dizayna başlamazdan əvvəl uyğun, lisenziyalı və keyfiyyətli real material tapılmalıdır. Sadəcə tipoqrafiya və qrafik formalarla kifayətlənmə. Bununla belə, sırf tipoqrafik dizayn daha güclü yaradıcı həll olduqda lazımsız foto əlavə etmə.

## AYRA Studio — daimi qayda (Pinterest Creative Research)

Bütün müştərilər üçün hər cover, post, karusel, story, reklam və Instagram grid dizaynında standart axın: müştəri + mövzu → `ayra-pinterest-research` (Pinterest-də 15–20+ nəticə, vizual analiz, 3–5 referans) → kreativ istiqamət → `ayra-visual-research` (lisenziyalı real material) → dizayn → vizual yoxlama → nəticə. İstifadəçidən referans istənmir. Pinterest şəkilləri yalnız referansdır, yekun dizayna qoyulmur və kopyalanmır.

## AYRA Studio — daimi qayda (Creative Intelligence System)

Bütün müştərilər üçün hər dizayn tapşırığı `ayra-creative-intelligence` skill-i ilə idarə olunur: BRAND PROFILE → MARKETING STRATEGY → CREATIVE DIRECTION → PINTEREST RESEARCH → DESIGN ARCHITECTURE → ASSET CURATION → DESIGN → VISUAL CRITIQUE → REFINEMENT → FINAL EXPORT. Mərhələlər arasında təsdiq gözlənilmir; sual yalnız çatışmayan müştəri faktı və ya brend istiqamətini dəyişən qərar üçün verilir. Dizayndan əvvəl Creative Idea Engine (insight → məqsəd → big idea → hook → treatment) və art direction brief məcburidir; araşdırma çox mənbəlidir (Google, YouTube, Pinterest, Behance, Meta Ad Library, elmi mənbələr) və tapıntılar FAKT/MÜŞAHİDƏ/HİPOTEZ/TEST kimi işarələnir; final Creative Review Board-dan (brend menecer, kreativ direktor, dizayner, auditoriya+ekspert) keçir. İstifadəçiyə yalnız müstəqil tənqiddə hər meyarı ≥ 8 olan nəticə təqdim olunur. Hər müştərinin öz `instagram-clients/<m>/brand_profile.md` faylı var; istifadəçinin düzəlişləri oranın «Qərarlar jurnalı»na yazılır və bir müştərinin üslubu başqasına keçmir.

## AYRA Studio — daimi qayda (müştəri master faylı və istehsal modeli)

Müştəri qovluğunda `instagram-clients/<m>/MASTER_BRAND_FILE.md` varsa, o müştərinin HƏR işindən əvvəl ilk o oxunur: mövqe, qadağalar, aktiv xidmətlər, aylıq istehsal modeli, ID sistemi və təsdiq qaydaları oradadır. Paylaşım ardıcıllığı `ayra-growth-strategist` § Smart Content Planner qaydaları ilə qurulur. Çəkiliş linki/qovluğu gələndə həmin fayldakı avtomatik zəncir (analiz → montaj → cover → caption → QC → ID ilə qovluğa) ayrıca tapşırıq gözləmədən icra olunur. Bir müştərinin istehsal modeli başqasına tətbiq edilmir. İcazəsiz heç nə paylaşılmır, planlanmır və hesabda dəyişiklik edilmir. Müştəri adı və şəxsi məlumat bu repoya yazılmır (müştəri qovluqları gitignore-dadır).
