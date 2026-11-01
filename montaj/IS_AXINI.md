# Əsas iş axını: Drive linki → yekun MP4 (davamlı təlimat)

Bu fayl istifadəçinin təsdiqlədiyi **əsas** iş axınıdır (sorğu → Drive linki → analiz → 3 storyboard → rəng/musiqi → MP4) və `SESSIYA_TELIMATI.md`-dən üstündür.
İstifadəçi yalnız **Drive linkini** verir — montajın hamısı Claude-da edilir və bir dəfəyə təhvil verilir. Redaktor paneli
istifadə olunmur: linkini göndərmə, təklif etmə (yalnız istifadəçi açıq istəyəndə — faylın sonundakı "Redaktor paneli").

Hədəf: video ilk dəfədən hazır olsun, əlavə düzəliş tələb etməsin. İstifadəçi ilə yalnız **iki dəfə** əlaqə:
(1) sorğu, (2) **bir qərar mesajı** — storyboard variantları + kadraj (əvvəl/sonra) + rəng variantları + musiqi
nümunələri birlikdə göndərilir, istifadəçi bir cavabla seçir (məs. “B, rəng A, musiqi 2”). Sonra yalnız **yekun MP4**.
Ara düzəliş raundları təklif etmə.

Montaj qərarlarının prinsipləri (niyə kəsirik, plan ölçüsü, uyğunluq, ritm, J/L-cut, etika): [`KINO_DILI.md`](KINO_DILI.md).

## Addımlar

1. **Əvvəl qısa sorğu — Drive linkindən ÖNCƏ.** İstifadəçi yeni video istəyəndə (və ya link sorğusuz gəlsə)
   **bir** sorğu aç (`AskUserQuestion`): müştəri, video növü, məqsəd, arzu olunan müddət, xüsusi istək.
   Yalnız məlum olmayan sahələri soruş. **Növ sualları reyestrdən:** `python -m montaj.session types --survey` —
   əvvəl ailə (Danışıq / Reklam və rəy / Seminar, tədbir, dərs / Qrafika və animasiya), növ ailədən aydın deyilsə
   ikinci sual (həmin ailənin növləri), məqsəd (maarifləndirmə / reklam / atmosfer / dəvət). Növ materialdan
   aydınlaşacaqsa soruşma — analizdən sonra `set-type`. Statusu "qismən"/"alət yoxdur" olan növdə nəyin əl ilə
   ediləcəyini sorğudan sonra bir cümlə ilə de (`types <N>` → "çatışmır"); hazır kimi təqdim etmə.
   - Profil adlarını `ls templates/expert-reels/experts/` ilə gör; yalnız seçilən müştərinin faylını oxu
     (profildə olan məlumatı yenidən soruşma). Müddət verilməyibsə — danışığa görə özün təyin et.
   - **Müştəri hələ çəkməyibsə** (və ya yeni növ/ilk çəkiliş): `types <N> --shoot --client "<ad>"` — çəkiliş tövsiyəsini
     (planlar, 4K/fps, HDR, fokus kilidi, işıq, mikrofon, 10 s otaq sükutu, fon/geyim) olduğu kimi göndər; təkrar müştəriyə
     `--compact`. Yaxşı çəkiliş sistemin imkanlarını açır (4K → virtual multikamera, 60 fps → yavaşlatma).
   - Sorğudan sonra Drive linkini istə.
2. **Drive linki gəlir.** Asılılıqlar yoxdursa `bash scripts/cloud-setup.sh`.
   `export MONTAJ_DATA_DIR=$HOME/montaj-data MONTAJ_OUT_DIR=$HOME/montaj-data/out`
3. **Analiz.** `python -m montaj.session new --title "<ad>" --link "<link>" --client "<profil>" --type <N> [--extra <N>]
   [--goal ...] [--subtype ...]` (növ — `types`; qarışıq videoda əsas növ + `--extra`; növ aydın deyilsə `--uncertain "<nə, niyə>"`;
   növün öz formatı varsa — məs. 15 modul dərs → 16:9 — `--aspect` verilməsə o götürülür; sonradan: `set-type <pid> <N>`)
   → `storyboard <pid>` (sonunda **material yoxlaması** çap olunur — ayrıca: `intake <pid>`: dəyişkən/qarışıq fps, HDR,
   ölçü və keyfiyyət ehtiyatı, səsin partlaması və zəifliyi, qaranlıq/çox açıq, fokus, titrəmə, kliplər arası ağ balansı/işıq
   fərqi; `!` olanları qərar mesajında bir cümlə ilə de — məs. "səs partlayır, tam düzəlmir"). Transkripsiya yerli faster-whisper `large-v3-turbo` ilə, nəticə keşlənir
   (mənbə/parametr dəyişməyibsə təkrarlanmır). Ölçü, kodek, HDR-i qısa qeyd et.
   Transkripti oxu: təkrar cümlələri, alınmayan cəhdləri, yarımçıq fikirləri tap. Köməkçi: `retakes <pid>` — ardıcıl
   təkrar/yarımçıq cümlələri və hazır `cut` təklifini göstərir (sonrakı, tam cəhd saxlanılır); yenə də özün oxuyub qərar ver.
   Müştərinin profilində `glossary` varsa (`terms`, `fixes`) — `new --client` Whisper-ə terminləri verir, `plan` düzəlişləri tətbiq edir.
   Çıxarmaq üçün: `cut <pid> [media:]başla-son …` (sərhəd səsin ən sakit yerinə çəkilir; söz kəsilmir;
   şübhəli sərhəddə material saxlanılır, çıxışda ŞÜBHƏLİ yazılır) və ya `edit --exclude N`.
2a. **B-roll / araya kadr materialı** (istifadəçi əlavə video/şəkil göndərsə — Drive linki və ya fayl):
   `add-broll <pid> --link <..> [--file <..>]` → material danışıq analizinə və kəsimə düşmür.
   Storyboard variantlarında harada işlədiləcəyini təklif et (planda `broll`):
   - `{"name": "<fayl>", "mode": "cover", "at": 6.0, "dur": 2.0, "from": 0}` — əsas videonun üstündə tam kadr;
     danışıq, altyazı, kartlar davam edir (məhsul, nümunə, emosiya kadrı üçün).
   - `"mode": "pip"` — küncdə kiçik pəncərə, mənbə nisbətində; `x`/`y` verilməsə **üzü və altyazını örtməyən**
     yer avtomatik seçilir (`scale` standart 0.42).
   - `"mode": "insert"` — araya kadr: əsas video **ən yaxın təbii pauzada** dayanır (söz və altyazı sözü bölünmür),
     kadr öz səsi ilə oynayır (`volume`, 0 — səssiz), sonra danışıq davam edir (gülməli reaksiya, keçid üçün).
   Şəkil də ola bilər (istənilən müddət). Rəng şablonu B-roll-a da tətbiq olunur. Material verilməyibsə B-roll uydurma.
3c. **Arxa fonun dəyişdirilməsi — yalnız istifadəçi istəyəndə** (yerli, pulsuz: MediaPipe insan seqmentasiyası):
   - Variantları müqayisə: `bg <pid> --preview --spec '{"mode":"blur"}' --spec '{"mode":"color"}' --spec '{...}'` →
     `arxafon.jpg` (orijinal + hər variant 3 kadrda; layihə dəyişmir) — qərar mesajına əlavə et.
   - Rejimlər: `blur` (bulanıq fon, `strength` 5–60 — ən etibarlısı, tövsiyə et), `color` (istənilən rəng və ya qradiyent:
     `color`, `color2`, `direction` vertical/horizontal/radial; rəng verilməsə müştərinin brend rəng ailəsi), `image` (şəkil faylı),
     `video` (video fon, dövrə ilə), `scene` (Claude-un səhnəsi: `kind`, `props` — `scenes` kataloqu). Seçimlər: `dim` 0–0.8
     (fonu qaraltmaq), `keepBelow` 0–1 (bu hündürlükdən aşağı orijinal qalır — masa, əllər havada qalmasın), `feather`, `smooth`,
     `model` accurate|fast.
   - Tətbiq: `bg <pid> --mode color --color '#F4EDE4' --color2 '#D9C8B4' --keep-below 0.86` (və ya `--spec '{...}'`) →
     törəmə video (orijinal dəyişmir, səs orijinaldan, kadr sayı eyni); render onu götürür. Geri: `bg <pid> --off`.
     ~2 dəq / 30 s (1080x1920). "kənar titrəməsi" çap olunur: >0.06 olsa `smooth`-u artır və ya `blur` təklif et.
   - **Təbii fon (interyer/studiya şəkilləri) — dəyişdirildiyi hiss olunmasın.** Fon kitabxanası: `bg-lib add <şəkillər> [--tag ...]`,
     `bg-lib list` (repoda: `montaj/backgrounds`, teqlər `ayaqüstə` / `oturan` / `studiya` / `interyer`; yeni fon əlavə edəndə
     duruş teqini qoy və commit et). `bg <pid> --auto --preview` — videonun otaq
     işığına (parlaqlıq, rəng temperaturu) ən uyğun 3 fon; və ya `--lib <id>`. image/video/scene üçün avtomatik:
     rəng/parlaqlıq uyğunlaşması (fon orijinal otağın işığına yaxınlaşır, insanın üzünə toxunulmur), fokus (detallı fon çox
     bulanır), kənar işığı, kameranın dənəvərliyi, **masa avtomatik tapılır — oturan şəxsdə masa və əllər orijinal qalır**,
     **ayaqüstə (tam boy) şəxsin ayağı altında yumşaq kölgə**. Çıxışda duruş və masa xətti çap olunur — yoxla. Əl ilə:
     `bgZoom`, `bgX`, `bgY` (fonun miqyası/yeri), `focus`, `wrap`, `grain`, `harmonize`, `keepBelow`, `shadow` (`--spec` JSON).
     Ayaqüstə şəxs üçün döşəməsi görünən fon (studiya, işıq dairəsi, boş otaq) seç; oturan üçün divar/rəf planı.
   - Məhdudiyyət (dürüst de): saç ucları, sürətli əl hərəkəti, fonla eyni rəngli geyim kənarda səhv verə bilər; ən təmiz nəticə
     yaşıl ekranla. **Etik qayda:** ekspertin olmadığı real məkanı (başqa ofis, ölkə) həqiqi kimi göstərmə — brend rəngi,
     qrafika, bulanıq fon normaldır.
3b. **Arxa səsin təmizlənməsi — HƏR videoda yoxlanır.** `voice-clean <pid>` (standart `auto`): kafe uğultusu,
   uzaq danışıq, çəngəl-bıçaq, uzaqdan musiqi azaldılır; **danışanın səsi qorunur** (zəiflətmə ≤20 dB, danışıq
   səviyyəsi orijinala bərabərləşdirilir, sinxron dəyişmir). Arxa səs azdırsa (studiya) özü tətbiq etmir.
   Orijinal dəyişmir; yalnız danışıq qatı təmizlənmiş nüsxəni işlədir (musiqi, SFX, B-roll səsi toxunulmaz).
   Təmizlənibsə `ses_evvel_sonra.m4a`-nı qərar mesajına əlavə et. Yaxında danışan başqa adamın səsi də danışıqdır —
   tam silinmir, bunu de. Model (DeepFilterNet3) internetdən endirildiyi üçün ilk işə salmada icazə soruşula bilər.
2f. **Nağıl və cizgi videoları** (VIDEO_TYPES növ 9 / M12 — obrazlar ardıcıl, üslub storyboardda təsdiqlənir,
   olmayan imkan iddia edilmir):
   - Obraz kitabxanası (`tale.tsx`, flat/sevimli üslub): **tülkü, dovşan, ayı, pişik, uşaq** — nəfəs, göz qırpma, danışma,
     əl yelləmə, tullanma, yan tərəfdən giriş. Fonlar: `forest`, `meadow`, `night`, `house`, `plain` (müştəri rəngi).
   - `tale-plan <pid>`: danışıqdakı obraz və məkanlardan səhnələr (`tale_plan.json`): danışan obraz danışır ("dedi"), sevinən
     tullanır, salamlaşan əl yelləyir; obraz video boyu eyni yerdə və görünüşdə; başlıq mətni danışıqdan.
     Kitabxanada olmayan obraz (canavar, əjdaha, nənə…) **uydurulmur** — `_review`-da; istifadəçiyə mövcud obrazla əvəz
     etməyi və ya səhnəsiz saxlamağı təklif et.
   - Rejimlər: `cover_pip` (nağıl səhnəsi tam kadr, danışan səmada dairədə — `x: 0.07, y: 0.33`), `cover`; real video üzərində
     obraz: `{"make": {"kind": "tale_char", "props": {"transparent": true, "char": {"kind": "fox", "action": "wave"}}}, "mode": "sticker"}`
     — şəffaf (ProRes 4444) obraz danışanın yanında (standart sol tərəf, altyazının üstü).
   - Real görünüşlü obraz (fotorealist) pulsuz deyil — təsdiqsiz ödənişli xidmət qoşma; cizgi üslubunu təklif et.
2g. **Video karusel** (Instagram: bir paylaşımda 2–10 qısa video slayd, 4:5) — əsas montaj təsdiqlənəndən sonra:
   - `carousel-plan <pid>` → `out/<pid>/carousel.json`: slayd = bir fikir (danışıqdakı "birincisi, ikincisi…, sonuncu" və ya
     pauzalar; yoxdursa cümlə sərhədlərində 3–7 bərabər hissə). 1-ci slayd örtükdür (hook), danışıqda çağırış varsa sonuncuda
     CTA kartı. Qısa hook (<2 s) növbəti fikirlə birləşir; slaydlar üst-üstə düşmür.
   - Başlıqlar **yalnız danışıqdan** (qısaldılmış) — `_review`-u oxu, ASR səhvini düzəlt, başlığı redaktə et (mənanı dəyişmə).
   - `carousel <pid> <carousel.json>` → `out/<pid>/carousel/slide_01.mp4…` (1080x1350, hər biri ≤60 s), `ortuk.jpg`,
     `karusel.jpg` (yoxlama üçün yan-yana). Hər slaydda sayğac "2/5", başlıq, söz-söz altyazı (y 0.84), müştəri rəngi;
     örtükdə böyük başlıq + "Sürüşdürün →". Əsas montaj dəyişmir (9:16 kartları slayda keçmir).
   - Yoxlama: `karusel.jpg`-ə bax (üz, başlıq, altyazı üst-üstə düşmür), sonra istifadəçiyə slaydları sıra ilə göndər.
2h. **Tədbir icmalı və kameraarxası — M09** (növ 5, 7; görüntülər musiqi ritmi ilə, danışıq yoxdur):
   - `new --type 5` (və ya 7) — tədbir kadrajı avtomatik; bütün klipləri/şəkilləri bir layihəyə əlavə et → `storyboard`.
   - `event-scan <pid>` → `shots.json` + `kadrlar.jpg`: hər kadr (avtomatik bölünür, xronoloji — çəkiliş vaxtı/fayl adı)
     kəskinlik, işıq, titrəmə, üz ilə qiymətləndirilir; zəif kadr (bulanıq/qaranlıq/titrək) qırmızı və seçilmir.
   - Musiqini Freesound-dan (yalnız CC0) seç → `event-plan <pid> --music <fayl> [--target 30]` → `event_A/B/C.json`:
     A xronoloji (4 vuruşluq kadrlar), B ritmik (2 vuruş), C qısa dəvət (15–20 s). Quruluş: açılış (ümumi plan, 2 qat uzun)
     → inkişaf (xronoloji, hər kadrın ən kəskin/sakit hissəsi) → final (uzun son kadr). Kəsimlər vuruşlara düşür
     (±20 ms), musiqi vuruşdan başlayır, sonda 2 s sönür; görüntünün öz səsi söndürülür (`liveSound`).
   - `_review`-da real səs namizədləri (fondan yüksək — alqış/gülüş ola bilər): dinlə, saxlamaq üçün planda
     `"liveSound": {"volume": 0, "keep": {"e5": 0.8}}` (kart id). Rəng üçün plana `"look"` əlavə et.
   - `variants <pid> event_A.json event_B.json event_C.json` → qərar mesajı → `choose` → `render` → `verify`.
   - **Yavaşlatma:** material ≥50 fps-dirsə (60 fps çəkiliş) final kadr avtomatik 0.5x yavaşlayır (`--slowmo auto|on|off`) —
     yalnız real kadrlarla, kadr uydurulmur. 30 fps materialda hamar yavaşlatma yoxdur — istifadəçiyə de, növbəti dəfə 60 fps.
     Başqa an üçün: `slowmo <pid> --media <id> --from a --to b [--speed 0.5]` → törəmə media, planda B-roll `"media"` kimi.
   - Yoxdur (iddia etmə): şəkillərdə hərəkət (Ken Burns), kadrın məzmununu tanıma (sertifikat, alqış) —
     açılış/final xronologiya və ümumi plana görə seçilir; variant şəklinə baxıb yoxla. Dəvət mətni (tarix, yer) yalnız istifadəçidən.
2i. **Sürətli, əyləncəli sual-cavab — M10** (növ 10): `new --type 10` → `storyboard` → `qa-plan <pid>` → `qa_A/B/C.json`:
   A yüngül yumor (sual səsi + sual yazısı yuxarıda, "pop", gülüş anında yüngül yaxınlaşma), B sual yalnız yazı ilə (sual səsi
   çıxır — hər cavab tək başına anlaşılmalıdır), C sakit (M01). Ölü pauza çıxır, reaksiya (gülüş, səsli pauza) qalır; cavablar
   yenidən sıralanmır. Sual: sual işarəsi / sözü / ədatı (“gəlmisənmi”, “hazırsan mı”; “kimi”, “elmi” sual deyil) və kadrarxası
   səs (kadrdakı şəxsin ağzı tərpənmir). `_review`-da hər sual-cavab: sual mətnində ASR səhvini düzəlt (yazı danışıqdandır);
   "kadrdakı şəxs özü soruşur" qeydi varsa ritorik ola bilər — sual-cavab deyilsə bu planları seçmə. Sonra `variants` → `choose`.
   Ekspert alçaldılmır, demədiyi fikir yaradılmır.
2j. **İki nəfərin söhbəti** (növ 11; iki nəfər BİR kadrda): seçilmiş hissə tətbiq olunandan sonra (`choose`/`apply`):
   - `duo <pid> --mode switch` — kadraj danışana keçir (ağız hərəkəti; ASR iki nəfəri bir cümləyə birləşdirsə də ~2 s hissələrlə
     yoxlanır; 1.5 s-dən qısa növbə birləşir, kəsim sözlər arasındakı boşluğa düşür). Danışma payı çap olunur.
   - `duo <pid> --mode split` — bölünmüş ekran (9:16): yuxarıda soldakı, aşağıda sağdakı şəxs, ortada nazik xətt, altyazı ortada.
     Reaksiyalar itmir — mübahisə/qarşılaşdırma (M06) üçün yaxşıdır.
   - Kadrda iki nəfər tapılmasa aydın xəta verir. İki ayrı kameranın sinxronu hələ yoxdur — iddia etmə.
2e. **Motion graphics** (data, IT, analitika — qrafika ağırlıqlı):
   - Qrafik səhnələr (`session scenes`, `mg_*`): `mg_bar` (sütun), `mg_line` (zaman üzrə xətt), `mg_donut` (faiz),
     `mg_compare` (iki dəyər), `mg_steps` (proses/yol xəritəsi), `mg_code` (kod/terminal), `mg_kpi` (2–4 rəqəm). Müştəri rəngində,
     rəqəmlər Azərbaycan yazılışı ilə (1 200; 4,5).
   - `mg-scan <pid>`: danışıqdakı rəqəmlər (vaxtla, "2022-ci", "iyirmi beş" də) və uyğun səhnə təklifi. **Qrafikada yalnız
     danışıqda deyilən rəqəmlər** — rəqəm yoxdursa rəqəmsiz səhnə (mg_steps, mg_code, checklist, timeline).
   - Rejim `"mode": "cover_pip"`: səhnə bütün kadrı tutur, danışan sol-aşağıda dairədə qalır (üz hissəsi), danışıq və altyazı
     davam edir (`size`, `x`, `y` ilə dəyişmək olar). Motion graphics variantında səhnələr ardıcıl gəlir, aralarda danışan tam kadrda.
2d. **Seminar və uzun çıxış** (VIDEO_TYPES.md, növ 4 — hissə kontekstsiz anlaşılmalı, səbəb əlaqəsi təhrif olunmur):
   - `highlights <pid> [--min 20 --max 75 --top 8]`: müstəqil qısa hissə namizədləri — cümlə başında başlayır, fikir sonunda bitir;
     əvvəlki kontekstə bağlı ("bu", "ona görə", "yəni"…) və təşkilati (salam, sual-cavaba keçid, "sonra danışarıq") başlanğıclar
     seçilmir; bal və səbəb göstərilir. **Təklifdir** — transkripti oxu, istifadəçiyə 3–6 hissəni qısa izahla təklif et.
   - `extract <pid> <media>:<başla>-<son> --title ".."`: seçilən hissə ayrıca layihə olur (eyni orijinal — hard link, eyni analiz —
     təkrar transkripsiya yox, müştəri/rəng/format ana layihədən). Sonra hər hissəyə adi iş axını (retakes/cut, framefix,
     voice-clean, looks, variants, render).
   - Kadrda bir neçə nəfər varsa `framefix` **danışan şəxsi** (ağız nahiyəsindəki hərəkət) tapıb kadrajı ona qurur; aydın deyilsə
     hamısını kadra salır və bunu deyir.
   - 16:9 çəkilişdən 9:16 kəsim kiçik ölçü verir (1080p → 608x1080). Standart: böyütmə yoxdur. İstifadəçi istəsə
     `new ... --size 1080x1920` (yumşalma `render` çıxışında bildirilir). Mümkünsə 4K və ya şaquli çəkiliş məsləhət gör.
2c. **Reklam videoları** (xidmət, təlim, məhsul) — `templates/expert-reels/VIDEO_TYPES.md` → "Reklam üçün ayrıca qayda":
   - `ad-scan <pid>`: danışıqdan təklif faktları (təklif növü, qiymət — köhnə/yeni, endirim, tarix, yer sayı, çağırış və açar söz,
     faydalar) vaxtla. Danışıqda olmayan heç nə əlavə edilmir (qiymət/tarix/nəticə/çağırış UYDURULMUR).
   - `ad-plan <pid>`: 3 variant (`ad_plan_A/B/C.json`): A təmiz + vurğu (M01+M02), B qrafik izah — fayda siyahısı (M03),
     C dinamik — Claude-un B-rollu + punch-in (M04). Ortaq: qiymət kartı (`offer`), nişan (`badge`: tarix/yer), çağırış (`cta`:
     "Şərhlərdə yazın" + açar söz). Kartlar avtomatik **üzün altına** yerləşir (yer azdırsa kiçilir, sığmırsa başın üstünə).
   - **Cümlə ardıcıllığı dəyişmir**, hook əvvələ çıxarılmır; struktur dəyişikliyi yalnız ayrıca təklif + təsdiqlə.
   - Plan fayllarındakı `_review` siyahısını yoxla: avtomatik qısaldılmış mətnləri danışığa sadiq qalaraq redaktə et, sonra `variants`.
   - Qrafika növləri planda da işlədilə bilər: `{"type": "offer", "heading", "oldPrice", "price", "note"}`,
     `{"type": "cta", "text", "keyword", "sub"}`, `{"type": "badge", "text"}`.
2b. **Claude-un hazırladığı B-roll** (istifadəçi material göndərmir — hamısını Claude hazırlayır):
   `scenes` — şablondakı animasiyalı səhnələr (siyahı, statistika, chat, zaman xətti, telefon, eskiz, illüstrasiya,
   kollaj və s., ~40). Planda: `{"make": {"kind": "checklist", "props": {...}}, "mode": "cover"|"insert", "at": .., "dur": ..}`
   — səhnə müştərinin rəng ailəsində render olunur (keşlənir), B-roll kimi qoyulur; variantlar önizləməsində görünür.
   - **Səhnədəki mətn, rəqəm, siyahı YALNIZ danışanın dediyindən** (transkriptdən) götürülür; statistika, fakt,
     vəd uydurulmur. Danışıqda rəqəm yoxdursa `stat`/`bg_number` işlətmə.
   - Səhnələrdə `times`/`at` — klipin öz başlanğıcından saniyələr (0-dan).
   - Hər storyboard variantında 0–3 B-roll; danışanın üzü ən vacib anlarda (hook, CTA) örtülmür.
   - Ayrıca sınaq: `make-broll <pid> --kind .. --props '{..}' --still`.
3a. **Kadraj düzəlişi — HƏR videoda məcburi.** `framefix <pid>`: əyrilik fondakı düz xətlərdən ölçülüb düzəldilir
   (0.4°–6°), üz/obyekt ortalanır, baş üstü boşluq təbii olur; ümumi yaxınlaşma ≤1.12x (görüntü yumşalmasın —
   lazım olsa ortalama qismən olur). Nəticə qaralamaya yazılır, variantlar və yekun montaj onu işlədir;
   `kadraj.jpg` (orijinal / düzəldilmiş) qərar mesajına əlavə olunur. Ölçülə bilməyəni (xətt yoxdur, üz yoxdur)
   düzəldilmiş kimi təqdim etmə. Əl kamerasının titrəməsi/hərəkəti izlənmir (stabilizasiya yoxdur).
4. **Üç vizual storyboard.** `storyboard` çıxışının sonunda növün 3 variantı (A/B/C yanaşmaları), qaydaları və
   müştərinin son seçimləri (`history`) görünür — variantları buna görə qur, son videonun giriş/qutu/effekt ardıcıllığını
   təkrarlama. Hər planda `"approach": "M01+M02"` yaz (tarixçəyə düşür). Hər variant üçün `plan_A.json`, `plan_B.json`, `plan_C.json` yaz və
   `variants <pid> plan_A.json plan_B.json plan_C.json` → `storyboard_variantlari.jpg` (real kadrlar üzərində
   qrafika ilə) + `variant_X.mp4` (540p önizləmə). Şəkli göndər + hər variant üçün 1–2 sətir izah.
   - Variantlar **giriş, ritm, başlıq, məlumat kartları və vizual təqdimat** baxımından həqiqətən fərqlənsin
     (məs. A: sakit, söz-söz altyazı + az kart; B: güclü hook başlıq + bölmələr + punch-in; C: siyahı/kart
     ağırlıqlı, məlumat yönümlü). Yalnız rəng dəyişərək variant yaratma.
   - Planda `"title"`, `"storyboard": {"exclude": [..], "order": [..], "text": {"1": ".."}}` (giriş/sıra fərqi),
     `captions`, `graphics`, `zooms`, `sfx`.
   - **Davamlılıq + müxtəliflik** (bütün müştərilər, istifadəçi qaydası): videolar bir-birinin davamı kimi — eyni rəng ailəsi,
     oxşar ruh; amma kopya yox. `storyboard` çıxışında "bu video üçün təklif" sətri var (son videolardan fərqli ton — əsas /
     açıq / tünd / solğun / ailədə krem varsa krem —, altyazı üslubu qutu/kontur, yazı girişi): planlara `"variation": {...}`
     kimi qoy (variantlardan biri təklifi, digərləri yaxın alternativ ola bilər). Tamamilə fərqli üslub təklif etmə. `choose`
     tonu, altyazı üslubunu və animasiyanı tarixçəyə yazır — növbəti təklif onlardan fərqlənir.
   - **J/L-cut**: planda `"jl": {"auto": true, "lead": 0.25}` — fərqli kameralar (media) arasında görüntü səsdən 0.25 s əvvəl
     keçir (səs yerində); əl ilə `"cuts": {"<video klip id>": 0.3 (J) | -0.3 (L)}`. Eyni kamerada tətbiq olunmur (dodaq
     sinxronu). Danışıq kəsimində 12 ms səs keçidi avtomatikdir (söndürmək: layihədə `"speechEdgeFade": false`).
   - **Virtual multikamera** (bir rakursdan fərqli plan ölçüləri): planda `"multicam": {"style": "calm" | "dynamic"}`
     (punch-in `zooms` əvəzinə) və ya tətbiq olunmuş montaja `multicam <pid> [--style dynamic]`. Cümlə sərhədlərində
     ümumi / orta / yaxın plan; giriş ümumi, vurğulu fikir (sual, nida, rəqəm, "ən vacib"...) yaxın; eyni ölçü ardıcıl gəlmir;
     sakit üslubda vurğuda yavaş yaxınlaşma. Plan sayı keyfiyyət ehtiyatından: 4K→1080 ≈ 2x (3 plan), 1080→1080 — yalnız
     1.12x (fərq zəif — XƏBƏRDARLIQ-ı istifadəçiyə de: "növbəti çəkilişi 4K çəkin"), 16:9→9:16 — plan dəyişmir.
     **Rakurs (bucaq) dəyişmir, yeni bucaq uydurulmur** — istifadəçiyə "fərqli rakurs" kimi təqdim etmə, "fərqli plan ölçüsü" de.
   - Müştəri brendi (`brand.theme`), məqsəd və əvvəl bəyənilən montajlar: profildəki üslub qeydləri,
     `templates/expert-reels/` (README, VIDEO_TYPES, AUDIT), `instagram-ops/edit-references/`.
     Talking-head, reklam, seminar, motion graphics üçün eyni şablonu məcburi işlətmə.
   - **Brend rəngi = rəng AİLƏSİ, tək kod deyil** (istifadəçi qərarı). Profildəki `palette.family` və `theme`
     istiqamətdir: həmin ailənin yaxın çalarlarından videoya uyğun seçmək olar (məs. Nilufar — bənövşəyi ailəsi).
     “Kod təsdiqlənməyib” xəbərdarlığı vermə. Ailədən kənar rəng işlətmə; bir müştərinin rəngini başqasına keçirmə.
     Loqo yoxdursa loqo uydurma; istifadəçi loqo versə sonluqda/küncdə işlət.
   - **Storyboard təsdiqlənmədən yekun montaj qərarı tətbiq edilmir** (`variants` layihəni dəyişmir).
5. **Rəng və musiqi — storyboard ilə EYNİ qərar mesajında.** Qərar mesajının tərkibi (hamısı bir mesajda, ayrıca sual yoxdur):
   (1) `storyboard_variantlari.jpg` + hər variant 1–2 sətir; (2) `kadraj.jpg` əvvəl/sonra; (3) `reng_variantlari.jpg`;
   (4) 2–3 musiqi nümunəsi; (5) arxa səs təmizlənibsə `ses_evvel_sonra.m4a`; (6) material yoxlamasının `!` qeydləri (bir cümlə);
   (7) istifadəçi fon dəyişməsini istəyibsə `arxafon.jpg`. Yeni imkanları (davamlılıq tonu `variation`, plan ölçüləri `multicam`,
   J/L, yavaşlatma) ayrıca soruşma — uyğun olanları storyboard variantlarının içinə qoy (məs. A — təklif olunan ton, B — plan
   ölçüləri ilə), qalanını özün standart seç. Cavab bir sətir olsun: “B, rəng A, musiqi 2”.
   - Rəng: `looks <pid>` → `reng_variantlari.jpg` (3 təmsilçi kadr × Orijinal, A təbii, B yumşaq-isti,
     C təmiz-neytral; orta parlaqlıq aşağıdırsa avtomatik **D: zəif işıq** — dən azalır, kölgə açılır). Göndər, seçim gözlə. Seçim planda `"look": "A"|"B"|"C"` (`null` — düzəliş yoxdur).
     Fərqli işıqlanan kliplər avtomatik yaxınlaşdırılır (`"matchExposure": true`, ±0.04).
     Dəri rəngi və detal qorunur; güclü doyumluluq, kəskinləşdirmə, “4K effekti” yoxdur;
     retuş/gözəlləşdirmə yalnız ayrıca istəklə.
   - Musiqi (özün tap, 2–3 namizəd təklif et), lisenziya kommersiya istifadəsinə uyğun olmalıdır:
     1) **Freesound** (`tools/audio/freesound_music.py`, `FREESOUND_API_KEY` mühit dəyişəni, pulsuz açar) —
        yalnız **CC0** (müəllif qeydi tələb etmir). Açar yoxdursa bu yol bağlıdır.
     2) **Müəllif qeydi tələb edən musiqi (CC BY, məs. Incompetech) İŞLƏDİLMİR** — istifadəçi caption-a ad
        yazmaq istəmir. Yalnız CC0 / qeydsiz kommersiya lisenziyası.
     3) İstifadəçinin öz faylı/linki.
     ccMixter yükləmələri bu mühitdə bloklanır (403); Pixabay Music da (403); NC (qeyri-kommersiya) lisenziyalı
     musiqi müştəri reklamında işlədilmir. Mənbə, müəllif və lisenziyanı layihədə və istifadəçiyə yaz;
     musiqini əlavə etmiş kimi göstərmə. Namizədlər üçün `music-preview <pid> f1 f2 f3` → 20 s-lik dinləmə
     nümunələri (`musiqi_N.m4a`); seçim planda `"music": {"file": "..", "volume": 0.12, "from": 0}`
     (yumşaq giriş/çıxış, danışıqda azalma avtomatik).
   - SFX məqsədli və ölçülü (whoosh/pop sintez, `sfx`).
6. **Montaj və yekun MP4 (bir dəfə).** `choose <pid> plan_X.json` (qaralama düzəlişləri → apply → plan) → `render <pid>` →
   **`verify <pid>`** → `words <pid>`. `choose` seçilən variantı (növ, yanaşma, rəng, altyazı üslubu) müştəri profilinin
   `history`-sinə yazır — növbəti videoda təkrarın qarşısını almaq üçün (profil dəyişikliyini commit et).
   - `verify` yekun faylı da yoxlayır: qara kadr, donmuş kadr (şəkil klipləri və sonluq kartı istisna), səs piki və qəfil
     səs sıçrayışı (adi səviyyədən 9 LU yuxarı), ekran yazısının oxunma müddəti (~3 söz/s, ən azı 1.2 s), texniki uyğunluq
     (ölçü, yuv420p, səs tezliyi). Davamlı bölünmə (virtual multikamera, danışana keçid) kəsim sayılmır.
   - `verify` növ qaydalarını da yoxlayır: hər növdə qrafikadakı rəqəm danışıqda olmalıdır; reklam (3), səsləndirməli
     hekayə (8), modul dərs (15) — mətnin ardıcıllığı dəyişməyib (hook əvvələ çəkilməyib); modul dərs — üfüqi çıxış.
   - `verify`: kəsim sərhədləri orijinal səsin enerjisi və söz vaxtları ilə, səs/görüntü uzunluğu, kliklər,
     kəsim yanındakı sözlər yekun səsdə yenidən tanınaraq yoxlanır. `!` olan yerləri düzəlt (`cut`/`edit` ilə
     sərhədi genişləndir, yenidən render). Yoxlanılmayan hissəni yoxlanılmış kimi təqdim etmə.
   - `render` səsi **−14 LUFS**-a gətirir (pik ≤ −1.5 dBTP, video təkrar kodlanmır); fayl 40 MB-dan böyükdürsə
     `_ig.mp4` yüngül nüsxə də yaranır (eyni ölçü/fps) — telefona onu göndər.
   - `verify` kartın/başlığın **üzü örtməsini**, qrafikaların **bir-birini örtməsini** və mətnin **Reels interfeysi zonalarına**
     (yuxarı ad, aşağı caption, sağ düymələr) düşməsini də yoxlayır — `!` varsa yeri dəyiş, yenidən render.
   - `words`: şübhəli tanınmış sözlər vaxtla — istifadəçiyə **bir qısa siyahı**. Mənanı dəyişən təxmin etmə.
     İstifadəçinin düzəlişi: `fix-word <pid> səhv düzgün` (layihədə yadda qalır); müştəriyə aid termin/ad isə
     `--remember` ilə profilin lüğətinə də yazılır (növbəti videolarda avtomatik) — profil faylını commit et (yalnız experts/*.json).
   - MP4-ü göndər (SendUserFile) + 2–4 sətir: nə edildi, nə yoxlanmalıdır.

## Danışıq və kəsim qaydaları

- Mənanı və təbii ritmi qoru; sözün başı/sonu, heca kəsilmir.
- Kəsim nöqtəsi yalnız Whisper-ə əsaslanmır: `analysis` səssizliyi ffmpeg ilə (-35 dB) tapır, `cut` ən sakit
  10 ms çərçivəni seçir, `verify` yekunda yenidən ölçür.
- Təbii nəfəs və pauzaların hamısını silmə (≥1,2 s sükut namizəddir, 0,25 s nəfəs payı qalır).
- Şübhəli sərhəddə daha çox orijinal saxla. Whisper-in tanımadığı səs (musiqi, gülüş) avtomatik atılmır.

## Keyfiyyət

- Önizləmə yüngül nüsxədən; yekun **orijinaldan**, H.264 CRF 18. Ölçü kiçiltmə, süni böyütmə yoxdur;
  format tələb etmədikcə kadr tezliyi dəyişmir. “Sıfır keyfiyyət itkisi” zəmanəti vermə.

## Sonrakı düzəlişlər

- Layihə (plan, mənbə vaxtları, altyazı, qrafika, rəng, səs) `MONTAJ_DATA_DIR`-də saxlanır.
- “Bu sözü düzəlt” → `fix-word`; “mahnını dəyiş” → planda yalnız `music`, `plan` yenidən; “kartı yuxarı çək” →
  yalnız həmin element (`plan`-da həmin qrafikanın `y`-i və ya layihədə həmin klip). Digər qərarları yenidən vermə.
  Sonra `render` + `verify`.
- Konteyner müvəqqətidir. Yekun MP4-dən sonra `save <pid>` → `<pid>_layihe.tar.gz` (orijinal videolar olmadan, ~1 MB):
  istifadəçiyə göndər və ya şəxsi repoya qoy (public repoya YOX). Sonradan düzəliş: `restore <paket>` — orijinal
  Drive linkindən özü endirilir (link yoxdursa `--file mid=yol`), təsdiqlənmiş montaj olduğu kimi qayıdır.

## Qənaət və ünsiyyət

- Hazır kodu, şablonları, keşlənmiş analizi işlət; hər video üçün kod yazma. Yalnız seçilən müştərinin profilini oxu.
- Ödənişli API/hosting qoşma.
- İstifadəçiyə uzun texniki hesabat yazma: yalnız seçimlər, vacib suallar, real maneələr və hazır nəticə.

## Redaktor paneli (yalnız istifadəçi açıq istəyəndə)
Panel (`editor`, artifact) ehtiyatdadır. İstənəndə `SESSIYA_TELIMATI.md` 9-cu addım. Paneldə **Studiya** bölməsi var: rəng tonu
(müştərinin ailəsindən, dərhal görünür), altyazı qutu/kontur, arxa fon (orijinal / bulanıq / kitabxanadan şəkil), plan ölçüləri,
J/L-cut (bir neçə kamera olanda), seçilmiş klipin 0.5x yavaşladılması (60 fps material). Bu seçimlər düzəlişin `requests`
hissəsində gəlir — `apply-edits` onları icra edir, sonra `render`.
