# Montaj tərzləri kataloqu

Müştəri **kim** olduğunu, tərz isə videonun **necə** montaj olunacağını müəyyən edir.

| Qat | Nə saxlayır | Harada |
|---|---|---|
| Müştəri | kadraj (üz, aşağı hissə), güzgü, brend rəngi (`accent`), ad | `instagram-clients/<müştəri>/brand_kit.json` → `talk` |
| Tərz | altyazı tipi, kəsim tempi, zoom, kartlar, SFX, rəng | `styles/<tərz>.json` |
| Video | kəsim aralıqları, hook, düzəlişlər, kart mətnləri | video planı (`plan.json`) |

Şrift verilməyibsə default **Montserrat** (Azərbaycan hərfləri; yoxdursa avtomatik yüklənir). Birləşmə sırası: default → müştəri → tərz → video planı (sonrakı üstün gəlir). Yəni eyni müştəri hər videoda fərqli tərz seçə bilər, kadrajı və rəngi isə avtomatik qalır.

## Tərzlər

| Tərz | Alət | Nə vaxt | Video planında əlavə |
|---|---|---|---|
| `sade` | talk.py | Səmimi söhbət; sadə ağ altyazı, kəsiklərdə yüngül zoom | — |
| `dinamik` | talk.py | Sürətli məsləhət, siyahı; söz-söz iri altyazı (aktiv söz vurğu rəngində), sıx kəsim, güclü zoom, swoosh | — |
| `musahibe` | talk.py | Sual-cavab; sual kartı, geniş/yaxın plan növbəsi | `questions: [[san, müddət, "Sual"]]` |
| `mif_fakt` | talk.py | İddia kartı + jestə sinxron qırmızı/yaşıl/sarı işıq və səs | `statements: [[başla, son, "İddia"]]`, `verdicts: [[san, "mif"\|"fakt"\|"yari"]]` |
| `minimal` | talk.py | Reklam, tanıtım; davamlı altyazı yox, iri açar söz kartları, sakit rəng | `cards: [[başla, son, "Söz"]]` |
| `dinamik_qalin` | talk.py | Ən güclü hook, cəsarətli fikir; 1–2 sözlük iri BÖYÜK HƏRFLİ altyazı, açar sözlər ikinci rəngdə | `keywords: ["söz"]` |
| `hook_basliq` | talk.py | Universal: video boyu yuxarıda sabit başlıq (səssiz izləyən də anlayır) + izləmə xətti | `headline: "Başlıq"` |
| `siyahi` | talk.py | "3 səhv", "4 addım": hər bənd deyiləndə nömrə ilə düşür və qalır, sonda tam siyahı ekranda (yadda saxlama gətirir) | `items: [[san, "Bənd"]]` |
| `serh_cavab` | talk.py | İzləyicinin real şərhinə video cavab; Instagram şərh balonu (yalnız real şərh, icazə ilə) | `comment: {t0, t1, user, text}` |
| `sekil_izah` | talk.py | Sxem, ekran görüntüsü, sənəd: split ekran (yuxarıda şəkil, aşağıda danışan) və ya tam ekran + dairəvi PiP | `inserts: [[başla, son, "şəkil.png", "split"\|"full"]]` |
| `kinematik` | talk.py | Hekayə, motivasiya: kino çərçivəsi, dən, vinyet, isti-soyuq rəng, kursiv serif altyazı | — (musiqi tövsiyə olunur) |
| `taymer` | talk.py | "60 saniyədə 3 məsləhət": küncdə geri sayım + dinamik altyazı | `timer: {t0, dur, label}` |
| `senedli` | editorial.py | Elmi mövzu; qrafik səhnələr, məqalə, kamera hərəkəti, kino dənəsi | plan editorial.py başlığında |
| `oyun` | game.py | Ekspertsiz interaktiv animasiya (yaddaş, Stroop, diqqət, boşluq) | `page`, `name`, `music` |

Kart və sual mətnlərində yeni sətir: `\N`. Vaxtlar hazır videonun zaman xəttindədir (kəsimdən sonra).

## İstifadə

```bash
python3 talk.py plan.json          # plan.json-da "style": "dinamik"
python3 editorial.py plan.json
python3 game.py plan.json
```

Hər nəticə `_vN` versiyası ilə yazılır (təsdiqlənmiş fayl qorunur), yanında `_qa.json`, story parçası və üz qabığı kadrı olur.

## Yeni tərz əlavə etmək

`styles/<ad>.json` faylı yarat. `_` ilə başlayan açarlar (`_ad`, `_nə_vaxt`) yalnız sənəddir. Mövcud parametrlər:
- altyazı: `sub` (`lines`/`words`/`none`), `font`, `fontsize`, `sub_bold`, `sub_italic`, `sub_outline`, `mv`, `upper`, `max_words`, `max_chars`, `keywords`, `word_size`, `word_mv`
- tempo və kadr: `zooms`, `gap`, `cut_sfx`, `cut_sfx_db`, `color` (ffmpeg rəng zənciri), `letterbox`, `grain`
- elementlər: `progress`, `headline`, `items`, `comment`, `inserts`, `timer`, `questions`, `statements`, `verdicts`, `cards`
- rəng: `accent` (müştəri kitindən də gələ bilər), `accent2`, `q_bg`, `split_bg`, `full_bg`

Hər element istənilən tərzlə birləşə bilər: məs. `dinamik` + `headline` + `progress`.

Tərzin istədiyi şrift (məs. `Lora`) sistemdə yoxdursa, avtomatik yüklənir (Google Fonts, OFL).

Qayda: oyun videoları həftədə 1-dən çox olmasın (kontent bəsit görünməsin).

## Planlaşdırılan tərzlər (#15–#48)

Hələ preset faylı yoxdur; seçiləndə `styles/`-ə əlavə olunur. Hazırlıq: hazır elementlərlə / kiçik əlavə / xüsusi iş.

### Oyun və şou formatları
_Ekspert kadrda; izləyici oynayır, sona qədər qalır_

| # | Tərz | Təsvir | Hazırlıq |
|---|---|---|---|
| 15 | 💰 Final sualı | Viktorina şousu janrı: 4 variant (A–D), geri sayım, gərgin musiqi, "50/50" köməyi, bal pilləkəni. Öz dizaynımızda. | kiçik əlavə |
| 16 | ✅ Düz / səhv sprint | 5 iddia, hər birinə 3 saniyə. Ekspert ✓ və ya ✕ göstərir, sonda izah. | hazır elementlərlə |
| 17 | 🕵️ Mif ovçusu | Mif/fakt seriyası: hər videoda 3 mif, "ovlanan" miflər sayğacda toplanır. | kiçik əlavə |
| 18 | 🔢 Təxmin et | Rəqəm sualı, slayder hərəkət edir, düz cavab sayğac animasiyası ilə açılır. | kiçik əlavə |
| 19 | ⚖️ Bu, yoxsa o? | İki seçim yan-yana, ekspert birini seçib 1 cümlə ilə izah edir. | hazır elementlərlə |
| 20 | ⚡ Blitz | Sürətli suallar, qəfil cavablar, "ding" və gülməli pauza kartları. | hazır elementlərlə |
| 21 | 🎯 Səviyyə testi | Asan → orta → çətin sual. Sonda: "Sən hansı səviyyədəsən?" | kiçik əlavə |
| 22 | ⏸️ Pauza et | "Ekranı dayandır və tap" — gizli detal, təkrar izləmə gətirir. | kiçik əlavə |
| 23 | 🗣️ Kim deyib? | Məşhur sitat, 3 ad variantı, ekspert kontekstini izah edir. | kiçik əlavə |

### Yumor və səmimiyyət
_Ekspertin insani tərəfi, paylaşılma gətirir_

| # | Tərz | Təsvir | Hazırlıq |
|---|---|---|---|
| 24 | 🎬 Bir neçə dəqiqə sonra… | Sitkom kartları, plastinka cızıltısı, dondurulmuş kadr: "Bəli, bu mənəm". | hazır elementlərlə |
| 25 | 🧊 Dondurulmuş kadr | Ən ifadəli anda kadr dayanır, üstünə komik yazı və səs. | hazır elementlərlə |
| 26 | 👂 Deyir / eşidir | "Valideyn deyir" və "Uşaq eşidir" — eyni cümlənin iki versiyası. | kiçik əlavə |
| 27 | 👀 POV | "POV: uşaq 10-cu dəfə 'niyə?' soruşur" — mətn kartı və ekspertin reaksiyası. | hazır elementlərlə |
| 28 | 🪞 Gözlənti / reallıq | Split ekran: gözlənti və reallıq kadrları yan-yana. | kiçik əlavə |
| 29 | 💬 Şərhləri oxuyuram | Real şərhləri oxuyub cavablayır (icazə ilə, mənfi şərhlər yox). | hazır elementlərlə |
| 30 | 😂 Uğursuz dubllar | Ayda bir: çəkilişdən gülməli səhvlər, "blooper" səsləri. | hazır elementlərlə |

### Təhsil və izah
_Ekspertliyi göstərir, yadda saxlanır_

| # | Tərz | Təsvir | Hazırlıq |
|---|---|---|---|
| 31 | ✍️ Lövhə | Açar sözlər danışdıqca əl yazısı kimi ekranda yazılır. | kiçik əlavə |
| 32 | 🧭 Sxem animasiyası | Proses addım-addım çəkilir, oxlar və bloklar danışığa sinxron. | kiçik əlavə |
| 33 | 📊 Rəqəm kartı | İri rəqəm sayğac animasiyası ilə çıxır, altında mənbə. | kiçik əlavə |
| 34 | ❌ Səhv / düz üsul | Sol tərəfdə qırmızı ✕ (səhv üsul), sağda yaşıl ✓ (düz üsul). | hazır elementlərlə |
| 35 | 👐 Addım-addım | Təlimat: nömrəli addımlar, əllərin yaxın planı, "evdə et" kartı. | hazır elementlərlə |
| 36 | ⏱️ 1 dəqiqəlik dərs | Problem → səbəb → həll; xronometr və 3 hissəlik çubuq. | kiçik əlavə |
| 37 | 📖 Termin lüğəti | Yeni termin kartı: söz, tələffüz, sadə izah, gündəlik nümunə. | hazır elementlərlə |

### Hekayə və emosiya
_Bağ qurur, sona qədər izlənir_

| # | Tərz | Təsvir | Hazırlıq |
|---|---|---|---|
| 38 | 📽️ Hekayə qarmağı | "Bir gün kabinetə bir ana gəldi…" — kinematik tərz, anonim hekayə. | hazır elementlərlə |
| 39 | 🗓️ Mənimlə bir gün | Kamera arxası: saat kartları, sürətlənmiş kadrlar, günün anları. | hazır elementlərlə |
| 40 | ✉️ Məktub | Ekspert izləyiciyə məktub oxuyur, kağız teksturası, yumşaq musiqi. | hazır elementlərlə |
| 41 | 🖋️ Sitat kartı | Ekspertin ən güclü cümləsi iri tipoqrafiya ilə, səs fonda. | hazır elementlərlə |

### Trend və platforma formatları
_Instagram alqoritminin sevdiyi mexanikalar_

| # | Tərz | Təsvir | Hazırlıq |
|---|---|---|---|
| 42 | 🟩 Yaşıl ekran | Ekspert məqalə, xəbər və ya ekran görüntüsünün önündə danışır (fon avtomatik çıxarılır). | xüsusi iş |
| 43 | 🔀 Duet / stitch | Başqa videoya (icazə ilə) split ekranda reaksiya və düzəliş. | kiçik əlavə |
| 44 | 🖼️ Karuseldən reel | Hazır karusel slaydları hərəkətli slayd-şou kimi, səs və keçidlərlə. | kiçik əlavə |
| 45 | ❓ Sual qutusu | Story sual stikeri görünüşündə sual, ekspert cavabı. | hazır elementlərlə |
| 46 | 🎧 Səs-ASMR | Sensor oyuncaqların yaxın plan səsləri (Lamiyə üçün ideal). | hazır elementlərlə |
| 47 | 📆 Gün 1/30 | Çağırış seriyası: hər videoda gün sayğacı, seriyaya bağlılıq. | hazır elementlərlə |
| 48 | 🔁 Loop video | Sonu əvvəlinə bitişik, izləyici dövrəni hiss etmir — təkrar izlənmə. | kiçik əlavə |

Qeyd: "Final sualı" viktorina şousu janrıdır — konkret televiziya şousunun loqosu, musiqisi və dizaynı istifadə olunmur.

## Agentlik S-kod kataloqu (S01–S36)

Agentliyin öz montaj kataloqu (PDF, S01–S36) və kod → tərz xəritəsi açıq repoda deyil, `instagram-clients/_agency/` qovluğundadır (`s_kodlar.json`; yol `PRO_AGENCY` ilə dəyişdirilə bilər). Video planında `"style": "S01"` yazmaq kifayətdir: kod uyğun tərzə çevrilir. Kod mövcud alətlə alınmırsa (B-roll, xüsusi çəkiliş), skript nə lazım olduğunu deyib dayanır.

İş qaydası (kataloqdan):
1. Müştəri, mövzu, məqsəd, material, kod, müddət, brend qaydaları oxunur; fayl və səs əvvəl yoxlanır.
2. Standart rejim avtomatik təhvildir. Storyboard yalnız istənəndə: `python3 talk.py plan.json storyboard` → `_storyboard.jpg` + `_storyboard.md` (seqmentlər, vaxt, mətn, elementlər); təsdiqdən sonra render.
3. Bir əsas tərz + ən çox bir köməkçi tərz. Brend rəngini dəyişmək yeni tərz yaratmır.
4. Mənbəsiz statistika və sitat yoxdur; musiqi, mənbə video və şəkillərin istifadə hüququ yoxlanır; məşhur şouların loqo və musiqisi təkrarlanmır.
5. Danışanın səsi, ifadəsi və mənalı pauzaları qorunur; ardıcıl işlərdə eyni açılış təkrarlanmır.
6. Son video açılıb yoxlanmadan "hazır" deyilmir (QA: kadr sayı, səs, pik, altyazı sahəsi).
7. Hər kodun ilk real işi "Sınaq", təsdiqdən sonra "Yoxlanıb" statusu alır.
