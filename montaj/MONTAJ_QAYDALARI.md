# Montaj qaydaları — TƏK MƏNBƏ (hər videoda məcburi)

Drive linki + montaj sorğusu gələndə **yalnız bu fayl** oxunur. Başqa qayda faylına baxmaq lazım deyil (köhnə qayda faylları silinib). `IS_AXINI.md` yalnız
**əmr istinadıdır** (fx, bg, karusel, seminar, kurs, tədbir və s. necə işlədilir); ziddiyyətdə bu fayl keçərlidir.
Müştəri profilindən (`templates/expert-reels/experts/<ad>.json`) yalnız **müştəriyə aid** olanlar götürülür: rəng ailəsi, şrift,
ad/titul, lüğət və müştərinin istifadəçi tərəfindən təsdiqlənmiş öz məhdudiyyətləri. "Araya kadr/B-roll yoxdur" kimi qadağa profilə yazılmır: B-roll və animasiya hər videoda storyboardda təklif olunur, lazımdırsa qoyulur, lazım deyilsə qoyulmur — qərarı istifadəçi verir. Ümumi qayda profilə yazılmır.

## 1. İş axını
1. Link gələndə ilkin sorğu yoxdur. Yalnız müştəri adı bilinmirsə onu soruş. Qovluqda bir neçə video varsa — **ardıcıl**, hər biri ayrı.
2. `new --title "<ad>" --link "<link>" --client "<Profil adı>" --type <N>` → `storyboard <pid> --quick` → `framefix` → `voice-clean`
   → transkripti oxu (`retakes` köməkçidir) → `music`.
3. **Hər video üçün 3 storyboard variantı (məcburi; mövzu imkan verirsə 5-ə qədər).** Variantlar bir-birindən tamamilə fərqli montaj üslubu olmalıdır
   (montaj növü, animasiya ilə cümləyə bağlı və ya birbaşa kadr dəyişmə, hook üsulu, ritm, tipoqrafiya, musiqi) — yalnız rəng/mətn fərqi yox.
   **Üslub dəstləri:** hər variant FƏRQLİ dəstdən qurulur (`python -m montaj.kits list`: classic, editorial, colorblock, handnote, kinetic).
   `storyboard` çıxışı müştərinin son/rədd edilmiş dəstləri xaric 3 dəst təklif edir. Plan parçası:
   `python -m montaj.kits build <dəst> content.json --theme theme.json` (məzmun YALNIZ danışıqdan; dəst qrafika, altyazı, SFX və hamar zoomu verir).
   `variants` fərqi yoxlayır (`montaj/difference.py`: fərqli dəst + 7 oxdan ≥4-də fərq) və müştəri yaddaşına baxır (`montaj/memory.py`); uyğunsuzluqda
   dayanır (`--force` yalnız istifadəçi bilərəkdən istəyəndə). Rəngdən başqa hər şey fərqli olmalıdır.
   **Hero videolar (reklam, brend, vacib bir video):** variantlardan ən azı biri bəzək rejimində olur — həmin videoya xas, sıfırdan yazılmış səhnə
   (`montaj/atelier.py`, `skills/creative/atelier-scenes.md`); hazır `scenes` şablonundan kopyalama yoxdur. Müddəti storyboardda yazılır.
   **Referans:** istifadəçi nümunə video verəndə `python -m montaj.refstyle analyze <video> --name <ad> --sheet-dir <qovluq>` → kontakt şəklinə bax,
   `decide` ilə qərarları yaz (hook, tipoqrafiya, keçid, B-roll, səs, retention). Qərarlar istifadəçi təsdiq edənə qədər (`approve`) fərziyyədir;
   yalnız təsdiqlənənlər planlaşdırmada istifadə olunur. Referans kopyalanmır, video/kadr/transkript repoya yüklənmir (`skills/creative/reference-learning.md`).
   Variantı ən keyfiyyətli, ən maraqlı və izləyicini sona qədər saxlayan formada qur — **render vaxtına görə sadələşdirmə**. Hər variantın yanında:
   **təxmini montaj müddəti** və bu video üçün **niyə** seçilib (reklamda — hansı daha çox geri dönüş gətirər). Qərar istifadəçinindir.
   `variants <pid> A.json B.json C.json` → `storyboard_variantlari.jpg` (360p proksidən, saniyələr; video önizləmə üçün `--mp4`).
   **Hər təklif həm yazılı, həm şəkilli göndərilir** (heç vaxt yalnız mətn). `fx` (arxada yazı, sticker və s.) olan variantda onun şəkli ayrıca: `fx <pid> --preview --spec '{...}'` → `effektler.jpg` (~7 s); `variants` önizləməsi `fx`-i göstərmir.
   Göndər: storyboard şəkli + variant izahları + 2–3 musiqi nümunəsi + `kadraj.jpg` + material qeydləri. İstifadəçi ilə birlikdə seçilir.
4. Seçimdən sonra: `choose <pid> <plan.json>` → `render <pid>` (preflight daxildir) → `verify <pid>` → yekun `_ig.mp4` + 2–4 sətir.
5. İstifadəçi təsdiq edəndən sonra: `choose <pid> --remember [--rejected kit1,kit2]` (profilin `history`, `approved`, `rejected` sahələrinə yazır; təsdiqsiz və fərziyyə heç nə yazılmır). Son 2 videoda işlənmiş və rədd edilmiş dəst təklif olunmur.
5a. **Preflight 4 avtomatik yoxlama edir (`montaj/checks.py`, əl ilə yoxlama lazım deyil):** (1) kəsim sərhədləri — söz yarımçıq kəsilirsə/son hecası riskdədirsə xəbərdarlıq; (2) danışıq səsi — `voice-clean` səsi boğursa (2–8 kHz −3.5 dB-dən çox azalıb) avtomatik orijinal səsə qayıdır; (3) kadraj — üz mərkəzdən ±4%-dən çox sapırsa avtomatik mərkəzləşdirir; baş üstü boşluq/üz ölçüsü rəqəmlə yoxlanır; (4) rəng — dəri tonunda qırmızılıq/sarılıq/solğunluq, klipler arası işıq fərqi və `look` hədləri. "bad" qalanı render-dən əvvəl düzəlt, "warn" olanı nəzərdən keç.
6. **Tam render bir dəfə.** Səhvlər renderdən əvvəl (variants, preflight) tutulur. `verify` yalnız yekun faylda, bir dəfə.

## 2. Hər videoda məcburi
**Kadr.** `framefix`: əyrilik düzəlir, obyekt ortalanır, baş üstü, aşağı və yan boşluq ayarlanır; uzaqdan çəkilibsə düzgün yaxınlaşdırılır
(≤1.12x, çoxu lazımdırsa bunu yaz). Yazı və kartlar bədənin böyük hissələrini örtmür; yer lazımdırsa kadr 2 hissəyə bölünür
(danışan bir hissədə, element digərində). Üz heç vaxt örtülmür.

**Element növbəsi (B-roll, animasiya, kart, birbaşa kadr dəyişmə).** Element girəndə ya tam kadr dəyişir (ekspert görünmür —
ya B-roll, ya animasiya), ya kadr bölünür; yarıörtmə yoxdur. Dəyişiklik **fikir bitəndən sonra** olur. 0.1–1 s göstərilən
element və ya ekspert olmaz: element ən azı ~2 s, elementlər arasında ekspert ən azı ~2 s. Bəzi videoda animasiya danışıqdakı
cümlələrə bağlı ekranda gəlir, bəzisində birbaşa kadr dəyişir — **videoya və mövzuya görə sən seç**. "Hər videoda B-roll/animasiya
olmalıdır" və ya "hamısı dümdüz olmalıdır" kimi qayda yoxdur.

**Hook və axıcılıq.** İlk saniyələr `skills/creative/hook-design.md` ilə seçilir (üsul + səbəb 1 cümlə); danışığın sırası dəyişmir.
Video başdan sona izləyicini saxlamalı, dinamik olmalıdır — mexaniki "hər N saniyə effekt" yoxdur, dinamika məzmundan gəlir.
`skills/creative/broll-function.md`: hər elementin funksiyası və izah etdiyi fikir var; yoxdursa qoyulmur.

**Kəsim və pauza.** Yalnız təkrar, alınmayan cəhd və kənar söhbət çıxır. Söz və heca kəsilmir. Vurğu yaradan və ya fikri anlamağa vaxt
verən pauza qalır; saniyə həddi ilə mexaniki kəsim yoxdur. Arxa səs kəsiləndə/təmizlənəndə ekspertin səsi dəyişmir (`voice-clean`).

**Zoom və keçidlər (MƏCBURİ — icra statusu §4; icra olunana qədər də qayda qüvvədədir, §4-dəki əvəzi tətbiq olunur).** Zoom yalnız hamar və yumşaq olur: planda `zooms` standart olaraq hamardır (smoothstep yaxınlaşma + qısa hamar geri çəkilmə, `scale` ≤1.12), `multicam` calm da hamardır. `smooth:false` (sıçrayış) işlədilmir.
Kəsimdə keçid hiss edilməməlidir: kəsim cümlə sərhədində, səsin ən sakit yerində, 12 ms səs keçidi, lazım olsa J/L-cut. Sərt sıçrayış yoxdur.

**Altyazı.** `skills/creative/caption-typography.md`: 4 rol ayrıdır (altyazı, hook, vurğu, CTA); Azərbaycan hərfləri düzgün; ≤2 sətir;
safe zone; mətn bloku enin ≤86%-i; kontrast kifayət qədər. ASR səhvləri `corrections` ilə düzəlir; mənanı dəyişən təxmin yoxdur — şübhəli sözlər siyahıda.

**Musiqi.** Standart olaraq VAR (yalnız istifadəçi bu müştəri/video üçün "yox" deyibsə istisna). Dinamik və sahəyə uyğun (uşaq/ana → şən kids;
təhsil/reklam → educational/corporate; hekayə/psixologiya → mövzuya uyğun, amma yavaş piano və kədərli yox). Yalnız CC0 və Mixkit; CC-BY və
qeyri-kommersiya yox. Planda `volume`/`vol` yazma — `"auto"` (danışıqdan ≈16 LU aşağı).

**SFX.** Videoya və vizual elementə uyğun seçilir; hər SFX bir elementə bağlıdır; element silinirsə SFX də silinir; köhnə versiyadan qalan SFX olmur.

**Rəng.** `look: auto`. Şablon, müştəriyə bağlı sabit filtr, saturation artımı, üz/dəri emalı yoxdur. Brend rəngi yalnız altyazı və qrafikaya aiddir.

**Çıxış.** Instagram üçün 1080x1920 (4K göndərilmir), H.264, −14 LUFS, pik ≤−1.5 dBTP. Zəmanət ("sıfır keyfiyyət itkisi", ölçülməmiş vaxt) verilmir.

**Dürüstlük.** Qiymət, tarix, əlaqə, rəqəm, çağırış, titul yalnız danışıqdan/profildən/istifadəçidən. Real olmayan məkan həqiqi kimi göstərilmir.
Müştəri mediası, transkript və şəxsi məlumat GitHub-a yüklənmir.

**Davamlılıq.** Müştərinin rəng ailəsi sabit; hook, altyazı üslubu və kart ardıcıllığı son 3 videodan (`history`) fərqli (`variation`).

## 2a. İstifadəçi düzəlişlərindən öyrənilmiş qaydalar (MƏCBURİ — hər videoda ilk render-dən ƏVVƏL yoxla)
Bunlar real videolarda istifadəçinin dəfələrlə düzəltdiyi səhvlərdir; yeni videoda təkrar olunmamalıdır. Agent qulaqla dinləyə bilmir — ona görə
aşağıdakı yoxlamalar ölçü ilədir və şübhəli yerlər istifadəçiyə saniyə ilə bildirilir ("səs qulaqla yoxlanmayıb").

**Kəsim seçimi.**
1. Hər cümlə üçün SON təkrar götürülür (istifadəçi sonuncunu ən yaxşı sayır). Yalnız sonuncuda büdrəmə/yarımçıq varsa əvvəlki tam çəkiliş götürülür və bu təhvildə açıq yazılır.
2. Vahid = tam cümlə (və ya tam fikir). Cümlənin ortasından başlamaq/bitmək, birinci cəhdin qalığı, "əh", "yox, nəsə…" olmaz.
3. Whisper söz vaxtlarına GÜVƏNMƏ (0.5 s-ə qədər sürüşür, uzun sözləri uzadır). Sərhədi ölçülmüş enerjiyə görə qoy: başlanğıc sözün başlamasından ~0.1–0.15 s əvvəl, sakitlikdə (<−48 dB); son səs sönəndən sonra, sakitlikdə. Sözün sonu (məs. "-dir", "-ır") kəsilməməli: son hecanın enerji quyruğu bitənə qədər saxla.
4. Hər kəsimin başında/sonunda 0.3 s-dən qısa təcrid olunmuş səs parçası (arxasında ≥0.25 s sakitlik) kənar səs və ya yarımçıq başlanğıcdır ("Da", "Əm", nəfəs, düşünmə səsi) — sərhədi onun o tayına çək. Preflight `kəsim səsi` yoxlaması (checks.cut_audio_scan) bunu avtomatik tapır; xəbərdarlıq qalırsa render etmə.
5. Cümlənin içindəki pauza təbii nitqin hissəsidir, kəsmə. Yalnız cümlələr ARASINDAKI uzun sakitlik qısaldıla bilər — və ancaq sakitlikdə kəsim + yumşaq keçidlə.
6. Müddət: reklam ≤60 s (istifadəçi başqa demirsə). Sığmırsa tam cümləni çıxar, yarım cümlə saxlama.

**Keçidlər.** Hər real kəsimdə (başqa mənbə yeri) hamar keçid məcburidir: planda `"dissolve": {"auto": "all", "dur": 0.3}` və həmin kəsimlərə bağlı danışıq səsi klipinə
`fadeIn`/`fadeOut` ≈ 0.08 s (12 ms klik qorumasıdır, keçid deyil). Kəsimin özü sakitlikdə olmalıdır. İstifadəçi sərt/ani keçidləri qəbul etmir.

**Kadr.** Sabit kamera: `frames` bir açar (cx, cy), hərəkət/izləmə/zoom sıçrayışı yox. Əyrilik: fonda şaquli xətlər (pərdə, divar küncü) varsa `checks.measure_tilt(video, times)` ilə ölç və
`rotate`-i (saat əqrəbi +) həmin qədər qoy; yekun videoda yenidən ölç (≈0° olmalıdır). Fonda xətt yoxdursa istifadəçiyə "əyrilik ölçülmədi" yaz, təxmini çevirmə. Üz kadrın hündürlüyündən ~41–45%-də;
yuxarı kartlar üçün baş üstü boşluq lazımdır: kartın alt kənarı ilə başın ən yüksək nöqtəsi arası ≥3% (yoxsa kadrı aşağı sal, kartı kiçilt, 3 sətirdən çox yazma).

**Üst yazı/kartlar.** Montserrat. Yazı başa/üzə/bədənin böyük hissəsinə düşmür; kart vaxtı altyazı qoyulmur (kart aşağıdadırsa) və ya kart yuxarıda qalır. Elementlər üst-üstə düşmür (bitmə ilə növbəti başlama arası ≥0.1 s) və hər biri ≥1.3 s görünür.
Ayırıcı nöqtə (•/·) HEÇ VAXT sətrin sonunda qalmır — həmişə növbəti elementin əvvəlində ("Montessori\n• oyun əsaslı məşğələlər"; `type` inline siyahısında kod bunu avtomatik edir). Mətn danışıqla uyğundur (qrafikanın vaxtı sözün deyilmə anına görə, mənbə vaxtından çevrilir).
**Altyazı mətninin düzgünlüyü (ASR səhvləri).** Səbəblər: müştəri profilində `glossary` boş idi (Whisper-ə terminlər verilmirdi), uzun kontekstli tanıma səhv sözü təkrar edirdi, ə/e, ğ/x/q kimi hərflər qarışırdı.
Qayda: (1) hər yeni müştəridə İLK videodan əvvəl profilin `glossary.terms` (işlədilən terminlər, düzgün yazılışla) və `glossary.fixes` (tez-tez rast gəlinən ASR səhvi → düzgün) doldurulur; `new --client` terminləri hotwords kimi Whisper-ə verir.
(2) Tanıma `beam_size=5`, `condition_on_previous_text=False`, VAD ilə işləyir; ə/e, ğ/x/q fərqli yazılışlar lüğətə `transcribe.snap_glossary` ilə avtomatik düzəlir. (3) Təhvildən əvvəl `python -m montaj.captionqa <pid> <yekun.mp4>`: yekun səs iki modellə (turbo + large-v3) oxunur, hər iki model başqa eşitdiyi altyazı sözləri
siyahı ilə təhvildə istifadəçiyə yazılır ("bu sözləri təsdiq edin"). (4) Şübhəli sözü (ASR "dəst", mənaca "dərs" kimi) təxmin edib yazmaq olar, amma təxmin edildiyi açıq deyilir; mənanı dəyişən təxmin yoxdur.
Sınaq nəticəsi (Rəhimə, 4 video): söz xəta dərəcəsi lüğətsiz/əvvəlki ayarla ≈0.47 (small) və ≈0.15 (turbo) → turbo + lüğət + yeni ayarla ≈0.10; large-v3 yalnız ≈0.09 (3× yavaş) — turbo saxlanılır.
Altyazı sözləri `candidates` sözlərindən qurulur — ASR səhvləri (məs. "baxçıb əlum") həm `analysis`, həm `candidates`-də düzəldilməlidir, yoxsa altyazıda səhv çıxır.

**Fon.** Standart olaraq təbii. Fon bulanıqlaşdırma/qaraltma (`fx focus`) YALNIZ istifadəçi istəyəndə; bulanıqlıq əl/qol ətrafında maska kənarı verir və "peşəkar görünmür" sayılır. Qaraltma (`dim`) kənarı daha az göstərir.

**Rəng.** `look: auto` + yalnız `sharpen 0.65` (+ avtomatik ton). Əlavə gamma/kontrast/denoise/şablon yoxdur (istifadəçi bunu rədd edib; saf auto təsdiqlənib).

**Musiqi.** Standart VAR. Seçərkən trekin ilk 8 s-nin səviyyəsinə bax (`ebur128`): başlanğıcı sakit olan trek ilk saniyələrdə eşidilmir. Planda `"under": 12` (danışıqdan 12 LU aşağı; standart 16 çox sakit sayılır), `fadeIn ≤0.5`, `fadeOut ≈2.5`. Eyni müştərinin ardıcıl videolarında fərqli trek.

**Yekun fayl (finalize).** İki keçidli `loudnorm=I=-14.5:TP=-2.2:LRA=11`, `-c:v copy -c:a aac -b:a 192k -ar 48000 -t <VİDEO müddəti>`. Danışıq səsinə `afade`/söndürmə QOYMA (sonuncu sözləri öldürür; yalnız musiqi sönür).
Audio və video müddəti eyni olmalı (`verify` fərqi göstərir; `-t` ilə video müddətinə kəs).

**Təhvil yoxlaması (hər videoda).** (1) tam səsi ASR et — təkrar/yarımçıq cümlə yoxdur; (2) preflight-da `kəsim səsi` və `kəsim sərhədləri` təmizdir; (3) yekun videoda əyrilik ölçüsü ≈0; (4) 8–10 kadr kontakt şəkli: kartlar başı örtmür, altyazı/kart toqquşmur, nöqtələr sətir əvvəlindədir; (5) müddət ≤60 s; (6) təhvil mətnində qulaqla yoxlanmadığı, çıxarılan hissələr, seçilən musiqi və qalan xəbərdarlıqlar yazılır.

## 3. YALNIZ istifadəçi deyəndə
Güzgü çevirmə (`hflip`), arxa fonu bulanıqlaşdırma/dəyişmə, ödənişli xidmət və API, hazır rəng şablonu.

## 4. Hazırda sistemdə YOXDUR (əvəzi)
- **Dəstlər çatmır:** istifadəçi `colorblock`, `kinetic`, `handnote`, `intertitle`-i rədd edib (`montaj/kit_decisions.json`); `editorial`, `frame` seçilib/təsdiqlənib. İcazə verilən dəstlər: `editorial`, `frame` (Çərçivə) və Apple üslublu şüşə dəstləri `milkglass` (süd şüşəsi kartı), `notification` (iOS bildiriş bannerı), `glasscaps` (şüşə kapsullar), `pblur` (mütərəqqi bulanıqlıq + keynote yazı) — hamısını istifadəçi seçdi — və təhlükəsiz baza `classic`. **Kamera vizörü** (`hook.viewfinder=true`: ● REC + taymkod, yalnız yuxarı künclər) HƏR dəstdə mümkündür; mövzuya uyğundursa (kamera arxası, etiraf, sirr) agent seçir, hər videoda deyil. Şüşə dəstləri üçün `content.brand_name` (profil adı) verilir. `intertitle` də rədd edildi (qeyri-peşəkar, premium deyil). 3 fərqli variant üçün çatışmayan variantlar YENİ üslub dəsti (fərqli dizayn dili, ≥4 oxda fərq) və ya bəzək rejimində (atelier) yazılmış variant kimi təklif olunur; rədd edilmiş dəst təklif olunmur. Yeni dəst təklifi əvvəl şəkil (eskiz) kimi göstərilir, istifadəçi bəyənəndən sonra qurulur.
Bunlar qaydadan azad etmir: §2-dəki qaydalar məcburidir, kod isə ayrıca işdir. İcra olunana qədər aşağıdakı əvəzi tətbiq olunur və təhvildə bunun hələ tam hamar olmadığı açıq yazılır.
- **Hiss edilməyən video keçidi (MƏCBURİ qayda, icra olunub):** danışıq kəsimində dissolve yoxdur → cümlə sərhədində, səsin ən sakit yerində kəsim + 12 ms səs keçidi + J/L-cut; yumşaq video keçidi (dissolve) İCRA OLUNUB: planda `"dissolve": {"auto": "broll", "dur": 0.2}` (B-roll giriş/çıxışı) və ya `"at": {"<növbəti klip id>": 0.3}` (konkret sərhəd). Ümumi müddət və səs dəyişmir; mənbədə ehtiyat yoxdursa və ya klip 4×yarım-keçiddən qısadırsa kəsim qalır. Danışıq kəsimləri də (başqa mənbə yeri) §2a-ya görə `"dissolve": {"auto": "all", "dur": 0.3}` ilə yumşaldılır (istifadəçi təsdiqləyib: sərt kəsim 'ani' sayıldı). Eyni mənbədə davamlı sərhədlərdə keçid qoyulmur. (Hamar zoom da var.)
- **Dəstlərin məhdudiyyəti:** `colorblock` paneli kadrın yuxarı ~30%-ni, `kinetic` zolaqları isə yuxarı 5% və aşağı 24%-i örtür (video miqyaslanmır, üz yoxlanmır, əllər zolağın altında qala bilər); `handnote`/`editorial` yazıları başın üstündə yer tutur. Kadrda baxıb yoxla; bədən örtülürsə yer/ölçünü dəyiş və ya kadrı böl.
- **Bədən örtülməsi yoxlaması:** `verify`/preflight yalnız üzü yoxlayır → vizual kadrda özün yoxla, kart bədəni örtərsə kadrı böl.
- **Element ≥2 s qaydası:** preflight xəbərdarlıq edir, avtomatik düzəltmir → planda vaxtları özün düzəlt.

## 5. Plan faylı (şablon — mətnləri danışıqdan yaz)
```json
{
  "approach": "M01+M02", "title": "<qısa ad>",
  "variation": {"tone": "...", "primary": "#...", "primaryDeep": "#...", "captions": "box", "anim": "pop"},
  "corrections": [{"from": "<ASR səhvi>", "to": "<düzgün>"}],
  "captions": {"enabled": true},
  "graphics": [{"type": "title", "text": "<hook sualı>", "start": 0.15, "dur": 4.5, "y": 0.19}],
  "sfx": [{"kind": "pop", "t": 0.2}],
  "music": [{"start": 0.0, "volume": "auto", "fadeIn": 1.2, "fadeOut": 2.0, "duck": true, "file": "<music çıxışındakı fayl>"}],
  "look": "auto"
}
```
`variation` `storyboard` çıxışındakı təklifdən götürülür. Qrafika `y`-ləri preflight-da interfeys zonasına görə avtomatik düzəlir.
Azərbaycan dili: `ə ğ ı İ ö ü ş ç` şriftdə olmalıdır; `i→İ`, `ı→I` (`lib/az_text`); rəqəmlər `1 200`, `4,5`.
