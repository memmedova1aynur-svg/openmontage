---
name: cinematic-editorial
description: «Cinematic Editorial Storytelling» — öyrənmə elmi üzrə təlim mentorunun (müştəri kodu «X») təsdiqlənmiş montaj stili. Danışıq sənədli hekayəyə çevrilir: real arxiv foto, muzey/tarixi material, kontekst B-roll, editorial tipoqrafiya, zərif motion. İstifadə et: «cinematic editorial», «sənədli montaj», «X stili», «təlim mentoru videosu», «arxiv foto ilə izah», bu müştəri üçün yeni video istənəndə.
---

# Cinematic Editorial Storytelling (müştəri «X»)

Müştəri adı repoda yazılmır (açıq fork). Müştəri qovluğu `instagram-clients/<müştəri>/` (gitignore); xam çəkilişlər Drive-dan.
Mühərrik: `templates/expert-reels/cine/` (`eng.py` səhnə mühərriki, `sfx.py`, `g10.py` nümunə).

## Mövqe
- Titul: **Təlim mentoru.** Motivasiya spikeri YOX — öyrənməni təhlil edən, mifləri araşdıran, üsul göstərən mentor.
- Yanaşma: **Sual → təhlil → nümunə → nəticə.** Ton: «Bəs niyə belədir?» (araşdırma izahı).
- Eyni agentlikdə öyrənmə mövzusunda başqa ekspert də ola bilər — brendlər QARIŞDIRILMIR: elmi baza ortaq ola bilər, başlıq/vizual dil/ssenari/montaj ayrıdır; eyni mövzu eyni həftədə düşürsə təqdimat fərqli olur.

## Əsas prinsip
- Sadə «talking head + altyazı + kart» YOX. Danışıq vizual hekayəyə çevrilir: izləyici dinlədiyini görür.
- Birləşmə: kinematik talking head · sənədli montaj · real foto · tarixi arxiv · kontekst B-roll · zərif motion · animasiyalı tipoqrafiya · vizual metafora · peşəkar səs dizaynı.
- Vizual hekayəni mətn özü müəyyən edir; hər cümləyə təsadüfi şəkil qoyulmur.

## Avtomatik analiz (soruşmadan)
Mətndən tap: A) insanlar (filosof, alim, tədqiqatçı) B) məkanlar C) tarixi dövr/hadisə D) elmi anlayışlar E) real həyat situasiyaları.

## Material prioriteti
1 müştərinin real kadrları · 2 etibarlı arxiv foto · 3 muzey/tarixi kolleksiya · 4 real foto · 5 lisenziyalı sənədli video · 6 real B-roll · 7 motion graphics · 8 vizual metafora.
- İngiliscə açar sözlərlə axtar («Socrates bust», «Ancient Rome»).
- «Yaddaş» → təsadüfi beyin şəkli yox; konkret prosesi göstər.
- Müasir foto qədim dövrün orijinalı kimi təqdim edilmir.
- Yalnız icazəli material (Wikimedia Commons PD/CC, Met Open Access və s.); mənbə + lisenziya `menbeler.json`-da. BY-SA materialdan qaç.

## Qərar mühərriki (hər fikir bloku)
A danışan qalır (şəxsi fikir, nəticə, müraciət, giriş, yekun, CTA) · B real foto/arxiv · C kinematik B-roll · D motion graphics · E editorial tipoqrafiya · F hibrid (spiker + foto/qrafik).

## Ritm və hərəkət
- Vizual dəyişiklik yeni məlumat/keçid/vurğu üçündür; «hər 2 s» qaydası yoxdur.
- Foto animasiyası: yavaş push-in/pull-out, pan, Ken Burns, yüngül parallax. Heykəl/tarixi üz danışdırılmır, süni hərəkət yox.
- Spiker əsas simadır: başlanğıc, əsas iddia, güclü sual, şəxsi fikir, nəticə, təlimə dəvət — spiker görünür. Tarixi/izah hissələrində foto/arxiv/B-roll daha geniş.
- Nümunə ardıcıllıq (şablon deyil): spiker yaxın plan → mövzu təhsil görüntüsü → «Yunanıstan/Roma» memarlıq/muzey → «Uzaq Şərq» → filosof heykəl/portreti (ad çəkildikcə) → sənaye inqilabı arxivi → spiker → təlim + CTA.

## Vizual dil
- Rəng: təsdiqli HEX sənəddə yoxdur → uydurma; mövcud postlardan: tünd yaşıl `#0F3B2C`, yarpaq yaşılı `#6CC57E`, ağ. **Laym rəng qadağan.** Profil şəkillərində yaşıl fon yox.
- Üstün: güclü tipoqrafiya, editorial kompozisiya, real foto/video, boşluq, məzmuna xidmət edən motion.
- Qadağan: şablon AI görünüşü, lazımsız 3D, hər postda eyni kompozisiya, mənasız ikonlar, süni insan təsvirləri, eyni animasiya/altyazı effekti, əlaqəsiz stok, şablon motivasiya.

## Məzmun qaydaları
- Uydurma fakt/statistika/araşdırma/müəllif/tarix YOX. «Alimlər sübut edib» kimi ifadə yox. Korrelyasiya ≠ səbəb. Öyrənmə piramidası faizləri yalnız MİF kimi.
- Hook ilk 1–3 s; hər videoya eyni «Bilirdinizmi?» yox; clickbait yox.
- Mövzu bankı: Mif/həqiqət · Araşdırma nə göstərir (Roediger & Karpicke, spacing, interleaving, desirable difficulties, consolidation, fluency illusion) · Effektiv metodlar (Feynman, blurting, active recall, Cornell, chunking, Pomodoro) · Vaxt/planlama (planning fallacy, time blocking, Zeigarnik — şişirtmədən) · Ən çox edilən səhvlər · Düşündürən suallar.
- Artıq işlənmiş (təkrarlama): yuxu və yaddaş, yetkin öyrənmə, fasiləli təkrar, başlığı suala çevir, tanıyıram–xatırlayıram, oxu–xatırla–yoxla, McCollough, təxirəsalma, yaşda yadda saxlama.

## Texniki
- Keçid sistemi, səs təmizliyi (noisereduce + gate; afftdn yox), kadraj, rəng (təbii), semantik kəsim (söz ortasında kəsim yox), final yoxlama.
- Musiqi: minimal cinematic / documentary ambient, CC0/lisenziyalı sakit instrumental. (Keçmişdə bir müddət «musiqisiz» tələbi olub — yeni işdə agentlikdən təsdiqlə.)
- SFX: yalnız peşəkar küy əsaslı («pro» dəsti); tonal «uyu» səsləri qadağan.
- Ölçülər: Reels/Story 1080×1920, post 1080×1350.
- Montaj darvazası: `python -m montaj.gate start <müştəri> <video> --type N` → concept → kəsim → render → `qc_render.py` → `gate deliver`.
