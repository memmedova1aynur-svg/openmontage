# Əsas iş axını: Drive linki → yekun MP4 (davamlı təlimat)

Bu fayl istifadəçinin təsdiqlədiyi **əsas** iş axınıdır və `SESSIYA_TELIMATI.md`-dən üstündür.
Redaktor paneli (artifact) saxlanılır, amma əsas axında **tələb edilmir və linki göndərilmir** —
yalnız istifadəçi açıq istəyəndə (`SESSIYA_TELIMATI.md`, 9-cu addım).

Hədəf: video ilk dəfədən hazır olsun, əlavə düzəliş tələb etməsin.

## Addımlar

1. **Drive linki gəlir.** Asılılıqlar yoxdursa `bash scripts/cloud-setup.sh`.
   `export MONTAJ_DATA_DIR=$HOME/montaj-data MONTAJ_OUT_DIR=$HOME/montaj-data/out`
2. **Müştəri profili və qısa sorğu.**
   - Profil adlarını `ls templates/expert-reels/experts/` ilə gör; yalnız seçilən müştərinin faylını oxu.
   - **Bir** qısa sorğu (`AskUserQuestion`) — yalnız məlum olmayan vacib sahələr: müştəri, məqsəd,
     format (talking-head / reklam: xidmət, təlim, məhsul / seminar / motion graphics / başqa), arzu olunan müddət,
     xüsusi istək. Məlum olanı yenidən soruşma. Müddət verilməyibsə — danışığa görə özün təyin et.
3. **Analiz.** `python -m montaj.session new --title "<ad>" --link "<link>" --client "<profil>" [--goal ...] [--format ...]`
   → `storyboard <pid>`. Transkripsiya yerli faster-whisper `large-v3-turbo` ilə, nəticə keşlənir
   (mənbə/parametr dəyişməyibsə təkrarlanmır). Ölçü, kodek, HDR-i qısa qeyd et.
   Transkripti oxu: təkrar cümlələri, alınmayan cəhdləri, yarımçıq fikirləri tap.
   Çıxarmaq üçün: `cut <pid> [media:]başla-son …` (sərhəd səsin ən sakit yerinə çəkilir; söz kəsilmir;
   şübhəli sərhəddə material saxlanılır, çıxışda ŞÜBHƏLİ yazılır) və ya `edit --exclude N`.
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
   - **Storyboard təsdiqlənmədən yekun montaj qərarı tətbiq edilmir** (`variants` layihəni dəyişmir).
5. **Seçimdən sonra rəng və musiqi.**
   - Rəng: `looks <pid>` → `reng_variantlari.jpg` (3 təmsilçi kadr × Orijinal, A təbii, B yumşaq-isti,
     C təmiz-neytral). Göndər, seçim gözlə. Seçim planda `"look": "A"|"B"|"C"` (`null` — düzəliş yoxdur).
     Fərqli işıqlanan kliplər avtomatik yaxınlaşdırılır (`"matchExposure": true`, ±0.04).
     Dəri rəngi və detal qorunur; güclü doyumluluq, kəskinləşdirmə, “4K effekti” yoxdur;
     retuş/gözəlləşdirmə yalnız ayrıca istəklə.
   - Musiqi: repoda hüququ təsdiqlənmiş musiqi kitabxanası **yoxdur**. Məqsədə və ritmə uyğun üslubu təklif et
     və istifadəçidən fayl/link istə (və ya trend musiqini Instagram-da paylaşarkən əlavə etməyi məsləhət gör).
     Musiqini əlavə etmiş kimi göstərmə. Fayl gələndə: `music-preview <pid> f1 f2 f3` → 20 s-lik dinləmə
     nümunələri (`musiqi_N.m4a`); seçim planda `"music": {"file": "..", "volume": 0.12, "from": 0}`
     (yumşaq giriş/çıxış, danışıqda azalma avtomatik).
   - SFX məqsədli və ölçülü (whoosh/pop sintez, `sfx`).
6. **Montaj və yekun MP4.** `choose <pid> plan_X.json` (qaralama düzəlişləri → apply → plan) → `render <pid>` →
   **`verify <pid>`** → `words <pid>`.
   - `verify`: kəsim sərhədləri orijinal səsin enerjisi və söz vaxtları ilə, səs/görüntü uzunluğu, kliklər,
     kəsim yanındakı sözlər yekun səsdə yenidən tanınaraq yoxlanır. `!` olan yerləri düzəlt (`cut`/`edit` ilə
     sərhədi genişləndir, yenidən render). Yoxlanılmayan hissəni yoxlanılmış kimi təqdim etmə.
   - `words`: şübhəli tanınmış sözlər vaxtla — istifadəçiyə **bir qısa siyahı**. Mənanı dəyişən təxmin etmə.
     İstifadəçinin düzəlişi: `fix-word <pid> səhv düzgün` (layihədə yadda qalır, təkrar analiz/render geri qaytarmır).
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
- Konteyner müvəqqətidir: sessiya bitəndə layihə itə bilər — istifadəçi orijinalı yenidən göndərir.

## Qənaət və ünsiyyət

- Hazır kodu, şablonları, keşlənmiş analizi işlət; hər video üçün kod yazma. Yalnız seçilən müştərinin profilini oxu.
- Ödənişli API/hosting qoşma.
- İstifadəçiyə uzun texniki hesabat yazma: yalnız seçimlər, vacib suallar, real maneələr və hazır nəticə.
