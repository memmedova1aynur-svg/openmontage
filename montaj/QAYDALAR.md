# Montaj sistemi — QAYDALAR (tək mənbə)

> Status: **qüvvədədir (2026-11-23).** Ziddiyyət olanda **yalnız bu fayl** keçərlidir. `IS_AXINI.md` — yalnız əmr istinadı;
> `arxiv/` — köhnə sənədlər; `marketinq-sistemi` §2a və müştəri profillərindəki köhnə "ümumi qaydalar" buraya köçürülüb.
> `⚠` işarəli bəndlər mənim təklifimdir, sizin təsdiqinizi gözləyir.

## 0. Qaydaların iyerarxiyası

1. **Bu fayl** — bütün müştərilər üçün ümumi qaydalar və iş axını.
2. **Üslub kitabçası** — `montaj/uslub/<növ>.md` (dəqiq ölçülər). İlk hazır olan: `ekspert-reels.md`.
3. **Müştəri profili** — `templates/expert-reels/experts/<müştəri>.json`: yalnız həmin müştəriyə aid olanlar
   (rənglər, şrift, musiqi janrı, qadağalar). **Ümumi qayda müştəri profilinə yazılmır.**

Müştəri profili üslub kitabçasından fərqli bir şey deyirsə — müştəri profili qalib gəlir (yalnız o müştəri üçün).
Heç bir sənəddə yazılmayan qərar lazımdırsa — Claude **ən sakit, ən ehtiyatlı** variantı seçir və bunu planda qeyd edir.

## 1. Əsas prinsiplər

- **Claude yaradıcılıq etmir, kitabçaya əməl edir.** Kitabçada olmayan effekt, keçid, animasiya, şrift işlədilmir.
  Yeni effekt yalnız kitabçaya əlavə ediləndən sonra (sizin təsdiqinizlə) istifadə olunur.
- **Uydurma yoxdur.** Qiymət, tarix, rəqəm, nəticə, çağırış, ad, titul yalnız danışıqdan və ya müştəri profilindən.
- **Danışığın mənası dəyişmir.** Cümlələrin sırası dəyişmir, hook əvvələ çıxarılmır (yalnız ayrıca təsdiqlə).
- **Əsas pulsuz.** Bütün montaj yerli/pulsuz alətlərlə. Ödənişli xidmət (AI video/şəkil, AI səs, API, server)
  yalnız **siz həmin video üçün ayrıca təsdiqləyəndə**. Claude ödənişli xidməti özü təklif edə bilər, işə sala bilməz.
- **Müştəri materialı repoya düşmür.** Video, transkript, layihə faylı commit edilmir.

## 2. Sessiya (söhbət) qaydası

- **Bir çəkiliş = bir söhbət.** Bir çəkiliş: bir müştəri, eyni məkan/işıq, ~10 video (DataClone ~5).
  Bir söhbətdə yalnız **bir müştəri** olur; başqa müştərinin videosu həmin söhbətdə edilmir.
  Ortaq qərarlar (kadraj, səs, rəng) bir dəfə verilir, 10 plan bir səhifədə təsdiqlənir.
- Müştəri yaddaşı söhbətdə yox, **müştəri profilində** saxlanır. Hər təhvildən sonra profilin `history`
  hissəsinə bir sətir yazılır.
- Düzəliş başqa gün yeni söhbətdə ola bilər: layihə faylı (`*.montaj.json`, mediasız) təhvil zamanı saxlanır,
  yeni söhbət onu bərpa edir, transkripsiya təkrarlanmır.
- Söhbət başlatma mətni (sabit format, kopyala-yapışdır):

  ```
  MONTAJ
  Müştəri: <profil adı>
  Çəkiliş: <YYYY-MM-DD>
  Qovluq: <Drive qovluq linki>
  Qeyd: <varsa, bir cümlə>
  ```

- Claude sessiyanın əvvəlində **yalnız** bunları oxuyur: bu fayl, növün üslub kitabçası, seçilən müştərinin profili.
  `AGENT_GUIDE.md` və digər OpenMontage təlimatları montaj sessiyasında oxunmur.

### 2.1 Drive qovluq quruluşu

```
<Müştəri>/
  2026-12-01/        ← çəkilişin xam faylları (çəkiliş günü yüklənir)
  2026-12-15/
  Hazır/             ← təsdiqlənmiş yekun videolar
```

Fayl adları kamera adı ola bilər; sıra ada görə götürülür. Qovluq paylaşımı: "Linki olan hər kəs — Baxan".

## 3. İş axını (hər çəkiliş)

| # | Addım | Kim | AI lazımdır? |
|---|---|---|---|
| 1 | Material müştərinin Drive qovluğuna düşür | Müştəri | Yox |
| 2 | Hazırlıq: `batch` əmri — endirmə, transkripsiya, material yoxlaması, səs təmizləmə, təkrar cəhdlər | Sistem | Yox |
| 3 | Plan: kəsimlər, ekran yazıları, kartlar, B-roll, musiqi — kitabçaya və profilə görə | Claude | **Bəli** |
| 4 | Plan təsdiqi — toplu səhifədə | Siz | Yox |
| 5 | Render + avtomatik keyfiyyət qapısı | Sistem | Yox |
| 6 | Yekun baxış: `OK` və ya 1 raund düzəliş | Siz | Yox |
| 7 | Təhvil: müştərinin `Hazır` qovluğu (sonra Metricool) | Sistem | Yox |

Müştəri ilə və sizinlə əlaqə yalnız 4-cü və 6-cı addımda olur. Ara sual verilmir, əlavə variant raundu təklif edilmir.

### 3.0 Hazırlıq əmri (addım 2)

```
python -m montaj.session batch --link "<qovluq linki>" --client "<profil adı>" --date 2026-12-01
python -m montaj.session batch-status <müştəri>-<tarix>
```

Hər fayl ayrıca layihə olur (`<müştəri>-<tarix>-01`, `-02` …). Əmr yarıda kəsilsə, eyni əmri təkrar işə salın:
bitmiş addımlar təkrarlanmır. Bir videonun xətası digərlərini dayandırmır. Xülasə (müddət, material xəbərdarlıqları,
xətalar): `out/batches/<id>.md`. Claude plan yazmağa yalnız bu xülasədən və transkriptlərdən başlayır.

### 3.1 Plan (addım 3) — nə yazılır

Plan qısa və yoxlanıla biləndir, hər video üçün eyni formatda:

- müddət (əvvəl → sonra);
- çıxarılan hissələr: vaxt + bir sözlə səbəb (`təkrar`, `yarımçıq`, `pauza`, `səhv cəhd`);
- ekran yazıları və kartlar: vaxt + mətn (danışıqdan);
- B-roll: vaxt + nə;
- musiqi: janr + trek adı;
- **şübhəli yerlər** (Claude əmin deyil): ayrıca siyahı.

Planda şəkil yalnız ehtiyac olanda göndərilir: storyboard kadrları yalnız şübhəli yerlər üçün.

### 3.1a Plan icmalı və toplu təsdiq səhifəsi (addım 3–4)

Claude hər video üçün `out/<pid>/plan_icmal.json` yazır (vaxtlar yekun videoya görə, "0:12" formatında):

```json
{"summary": "bir cümlə", "before": 96, "after": 58,
 "cuts":  [{"at": "0:14", "len": 6.4, "why": "təkrar cəhd"}],
 "texts": [{"at": "0:01", "text": "..."}],
 "cards": [{"at": "0:09", "dur": 4, "kind": "list", "text": "..."}],
 "broll": [{"at": "0:26", "dur": 3, "what": "..."}],
 "music": "janr + trek", "doubts": ["0:33 — ..."]}
```

Sonra:
1. `python -m montaj.session batch-review <paket-id> [<paket-id> …]` → `.montaj/review/plans.json`
   (təsdiq gözləyən bütün paketlər bir faylda).
2. Səhifəni yenilə: Artifact publish — `file_path: .montaj/review/index.html` (mənbə: `montaj/review/review.html`),
   `files: {"plans.json": ".montaj/review/plans.json"}`, `url: https://claude.ai/artifact/4zkyDDwpJQwNQ3fNYDWwRW`
   (URL dəyişmir; səhifə hər dəfə eyni linkdədir).
3. İstifadəçi telefonda hər videoya "Təsdiq" və ya "Qeyd" verir.
4. Claude təsdiqləri oxuyur: `ArtifactData list`, collection `approvals`, sənəd id `<paket-id>--<NN>`
   (`{status: "ok"|"note", note}`). `ok` → render; `note` → yalnız yazılanlar dəyişir (§3.2), sonra render.

### 3.2 Düzəliş (addım 6) — 1 raund, sabit format

Bütün düzəlişlər **bir mesajda**, hər sətir bir düzəliş:

```
0:12 söz kəsilib
0:30 yazı: "müəllim" → "müəllimlər"
0:45-0:52 çıxart
musiqi: daha sakit
```

Claude yalnız yazılanları dəyişir, qalanına toxunmur, bütün planı yenidən qurmur.
**Hər düzəlişin səbəbi qeydə alınır** (§6): eyni səhv ikinci dəfə olmamalıdır.

## 3a. 15 günlük iş dövrü (hər müştəri, ayda 2 dəfə)

Ay iki dövrə bölünür: **1–15** və **16–ay sonu**. Hər dövr bir müştəri üçün bir iş paketidir:

| Addım | Nə | Harada |
|---|---|---|
| 1 | 15 günlük kontent strategiyası (mövzular, formatlar, satış məqsədi) | `ig-month` / `ig-plan` skill-ləri |
| 2 | Çəkiliş: 2 saat → ~10 video (DataClone: 1 saat → ~5) | çəkiliş planı (1, 3, 6-cı günlər) |
| 3 | Montaj: `batch` → plan → toplu təsdiq → render | §3 |
| 4 | Caption + hashtag: hər video üçün `out/<pid>/caption.json` | `ig-caption` skill-i |
| 5 | Lazımdırsa karusel, poster | `ig-carousel`, `post-studio` |
| 6 | Planlama paketi (aşağıda) | sistem |
| 7 | Planlama: Meta Business Suite (pulsuz, müştəri sizi partnyor kimi əlavə edir) | siz |

### Planlama paketi

```
python -m montaj.session batch-pack <paket-id> --start 2026-12-02 [--days 15] [--time 19:00]
```

`out/batches/<paket-id>_paket/`: `01_2026-12-02_19-00.mp4`, `…_caption.txt` (caption + hashtag), `…_cover.jpg`
(örtük; `caption.json`-da `cover_at` saniyəsi, standart 1.0), `teqvim.md` və `teqvim.csv`. Paylaşımlar dövrə bərabər
paylanır (10 video → 15 günə, hər biri ayrı gündə). Render olmayan videolar pakete düşmür və siyahıda göstərilir.
`caption.json`: `{"caption": "...", "hashtags": ["#..."], "cover_at": 1.0}`.

Alətlər: müştərilərin planlaması — **Meta Business Suite** (pulsuz, limitsiz). **Metricool** (pulsuz plan, 1 brend) —
yalnız öz səhifəniz üçün statistika. Ödənişli planlama aləti (SocialBee və s.) istifadə olunmur.

## 4. Ümumi montaj qaydaları (bütün növlər, bütün müştərilər)

Bunlar əvvəllər müxtəlif sənədlərdə və müştəri profillərində səpələnmişdi; indi yalnız buradadır.

- **Rəng:** həmişə `look C` (təmiz-neytral). Daha güclü effekt yoxdur. Dəri tonu təbii qalır.
- **Arxa fon:** orijinal qalır — bulanıqlaşdırılmır, qaraldılmır. Fon dəyişdirmə yalnız siz istəyəndə.
- **Güzgü çevirmə (hflip):** yoxdur. İstisna: mənbə özü güzgülənibsə (məs. saat səhv qoldadır) — yalnız təsdiqlə.
- **Pauzalar:** danışılmayan boşluqlar **≥0.45 s** kəsilir. Söz kəsilmir. Kəsimdən sonra söz təkrarı olmamalıdır.
- **Təkrar cəhdlər:** sonuncu tam cəhd saxlanılır, əvvəlkilər çıxarılır.
- **Səs:** hər videoda `voice-clean` yoxlanır; yekun səs **−14 LUFS**, pik ≤ −1 dBTP.
- **Musiqi:** yalnız CC0 / lisenziyası yoxlanmış. Danışıqda avtomatik enir (ducking).
  **Hər müştəridə dinamik musiqi** — yavaş musiqi yoxdur; janr və enerji videonun mövzusuna uyğun
  (məs. təhsil reklamı → educational/corporate; uşaq mövzusu → kids; ana-körpə, psixologiya → isti, amma aqressiv yox).
- **Səs effektləri (SFX):** hər animasiya girişində, xarakterinə uyğun (bax kitabça). Nitqdən aşağı.
- **B-roll başı örtmür:** bölünmüş ekran — danışan yuxarıda, B-roll sinədən aşağı; həmin anda altyazı başın üstündə.
- **Animasiya ekranı örtəndə** altyazı göstərilmir.
- **Etik:** ekspertin olmadığı real məkan həqiqi kimi göstərilmir; müştərini lağa qoyan yumor, dini simvol yoxdur.

## 5. Avtomatik keyfiyyət qapısı (addım 5)

Render-dən sonra `verify` + `delivery_qc`. **Hər hansı `fail` olan video sizə göndərilmir** — Claude düzəldib
yenidən render edir, yalnız sonra göndərir. Yoxlananlar (mövcud olanlar):

- ölçü, fps, səs-görüntü uzunluğu, sinxron;
- səs səviyyəsi, pik, dead air (ölü səssizlik);
- qara/donmuş kadr;
- kəsim yerində kəsilmiş söz (yekun videonun yenidən transkripsiyası);
- yazının oxunma müddəti, yazının üzü örtməsi;
- danışıqda olmayan rəqəm.

⚠ **Əlavə ediləcək yoxlamalar** (sizin səhv siyahınıza görə, kodda yazılmalıdır):
- musiqinin danışığı basması (danışıq zamanı musiqi səviyyəsi həddi);
- SFX-in çox yüksək olması / animasiyasız SFX;
- B-roll-un başı örtməsi;
- kitabçada olmayan effekt/animasiya istifadəsi (planda yalnız icazəli siyahıdan);
- rəng: look C-dən başqa dəyər;
- animasiya sayı və müddəti kitabçadakı hədlərdən kənar; iki animasiya/kart/B-roll arasında 4 s-dən az boşluq.

## 6. Səhv jurnalı — sistemin özünü düzəltməsi

Hər düzəliş (addım 6) bir sətir kimi `montaj/SEHV_JURNALI.md`-yə yazılır:

```
2026-11-22 | müştəri | kateqoriya | nə oldu | qayda/yoxlama əlavə olundu?
```

Kateqoriyalar: `kəsim`, `yazı`, `altyazı`, `səs`, `musiqi`, `SFX`, `rəng`, `kadraj`, `kart`, `B-roll`, `animasiya`, `render`.
Eyni kateqoriyada **2-ci səhv** olanda: ya kitabçaya dəqiq qayda yazılır, ya da §5-ə avtomatik yoxlama əlavə olunur.
Məqsəd: hər həftə düzəliş sayı azalır.

## 7. Miqyas (iş qrafikinə görə, 2026-12-01-dən)

- Çəkiliş: 1, 3, 6-cı günlər. Montaj: 2, 4, 5-ci günlər. Hər müştəri ayda 2 dəfə, çəkiliş başına ~10 video.
- Hədəf: ayda 350–400 video → **montaj günü orta ~30, ən sıx həftədə ~38 video**.
- Sizin vaxtınız video başına **10–15 dəqiqə**: plan təsdiqi + yekun baxış.
- AI yalnız 3-cü addımda (plan) işlədilir. Qalan addımlar AI-sız, toplu işləyir (hazırlıq çəkiliş günü axşam başlaya bilər).
- Plan söhbəti qısadır: çəkiliş başına bir söhbət, bir plan raundu, bir düzəliş raundu.
- ⚠ **Məhdudiyyət (dürüst):** abunəliyin istifadə limiti və GPU-suz konteyner (transkripsiya ~0.5x real vaxt) ölçülməlidir.
  İlk iki həftə hər paketdə addım müddətləri (`batch-status`) və istifadə qeyd olunur.

### Hələ qurulmayanlar (ardıcıllıqla)

1. ⚠ Yığcam sessiya girişi: `CLAUDE.md` montaj söhbətini birbaşa bu fayla yönləndirir.
2. ✓ Çəkiliş paketi əmri (`batch`). ⚠ Sonra: müştəri qovluğunda yeni çəkiliş qovluğunu avtomatik tapmaq.
3. ✓ Toplu plan təsdiqi səhifəsi (§3.1a).
4. ⚠ §5-dəki əlavə avtomatik yoxlamalar.
5. ⚠ Təhvil: `Hazır` qovluğu; sonra Metricool.
