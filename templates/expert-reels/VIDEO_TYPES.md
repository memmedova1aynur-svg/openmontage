# Video növləri və montaj yanaşmaları

Gələcək işlər üçün istinad. Montaj resepti deyil. **Mühərrikin oxuduğu forma — `montaj/types.py` (reyestr):**
`python -m montaj.session types` (siyahı, hazırlıq statusu), `types <N>` (3 storyboard variantı, əmrlər, qaydalar),
`types --survey` (sorğu sualları). Bu cədvəl dəyişəndə reyestri də yenilə (test uyğunluğu yoxlayır). Hər yeni material gələndə əvvəl burada növü müəyyənləşdirilir, sonra işlənir.

Növ çəkiliş tətbiqinin adına görə yox, faylın özünə və məzmununa görə təyin edilir.

Material təxminən belə bölünür: 90% danışıq, 10% fəaliyyət və digər vizual görüntülər. Bu, müşahidədir, istehsal üçün məcburi nisbət deyil.

## Üç ayrı ox

Videonu təsnif edərkən bu üç şeyi qarışdırma:

| ox | sual | nümunə |
|---|---|---|
| **Forma** | Material necə çəkilib? | kameraya danışıq, seminar görüntüsü, ekran yazısı |
| **Məzmun** | Nə deyilir və ya göstərilir? | izah, hadisə, mikrodərs, rəy |
| **Məqsəd** | Video nəyə xidmət edir? | maarifləndirmə, atmosfer, reklam, dəvət |

Eyni material bir neçə növə çevrilə bilər. Məsələn, seminar görüntüsündən atmosfer videosu (5), ekspert çıxarışı (4) və ya reklam hazırlamaq olar.

## Növlər

| # | Növ | Əsas dəyəri nə daşıyır | Diqqət nöqtəsi |
|---|---|---|---|
| 1 | **Birbaşa kameraya ekspert danışığı.** Oturaraq və ya ayaqüstə; teleprompterlə və ya sərbəst. | Danışığın mənası və ekspertin təqdimatı | Teleprompter ayrıca növ deyil, çəkiliş üsuludur. Məzmun fikir, izah, diaqnostik sual, hadisə, təhlil və ya mikrodərs ola bilər. |
| 2 | **Kadrarxası sual-cavab.** Sual kameranın arxasından verilir, ekspert sual verənə baxaraq cavab verir. | Sual və cavab birlikdə | Sual çıxarılsa, cavabın tək başına anlaşıldığını yoxla. |
| 3 | **Hazır mətnli reklam və xidmət təqdimatı.** Xidmət, konsultasiya, təlim və ya proqram haqqında. | Təsdiqlənmiş mətnin ardıcıllığı | Ayrıca hook yaratmaq və cümlələrin yerini dəyişmək avtomatik lazım deyil. Giriş artıq mətndə ola bilər. |
| 4 | **Seminardan ekspert çıxarışı.** Uzun seminardan müstəqil qısa video. Alt növlər: izah/mikrodərs, motivasiyaedici çıxış, hadisə/hekayə, auditoriya ilə sual-cavab, praktik nümayiş. | Seçilən hissənin özü | Hissə seminardan ayrılanda da anlaşılmalıdır. Nümayişdə intonasiya, jest və mənalı pauzalar məzmunun bir hissəsidir. |
| 5 | **Seminar və tədbir icmalı.** Məkan, təlimçi, iştirakçılar, fəaliyyətlər, sertifikat, alqış. | Hadisənin görüntüləri | Əsasən musiqi; seçilmiş real səslər qala bilər. Məqsəd atmosfer, prosesi tanıtmaq və ya dəvət ola bilər. |
| 6 | **Praktik fəaliyyət və ekspert səsləndirməsi.** Oyun, materialla iş, dərs, metodun tətbiqi. | Görüntüdəki konkret fəaliyyət və onun izahı | Danışıq görüntüdəki konkret fəaliyyətlə bağlı olmalıdır. Məqsəd maarifləndirmə və ya reklam ola bilər. |
| 7 | **İş prosesi və kameraarxası.** Hazırlıq, material seçimi, dərsə hazırlıq, çəkiliş, gündəlik iş. | İşin necə görüldüyü | Musiqi ilə və ya səsləndirmə ilə hazırlana bilər. |
| 8 | **Görüntülər üzərindən səsləndirməli hekayə və ya reklam.** Müxtəlif fəaliyyətlərin görüntüləri bir mövzu ətrafında birləşdirilir. | Səsləndirmənin mesajı | Səs hərəkəti təsvir etmir. Peşəkar hekayə, mövqe, xüsusi gün mesajı və ya təklif çatdırır. |
| 9 | **Nağıl və animasiyalı hekayə.** Səsləndirilmiş hekayə, motion və ya cizgi səhnələri. | Hekayənin ardıcıllığı və səsin ifadəsi | Obrazlar davamlı qalmalı, səhnələr mətnə uyğun olmalıdır. |
| 10 | **Sürətli, əyləncəli sual-cavab.** Qısa suallar, spontan, bəzən yumorlu cavablar. | Cavablar və onların təbiiliyi | Tərəddüd, pauza, üz ifadəsi və gülüş də məna daşıyır. Sakit müsahibə ritmində işlənmir. |
| 11 | **İki ekspertin söhbəti.** Qarşılıqlı danışıq, suallar, fikirlərə münasibət. | Danışanların bir-biri ilə əlaqəsi | Seçilən hissədə kontekst qorunmalıdır. Hələlik söhbətdən qısa video çıxarmaq nəzərdə tutulur, uzun podkast deyil. |
| 12 | **Hərəkətli kartlar və video-karusel.** Mətn, şəkil, sxem, qrafika video səhifələrində. | Ekran | Ekspertin görünməsi şərt deyil. Oxuma müddəti və səhifələr arasındakı məntiq vacibdir. |
| 13 | **Material və ekran üzərində izah.** Dərs planı, təqdimat, kart, sənəd, ekran yazısı. | Təhlil olunan material | Ekspert tam görünə, kiçik pəncərədə qala və ya yalnız səsi eşidilə bilər. |
| 14 | **İştirakçı rəyi və təcrübəsi.** İnsan təlim və ya xidmət haqqında öz təcrübəsini danışır. | Real rəy və konteksti | Montajla insanın demədiyi nəticə yaradılmamalıdır. |
| 15 | **Saytda yerləşdirilən modul təlim dərsi.** Adətən üfüqi, 5–10 dəq.; kursun bir neçə əlaqəli bölümündən biri; mütəxəssis kamera qarşısında mövzunu izah edir (teleprompterlə və ya sərbəst). | Dərsin aydınlığı və məntiqi ardıcıllığı | Hər bölüm ayrıca fayldır, amma kursun vizual dili bütün bölümlərdə eynidir. Hook yoxdur; Reels ritmi tətbiq edilmir. |
| 16 | **Qrafika ağırlıqlı izah (motion graphics).** Data, IT, analitika: rəqəmlər, qrafiklər, proses addımları qrafika ilə; ekspert dairədə və ya yanda. | Qrafikanın çatdırdığı rəqəm/məntiq | Qrafikada yalnız danışıqda deyilən rəqəmlər. |
| 17 | **Loqo animasiyası.** Brendin loqosunun qısa hərəkətli açılışı/bağlanışı. | Brend tanınması | Müştərinin loqo faylı (PNG/SVG) olmadan qurulmur — planlaşdırılıb. |

## Təsnifat qaydaları

- **B-roll ayrıca məqsəd deyil.** O, başqa videonu tamamlayan əlavə görüntüdür.
- **Reklam bir məqsəddir.** Müxtəlif formalarla hazırlana bilər (3, 5, 6, 8, 12, 14 və s.). "Hazır mətnli reklam" (3) isə ayrıca iş halıdır.
- **Qarışıq video.** Bir neçə növü birləşdirən videoda əsas növü və əlavə xüsusiyyəti yaz. Məsələn: "1 + 13: ekran izahı ilə".
- **Hook və B-roll avtomatik deyil.** Hər danışıq videosuna lazım olduqlarını fərz etmə.
- **Çəkiliş yeri növü təkbaşına müəyyən etmir.**
- **Növ aydın deyilsə,** yanlış ad vermə. Qeyri-müəyyənliyi və mümkün variantları qeyd et.

## Qeyd forması

Hər layihədə (`projects/<id>/`) və ekspert tarixçəsində (`experts/<id>.json` → `history`) belə yazılır:

```
növ: 3                     # əsas növ
əlavə: —                   # varsa: "1 + 13", "4 / alt növ: praktik nümayiş"
məqsəd: reklam (təlimə qeydiyyat)
qeyri-müəyyənlik: —        # varsa, nə və niyə
```

## İndiyə qədərki videolar (Aytən Calilova)

Bu nümunələr işlənmiş materialdan götürülüb:

- **Növ 1** (birbaşa kameraya danışıq, maarifləndirmə). Danışıq videoları: yaddaş/məlumatsızlıq, öyrənmək bacarıqdır və s.
- **Növ 3** (hazır mətnli reklam). Təhsildə satış təlimi, qeydiyyat; video "şərhlərdə SATIŞ yazın" çağırışı ilə bitir. Əvvəlki iki reklam videosu da bu növə aiddir.

---

# Montaj yanaşmaları kitabxanası

Video növü montaj seçimini istiqamətləndirir, amma heç bir növün tək şablonu yoxdur. Hər işdə **bir əsas yanaşma** seçilir, lazım olsa **bir əlavə yanaşma** ilə tamamlanır. Seçim layihə qeydinə yazılır: `yanaşma: M01 + M02`.

### M01 — Təmiz ekspert montajı
- Əsasda ekspertin danışığı və performansı dayanır.
- Artıq başlanğıcları, texniki gözləmələri və mənasız təkrarları çıxar.
- Mənalı pauzaları və fikrin vacib şərtlərini saxla.
- Oxunaqlı altyazı, seçilmiş yaxınlaşdırma və az sayda vurğu istifadə et.
- Hər cümləyə ayrıca effekt və ya yazı qutusu vermə.
- **Uyğundur:** peşəkar fikir, həssas mövzu, şəxsi təcrübə, sakit izah.

### M02 — Tipoqrafik vurğu
- Ekspert görünür, seçilmiş söz və ifadələr vizual vurğu alır.
- Altyazı ilə vurğu mətnini ayır.
- Mətnin ölçüsünü və yerini fikrin əhəmiyyətinə görə seç.
- Qutusuz mətn, qısa qeyd və iri ifadələrdən uyğun olanını istifadə et.
- Bütün danışığı böyük hərəkətli yazıya çevirmə.
- **Uyğundur:** aydın tezislər, əsas anlayışlar, seçilmiş reklam və motivasiya çıxışları.

### M03 — Ekspert + qrafik izah
- Mərhələ, rol, səbəb, seçim və əlaqələri kart, ox və sadə sxemlə aç.
- Ekspertin və qrafikanın yerini birlikdə planla.
- Məlumatı hissə-hissə göstər, eyni anda çox element yığma.
- Qrafikada yalnız danışıqda olan və ya təsdiqlənmiş məlumatı istifadə et.
- **Uyğundur:** mikrodərs, metod izahı, mərhələlər, xidmətin quruluşu.

### M04 — Danışıq + tam ekran əlavə görüntü
- Danışıq əsas xətt kimi davam edir.
- Müəyyən hissələrdə uyğun görüntü ekspertin yerini tutur.
- Görüntünü deyilən fikirlə əlaqələndir.
- Təsadüfi stock görüntüsünü real fəaliyyətin və ya nəticənin sübutu kimi təqdim etmə.
- Uyğun material yoxdursa, B-roll məcburi deyil.
- **Uyğundur:** real nümunə, proses, fəaliyyət və xidmət haqqında danışıq.

### M05 — Material əsasdır, ekspert kiçik pəncərədədir
- Ekranın əsas sahəsini sənəd, fəaliyyət, ekran yazısı və ya nümunə tutur.
- Ekspert dairə və ya düzbucaqlı pəncərədə görünür.
- Pəncərənin forması və yeri əsas məlumatı örtməməlidir.
- Ekspertin kiçik görünməsi fayda vermirsə, bu yanaşmanı seçmə.
- **Uyğundur:** material təhlili, ekran izahı, fəaliyyətə ekspert şərhi.

### M06 — Müqayisəli montaj
- İki variantı ardıcıl və ya bölünmüş ekranda göstər.
- Müqayisə meyarını aydınlaşdır.
- Fərqi göstərmək üçün uyğun mətn və işarələrdən istifadə et.
- Kontekstdən asılı məsələni avtomatik "doğru/səhv" kimi etiketləmə.
- **Uyğundur:** iki yanaşma, iki izah, situasiyanın alternativ həlli.

### M07 — Hekayə və çıxış montajı
- Vəziyyət → çətinlik → qərar → nəticə əlaqəsini qoru.
- Emosional pauza, baxış və reaksiyaları məqsədlə saxla.
- Musiqini danışığın ifadəsinə uyğunlaşdır.
- Motivasiya çıxışını mütləq sürətli kəsim və yüksək musiqi ilə işləmə.
- Cümlələrin yerini dəyişəndə məna və səbəb əlaqəsini təhrif etmə.
- **Uyğundur:** hadisə, şəxsi təcrübə, motivasiyaedici seminar çıxarışı.

### M08 — Praktik nümayiş montajı
- Hərəkətin vacib mərhələləri görünən qalmalıdır.
- Detalı və nəticəni lazım olan anda göstər.
- İzahı müvafiq hərəkətlə uyğunlaşdır.
- Nağıl danışma nümayişində intonasiya, jest və pauzalar nümayişin hissəsidir.
- Vacib addımları sürətləndirmə və ya kəsimlə gizlətmə.
- **Uyğundur:** oyun, metodun tətbiqi, nağıl danışma nümayişi, materialla iş.

### M09 — Tədbir və proses montajı
- Görüntüləri sadəcə qarışdırma: açılış, inkişaf və tamamlanma qur.
- Musiqi ilə yanaşı uyğun real səslər də istifadə edilə bilər.
- Sertifikat, alqış və digər anları hadisədəki roluna görə yerləşdir.
- Yavaşlatmanı yalnız materialın texniki imkanı və səhnənin məqsədi uyğun gəldikdə işlət.
- Musiqinin hər döyüntüsündə kəsmək məcburi qayda deyil.
- **Uyğundur:** seminar icmalı, kameraarxası və iş prosesi.

### M10 — Yumorlu sual-cavab montajı
- Təbii zarafatı, cavabdan əvvəlki pauzanı və üz ifadəsini tap.
- Bunlardan seçərək istifadə et: yaxınlaşdırma, donmuş kadr, qısa təkrar, reaksiya yazısı, səs effekti.
- Hər cavaba effekt əlavə etmə.
- Eksperti alçaldan və ya demədiyi fikri deyirmiş kimi göstərən əlaqə yaratma.
- İlkin seçim yüngül yumordur; daha intensiv yanaşma storyboardda təklif olunur.
- **Uyğundur:** sürətli, spontan, əyləncəli sual-cavab.

### M11 — Səsləndirməli vizual hekayə
- Səsləndirmə ilə görüntü arasında məna əlaqəsi qur.
- Görüntü deyilən sözü təkrarlamaq məcburiyyətində deyil, amma mövzudan yayınmamalıdır.
- Reklamın, hekayənin və xüsusi gün mesajının fərqli quruluşunu nəzərə al.
- Hazır və təsdiqlənmiş səsləndirməni özbaşına yenidən sıralama.
- **Uyğundur:** fəaliyyətlərdən yığılmış reklam, peşəkar hekayə, mövzu videosu.

### M12 — Nağıl və animasiya
- Səhnələri səsləndirmənin ardıcıllığına uyğun qur.
- Obrazların görünüşü, məkan və vizual üslub ardıcıl qalmalıdır.
- Hərəkət və səslər nağılın ifadəsini dəstəkləsin.
- Obraz və səhnə üslubu storyboard təsdiqinə daxil edilir.
- Texniki imkan çatmırsa, yaradılmış kimi göstərmə; uyğun alternativi bildir.
- **Uyğundur:** nağıl səsləndirməsi, animasiyalı hekayə.

### M13 — Hərəkətli kartlar
- Bir səhifədə bir əsas fikir göstər.
- Mətnə oxuma vaxtı ver.
- Keçidləri məlumatın məntiqinə uyğun qur.
- Şəkil, sxem və hərəkəti izaha xidmət etdiyi qədər istifadə et.
- **Uyğundur:** video-karusel, səssiz mikrodərs, qısa məlumat videosu.

### M14 — Təlim dərsi montajı
- Dərsin və təsdiqlənmiş danışığın məntiqi ardıcıllığını qoru; ayrıca hook yaratma.
- Səhv başlanğıcları, aydın təkrarları, texniki fasilələri və qeydlərə baxmaq üçün olan lazımsız gözləmələri çıxar.
- Ekspert cümləni yenidən deyib düzəldirsə, düzgün və tam variantı saxla.
- Mənalı pauzaları, vacib izahları və şərtləri saxla.
- Hansı ifadənin doğru olduğu aydın deyilsə (xüsusən tibbi və texniki mövzuda), özün seçmə: storyboardda göstər, təsdiq al.
- Kəsimləri görüntü və səs baxımından yumşaq birləşdir. Mənbə imkan verirsə, kəsimi gizlətmək üçün ölçülü yaxınlaşdırma və ya yenidən çərçivələmə istifadə et.
- Hər kəsimə animasiyalı keçid qoyma. B-roll, komedik effekt və sürətli Reels montajı yoxdur.
- **Ad–peşə yazısı (lower third):** yalnız təlim dərslərində və yalnız istifadəçi adı, soyadı və peşəni özü verəndə. Əvvəl bir neçə vizual variant şəkil kimi göstərilir; təsdiqlənən variant dərsin əvvəlində çıxır və bir neçə saniyədən sonra yox olur. Altyazını və üzü örtmür. Digər videolarda ad yazılmır.
- **Altyazı:** Montserrat (Azərbaycan hərfləri ilə), əsasən ağ, lazım olsa incə kölgə və ya zəif fon. Cümlələr məna üzrə bölünür və səslə dəqiq uyğunlaşdırılır. Söz-söz sıçrayan və ya karaoke animasiya yoxdur. Adlar, terminlər, rəqəmlər və hərflər yoxlanılır. Mümkün olduqda ayrıca SRT/VTT faylı da verilir. Altyazının videoya yazılması və ya ayrıca fayl kimi verilməsi storyboardda göstərilir.
- **İzahlı elementlər (mətn, siyahı, sxem, şəkil):** yalnız ehtiyac olan yerdə. Eksperti və altyazını örtmür. Fakt, təsnifat və şəkil uydurulmur. Dəqiq mətn və vizual storyboardda göstərilir.
- **Uyğundur:** növ 15; həmçinin uzun izahlı dərs formatında olan digər materiallar.

## Reklam üçün ayrıca qayda

Reklam bu yanaşmalardan biri və ya bir neçəsi ilə hazırlana bilər.

Hazır mətn təsdiqlənibsə:
- Mətnin ardıcıllığını qoru.
- Ayrıca hook çıxarıb əvvələ qoyma.
- Təklifin vacib hissələrini uyğun vizual üsulla aç.
- Qiymət, tarix, fayda, nəticə və çağırış uydurma.
- Struktur dəyişikliyi lazımdırsa, onu təklif kimi göstər və təsdiq gözlə.

## Təkrarın qarşısını almaq

- Brendin şrift və rənglərinin sabit qalması normaldır.
- Eyni girişi, yazı qutusunu, qrafik düzülüşü və effekt ardıcıllığını avtomatik təkrarlama.
- Müxtəliflik üçün mənasız effekt əlavə etmə.
- Son montaj seçimlərini qısa qeyd et (`experts/<id>.json` → `history`) və növbəti işdə nəzərə al.
- Vizual profil yoxdursa, neytral və oxunaqlı üslubdan istifadə et.

## Növ → yanaşma xəritəsi

| Video növü | Əsas montaj seçimləri | Vacib məhdudiyyət |
|---|---|---|
| 1 Kameraya ekspert danışığı | M01; lazım olsa + M02 və ya M03 | Hook, B-roll və hər cümləyə effekt avtomatik deyil |
| 2 Kadrarxası sual-cavab | M01; + M02 (sual ekranda mətn kimi) | Sual çıxarılırsa, cavab tək başına anlaşılmalıdır |
| 3 Hazır mətnli reklam | M01 + M02; xidmətin quruluşu üçün M03 | Mətnin ardıcıllığı qorunur; hook çıxarılmır; qiymət, tarix, nəticə və çağırış uydurulmur |
| 4 Seminardan çıxarış | Alt növə görə: izah → M03/M01; çıxış və hekayə → M07; auditoriya ilə sual-cavab → M01; nümayiş → M08 | Hissə kontekstsiz də anlaşılmalıdır; səbəb əlaqəsi təhrif olunmur |
| 5 Seminar və tədbir icmalı | M09 | Açılış, inkişaf və tamamlanma olmalıdır; yavaşlatma yalnız material imkan verəndə |
| 6 Fəaliyyət + ekspert səsi | M08; + M05 | Danışıq hərəkətlə üst-üstə düşür; vacib addım gizlədilmir |
| 7 İş prosesi, kameraarxası | M09; səsləndirmə varsa + M11 | Real proses göstərilir, səhnələşdirilmiş nəticə kimi təqdim edilmir |
| 8 Səsləndirməli hekayə və ya reklam | M11; + M04 | Təsdiqlənmiş səsləndirmə yenidən sıralanmır; stock görüntü sübut kimi təqdim edilmir |
| 9 Nağıl, animasiya | M12 | Obrazlar ardıcıl qalır; üslub storyboardda təsdiqlənir; olmayan imkan iddia edilmir |
| 10 Sürətli, əyləncəli sual-cavab | M10 | İlkin seçim yüngül yumordur; ekspert alçaldılmır, demədiyi fikir yaradılmır |
| 11 İki ekspertin söhbəti | M01; fikirlər qarşılaşırsa + M06 | Hər iki danışanın konteksti və bir-birinə münasibəti qorunur |
| 12 Hərəkətli kartlar | M13 | Bir səhifədə bir fikir; oxuma vaxtı verilir |
| 13 Material və ekran üzərində izah | M05; + M03 | Pəncərə materialı örtmür |
| 14 İştirakçı rəyi | M01 | Demədiyi nəticə montajla yaradılmır; rəyin konteksti qorunur |
| 15 Modul təlim dərsi | M14; lazım olsa + M03 (izahlı element) | Dərsin ardıcıllığı qorunur; şübhəli ifadə təsdiqsiz seçilmir; üfüqi dərs şaquliyə çevrilmir |
| 16 Motion graphics | M03; yüngül variant M01 + M03 | Qrafikada yalnız deyilən rəqəmlər |
| 17 Loqo animasiyası | — (planlaşdırılıb) | Loqo faylı olmadan qurulmur |

M06 (müqayisə) istənilən növdə iki variant göstərildikdə əlavə yanaşma kimi qoşula bilər.

### Son seçimlər (Aytən Calilova)

- Növ 1 danışıq videoları: **M01 + M02**. Altyazı, kənarda vurğular (pops), seçilmiş zoom; əlavə görüntü yoxdur.
- Növ 3 satış təlimi reklamı: **M01 + M02**. Mətnin ardıcıllığı qorundu, hook əlavə edilmədi; etirazlar ardıcıl vurğu kimi verildi.
- Eyni məkan və geyimdə çəkilən ardıcıl videolarda altyazı və vurğu üslubu dəyişdirilir.
