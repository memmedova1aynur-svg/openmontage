# Montaj sistemi — QAYDALAR (tək mənbə)

> Status: **QARALAMA — təsdiq gözləyir.** Təsdiqdən sonra köhnə sənədlər (`IS_AXINI.md`, `SESSIYA_TELIMATI.md`,
> `YENI_SESSIYA_PROMPTU.md`, `marketinq-sistemi` §2a, müştəri profillərindəki "ümumi qaydalar") arxivə gedir və
> ziddiyyət olanda **yalnız bu fayl** keçərlidir.
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

- **Bir video = bir yeni söhbət.** Bir söhbətdə ikinci video edilmir.
  Səbəb: uzun söhbət baha başa gəlir və müştərilər arasında qarışıqlıq yaradır.
- Müştəri yaddaşı söhbətdə yox, **müştəri profilində** saxlanır. Hər təhvildən sonra profilin `history`
  hissəsinə bir sətir yazılır.
- Düzəliş də yeni söhbətdə ola bilər: layihə faylı (`*.montaj.json`, mediasız) təhvil zamanı saxlanır,
  yeni söhbət onu bərpa edir, transkripsiya təkrarlanmır.
- Söhbət başlatma mətni (sabit format, kopyala-yapışdır):

  ```
  MONTAJ
  Müştəri: <profil adı>
  Növ: ekspert-reels
  Fayl: <Drive linki və ya "qovluqdakı yeni fayl">
  Qeyd: <varsa, bir cümlə>
  ```

- Claude sessiyanın əvvəlində **yalnız** bunları oxuyur: bu fayl, növün üslub kitabçası, seçilən müştərinin profili.
  `AGENT_GUIDE.md` və digər OpenMontage təlimatları montaj sessiyasında oxunmur.

## 3. İş axını (hər video)

| # | Addım | Kim | AI lazımdır? |
|---|---|---|---|
| 1 | Material müştərinin Drive qovluğuna düşür | Müştəri | Yox |
| 2 | Hazırlıq: endirmə, material yoxlaması, transkripsiya, səs təmizləmə, kadraj | Sistem | Yox |
| 3 | Plan: kəsimlər, ekran yazıları, kartlar, B-roll, musiqi — kitabçaya və profilə görə | Claude | **Bəli** |
| 4 | Plan təsdiqi — toplu səhifədə | Siz | Yox |
| 5 | Render + avtomatik keyfiyyət qapısı | Sistem | Yox |
| 6 | Yekun baxış: `OK` və ya 1 raund düzəliş | Siz | Yox |
| 7 | Təhvil: müştərinin `Hazır` qovluğu (sonra Metricool) | Sistem | Yox |

Müştəri ilə və sizinlə əlaqə yalnız 4-cü və 6-cı addımda olur. Ara sual verilmir, əlavə variant raundu təklif edilmir.

### 3.1 Plan (addım 3) — nə yazılır

Plan qısa və yoxlanıla biləndir, hər video üçün eyni formatda:

- müddət (əvvəl → sonra);
- çıxarılan hissələr: vaxt + bir sözlə səbəb (`təkrar`, `yarımçıq`, `pauza`, `səhv cəhd`);
- ekran yazıları və kartlar: vaxt + mətn (danışıqdan);
- B-roll: vaxt + nə;
- musiqi: janr + trek adı;
- **şübhəli yerlər** (Claude əmin deyil): ayrıca siyahı.

Planda şəkil yalnız ehtiyac olanda göndərilir: storyboard kadrları yalnız şübhəli yerlər üçün.

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

## 4. Ümumi montaj qaydaları (bütün növlər, bütün müştərilər)

Bunlar əvvəllər müxtəlif sənədlərdə və müştəri profillərində səpələnmişdi; indi yalnız buradadır.

- **Rəng:** həmişə `look C` (təmiz-neytral). Daha güclü effekt yoxdur. Dəri tonu təbii qalır.
- **Arxa fon:** orijinal qalır — bulanıqlaşdırılmır, qaraldılmır. Fon dəyişdirmə yalnız siz istəyəndə.
- **Güzgü çevirmə (hflip):** yoxdur. İstisna: mənbə özü güzgülənibsə (məs. saat səhv qoldadır) — yalnız təsdiqlə.
- **Pauzalar:** danışılmayan boşluqlar **≥0.45 s** kəsilir. Söz kəsilmir. Kəsimdən sonra söz təkrarı olmamalıdır.
- **Təkrar cəhdlər:** sonuncu tam cəhd saxlanılır, əvvəlkilər çıxarılır.
- **Səs:** hər videoda `voice-clean` yoxlanır; yekun səs **−14 LUFS**, pik ≤ −1 dBTP.
- **Musiqi:** yalnız CC0 / lisenziyası yoxlanmış. Danışıqda avtomatik enir (ducking).
  Yavaş piano yoxdur. Janr mövzuya görə (məs. təhsil reklamı → educational/corporate; uşaq mövzusu → dinamik kids).
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
- animasiya sayı və müddəti kitabçadakı hədlərdən kənar.

## 6. Səhv jurnalı — sistemin özünü düzəltməsi

Hər düzəliş (addım 6) bir sətir kimi `montaj/SEHV_JURNALI.md`-yə yazılır:

```
2026-11-22 | müştəri | kateqoriya | nə oldu | qayda/yoxlama əlavə olundu?
```

Kateqoriyalar: `kəsim`, `yazı`, `altyazı`, `səs`, `musiqi`, `SFX`, `rəng`, `kadraj`, `kart`, `B-roll`, `animasiya`, `render`.
Eyni kateqoriyada **2-ci səhv** olanda: ya kitabçaya dəqiq qayda yazılır, ya da §5-ə avtomatik yoxlama əlavə olunur.
Məqsəd: hər həftə düzəliş sayı azalır.

## 7. Miqyas (gündə 100+)

Hədəf gündə 100+ video, tam pulsuz. Bunun üçün qaydalar:

- AI yalnız 3-cü addımda (plan) işlədilir. Qalan bütün addımlar AI-sız, toplu işləyir.
- Plan söhbəti qısa olmalıdır: bir söhbət ≈ bir plan + bir düzəliş. Uzun müzakirə yoxdur.
- Rutin addımlar üçün ucuz model, plan üçün güclü model.
- ⚠ **Məhdudiyyətlər (dürüst):** abunəliyin istifadə limiti və bulud konteynerində GPU olmaması gündəlik həcmi
  məhdudlaşdıra bilər. İlk həftə hər video üçün vaxt və istifadə ölçülür; 100+ üçün nə çatışmadığı rəqəmlərlə qərarlaşdırılır.

### Hələ qurulmayanlar (ardıcıllıqla)

1. ⚠ Yığcam sessiya girişi: `CLAUDE.md` montaj söhbətini birbaşa bu fayla yönləndirir.
2. ⚠ Müştəri qovluğu skaneri: Drive qovluğundakı yeni faylları tapıb hazırlığı (addım 2) başlatmaq.
3. ⚠ Toplu plan təsdiqi səhifəsi (telefondan, 10–30 plan bir səhifədə).
4. ⚠ §5-dəki əlavə avtomatik yoxlamalar.
5. ⚠ Təhvil: `Hazır` qovluğu; sonra Metricool.
