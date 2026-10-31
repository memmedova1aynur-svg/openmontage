# Əsas iş axını: Drive linki → yekun MP4 (davamlı təlimat)

Bu fayl istifadəçinin təsdiqlədiyi **əsas** iş axınıdır (sorğu → Drive linki → analiz → 3 storyboard → rəng/musiqi → MP4) və `SESSIYA_TELIMATI.md`-dən üstündür.
Redaktor paneli (artifact) saxlanılır, amma əsas axında **tələb edilmir və linki göndərilmir** —
yalnız istifadəçi açıq istəyəndə (`SESSIYA_TELIMATI.md`, 9-cu addım).

Hədəf: video ilk dəfədən hazır olsun, əlavə düzəliş tələb etməsin. İstifadəçi ilə yalnız **iki dəfə** əlaqə:
(1) sorğu, (2) **bir qərar mesajı** — storyboard variantları + kadraj (əvvəl/sonra) + rəng variantları + musiqi
nümunələri birlikdə göndərilir, istifadəçi bir cavabla seçir (məs. “B, rəng A, musiqi 2”). Sonra yalnız **yekun MP4**.
Ara düzəliş raundları təklif etmə.

## Addımlar

1. **Əvvəl qısa sorğu — Drive linkindən ÖNCƏ.** İstifadəçi yeni video istəyəndə (və ya link sorğusuz gəlsə)
   **bir** sorğu aç (`AskUserQuestion`): müştəri, məqsəd, format (talking-head / reklam: xidmət, təlim, məhsul /
   seminar / motion graphics / başqa), arzu olunan müddət, xüsusi istək. Yalnız məlum olmayan sahələri soruş.
   - Profil adlarını `ls templates/expert-reels/experts/` ilə gör; yalnız seçilən müştərinin faylını oxu
     (profildə olan məlumatı yenidən soruşma). Müddət verilməyibsə — danışığa görə özün təyin et.
   - Sorğudan sonra Drive linkini istə.
2. **Drive linki gəlir.** Asılılıqlar yoxdursa `bash scripts/cloud-setup.sh`.
   `export MONTAJ_DATA_DIR=$HOME/montaj-data MONTAJ_OUT_DIR=$HOME/montaj-data/out`
3. **Analiz.** `python -m montaj.session new --title "<ad>" --link "<link>" --client "<profil>" [--goal ...] [--format ...]`
   → `storyboard <pid>`. Transkripsiya yerli faster-whisper `large-v3-turbo` ilə, nəticə keşlənir
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
3b. **Arxa səsin təmizlənməsi — HƏR videoda yoxlanır.** `voice-clean <pid>` (standart `auto`): kafe uğultusu,
   uzaq danışıq, çəngəl-bıçaq, uzaqdan musiqi azaldılır; **danışanın səsi qorunur** (zəiflətmə ≤20 dB, danışıq
   səviyyəsi orijinala bərabərləşdirilir, sinxron dəyişmir). Arxa səs azdırsa (studiya) özü tətbiq etmir.
   Orijinal dəyişmir; yalnız danışıq qatı təmizlənmiş nüsxəni işlədir (musiqi, SFX, B-roll səsi toxunulmaz).
   Təmizlənibsə `ses_evvel_sonra.m4a`-nı qərar mesajına əlavə et. Yaxında danışan başqa adamın səsi də danışıqdır —
   tam silinmir, bunu de. Model (DeepFilterNet3) internetdən endirildiyi üçün ilk işə salmada icazə soruşula bilər.
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
4. **Üç vizual storyboard.** Hər variant üçün `plan_A.json`, `plan_B.json`, `plan_C.json` yaz və
   `variants <pid> plan_A.json plan_B.json plan_C.json` → `storyboard_variantlari.jpg` (real kadrlar üzərində
   qrafika ilə) + `variant_X.mp4` (540p önizləmə). Şəkli göndər + hər variant üçün 1–2 sətir izah.
   - Variantlar **giriş, ritm, başlıq, məlumat kartları və vizual təqdimat** baxımından həqiqətən fərqlənsin
     (məs. A: sakit, söz-söz altyazı + az kart; B: güclü hook başlıq + bölmələr + punch-in; C: siyahı/kart
     ağırlıqlı, məlumat yönümlü). Yalnız rəng dəyişərək variant yaratma.
   - Planda `"title"`, `"storyboard": {"exclude": [..], "order": [..], "text": {"1": ".."}}` (giriş/sıra fərqi),
     `captions`, `graphics`, `zooms`, `sfx`.
   - Müştəri brendi (`brand.theme`), məqsəd və əvvəl bəyənilən montajlar: profildəki üslub qeydləri,
     `templates/expert-reels/` (README, VIDEO_TYPES, AUDIT), `instagram-ops/edit-references/`.
     Talking-head, reklam, seminar, motion graphics üçün eyni şablonu məcburi işlətmə.
   - **Brend rəngi = rəng AİLƏSİ, tək kod deyil** (istifadəçi qərarı). Profildəki `palette.family` və `theme`
     istiqamətdir: həmin ailənin yaxın çalarlarından videoya uyğun seçmək olar (məs. Nilufar — bənövşəyi ailəsi).
     “Kod təsdiqlənməyib” xəbərdarlığı vermə. Ailədən kənar rəng işlətmə; bir müştərinin rəngini başqasına keçirmə.
     Loqo yoxdursa loqo uydurma; istifadəçi loqo versə sonluqda/küncdə işlət.
   - **Storyboard təsdiqlənmədən yekun montaj qərarı tətbiq edilmir** (`variants` layihəni dəyişmir).
5. **Rəng və musiqi — storyboard ilə EYNİ qərar mesajında.**
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
   **`verify <pid>`** → `words <pid>`.
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
