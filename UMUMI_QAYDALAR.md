# Ümumi qaydalar (bütün müştərilər)

> **Vacib qeyd (2026-11-25):** istifadəçinin təsdiqlədiyi **13 bölməli** `UMUMI_QAYDALAR.md` və `MUSTERI_SABLONU.md` bu repoda və görünən heç bir branch-də **yoxdur**.
> Bu fayl yalnız Adaptive Crystal Clear (və ona bağlı yoxlama/saxlama/təhlükəsiz sahə) bölmələrini ehtiva edir və həmin sənədin bölməsi kimi hazırlanıb.
> Orijinal 13 bölməli sənəd təqdim edilərsə, bu bölmələr ona **əlavə** olunacaq (əvəz etməyəcək); mövcud əvvəlki qaydalara toxunulmayıb.

Bu fayl **bütün müştərilər** üçün ortaq standartlardır. Müştəri profillərində (`templates/expert-reels/experts/`, `instagram-clients/`) təkrarlanmır;
müştəriyə məxsus istisna varsa yalnız profildə, bu fayla istinadla yazılır.

## Görüntü keyfiyyəti — Adaptive Crystal Clear Natural Look

**Məqsəd:** sanki eyni görüntü daha keyfiyyətli kamera və obyektivlə çəkilib — təmiz, kristal aydın, təravətli, təbii və premium; korreksiya nəzərə çarpmasın.

**Vizual referans (təsdiqlənib 2026-11-25):** `montaj/references/crystal_clear_v3/` (`reference_original.jpg` → `reference_v3.jpg`, `params.json`).
V3-ün real parametrləri orada qeyd olunub; onlar yalnız həmin kadr üçün seçilib və **heç bir videoya mexaniki tətbiq olunmur**.

**İş üsulu (standart, rəng təsdiqi soruşulmur, V1/V2/V3 alternativləri hazırlanmır):**
1. Montajdan əvvəl təmsilçi kadrlar analiz olunur (işıq, ağ balansı, dəri tonu, canlılıq, kontrast, kəskinlik, səs-küy).
2. Yalnız ehtiyac olan parametr V3 səviyyəsinə qədər tənzimlənir; yaxşı vəziyyətdə olana toxunulmur; mənbə artıq yüksək keyfiyyətlidirsə korreksiya yoxdur.
3. Tam renderdən əvvəl nümunə kadrlarda yoxlanılır; yalnız problem varsa həmin parametr azalır.
4. Eyni işıq və məkan üçün parametrlər təkrar istifadə oluna bilər (keş), hər videoda uyğunluq yenə yoxlanır.
5. Yekun renderdən sonra texniki yoxlama: kadrlar arası işıq/rəng sıçrayışı, rəng sürüşməsi, kəskinlik (`python -m montaj.crystal check <orijinal> <nəticə>`).

**Alət:** `montaj/crystal.py` (montaj sisteminə qoşulub: plan `"look"` standartı `CRYSTAL`; `templates/expert-reels/pro/talk.py`, `editorial.py`, `build.py`).
CLI: `python -m montaj.crystal analyze <video>` · `sample <video> --start S --dur D --out x.mp4` (hərəkətli nümunə + yoxlama).

**Qadağalar:** qırmızılıq, sarılıq, göyümtüllük, solğunluq · dəri tonunun və üz cizgilərinin dəyişməsi · süni kəskinlik, plastik dəri, HDR effekti ·
rəng temperaturuna səbəbsiz müdaxilə · süni detal, upscaling, ağır AI emalı · kadrlar arası rəng/işıq sıçrayışı · orijinal fonun dəyişməsi.

**Açıq məhdudiyyətlər:** hədlər 3 çəkiliş mühitindən (Xəyyam) kalibrlənib — yeni müştəridə ilk videonun nümunə kadrı yoxlanılmalıdır; HDR mənbədə avtomatik korreksiya yoxdur;
çəkilişdə pozulmuş ağ balans avtomatik düzəldilmir, yalnız xəbərdarlıq verilir; mənbədə olmayan detal yaradılmır.
Üslub presetlərinin öz `color` zənciri (məs. `kinematik`) varsa, o ayrıca yaradıcı qərardır və bu standartı əvəz edir.

**Ləğv edilənlər:** Xəyyam Həsənov üçün C/H/W məcburi filtr seçimləri; "rəng həmişə looks C" qaydası; `looks` əmri ilə variant seçimi (əl ilə müqayisə üçün qalır, standart deyil).

## Adaptive Crystal Clear — əlavə qaydalar (2026-11-25)

**Tətbiq sırası:** görüntü korreksiyası altyazı, kart və qrafikdən **əvvəl** tətbiq olunur (brend rəngləri dəyişməsin). Kinematik və s. üslub presetləri bu standartı özbaşına əvəz etmir;
preset öz rəng zəncirini yalnız istifadəçi açıq şəkildə seçibsə tətbiq edir.

**Yekun keyfiyyət yoxlaması (montajlı video):** `montaj.crystal.aligned_check` — hər nümunə kadr üçün mənbədə uyğun an tapılır (kəsimlər), eyni zoom/kadraj tətbiq olunur,
nəticə yalnız təmiz sahədə müqayisə olunur (altyazı kartı, kartlar, qrafik elementləri və tam ekran vaxtları çıxarılır). Yoxlanır: işıq/rəng sürüşməsi və kadrlar arası dalğalanma,
dəri R/G, ağ balans, doyma, kəskinlik. Orijinalla eyni saniyədə sadə müqayisə (`check`) yalnız kəsimsiz nümunədə mənalıdır.

**Avtomatik həll olunmayan hallar** (korreksiya edilmir, görüntü korlanmır, xəbərdarlıq verilir — `XƏBƏRDARLIQ [crystal]`):
HDR mənbə (əvvəl tone-map lazımdır) · çəkilişdə pozulmuş ağ balans (neytral sahənin R/G və B/G 6%-dən çox sapması) · qarışıq işıq mənbələri · çox yüksək səs-küylü mənbə (təmizləmə həddi 4.0-dır) ·
mənbədə olmayan detalın bərpası (upscaling/AI yoxdur) · yoxlama keçməyəndə — korreksiya söndürülür.

**Yeni müştəri — ilk video üzərində qısa kalibrasiya:** (1) `python -m montaj.crystal analyze <video>` — rejim və qərarlar; (2) `python -m montaj.crystal sample <video> --start S --dur 5 --out x.mp4` —
5 saniyəlik hərəkətli nümunə + hərəkət yoxlaması; (3) nəticə yoxlanılandan sonra müştəri üçün keş (`crystal_cache.json`) təkrar istifadə olunur; hədlər yeni mühitdə problem göstərsə yalnız həmin müştərinin parametri düzəldilir,
ümumi hədlər dəyişdirilmir. Kalibrləmə nəticəsi 3–5 sətirlə qeyd olunur.

**Referansın saxlanması:** müştərinin **üzünün göründüyü şəkillər repoya yazılmır** (`.gitignore`: `*_FACE.*`, `reference_original.jpg`, `reference_v3.jpg`). Repoda yalnız üzsüz kəsik (arxa fon/rəf) və rəqəmsal
barmaq izi (`params.json`: parlaqlıq, kəskinlik, səs-küy, doyma, dəri R/G) saxlanır. Üz referansı istifadəçinin şəxsi, qapalı yaddaşında (məs. şəxsi Drive qovluğu) saxlanmalıdır; yerli surət
`instagram-clients/<müştəri>/` (gitignored, mühit sıfırlananda itir). Müştəri nümunələri/render faylları da repoya yazılmır.

**Instagram təhlükəsiz sahə (1080×1920, təxmini — platforma interfeysi dəyişə bilər):** yuxarı ~250 px, aşağı 1500 px-dən sonrası və sağ ~960 px-dən sonrası interfeys elementləri üçündür;
altyazı, kart və başlıq bu sahələrə girməməlidir. Üzü, ağzı və vacib jestləri örtmə.

**Müştəri tarixçəsi:** profilin `history` hissəsində yalnız real videoların **yekun** versiyası saxlanır; render variantları və aralıq versiyalar `templates/expert-reels/experts/_arxiv/` altında arxivləşdirilir.

## Hazır studiya: sessiya, kitabxana, rejissor, kadraj (2026-11-25)

**Sessiya başlanğıcı (soruşma, "yoxdur" demə):** `python -m montaj.doctor` — bir əmr: yoxlayır, çatışanı `--fix` ilə özü qurur, bir sətir nəticə verir. Mühitin quraşdırma skripti
(`scripts/cloud-setup.sh`) təzə konteynerdə asılılıqları qurur; fərdi açarlar (Pixabay/Freesound) isteğe bağlıdır.

**Kitabxana (musiqi, B-roll, SFX):** `montaj/library/catalog.json` (kiçik kataloq, repoda) + fayllar lazım olanda endirilir (`python -m montaj.library search|get|sync`).
Mənbələr: Mixkit (pulsuz lisenziya, mühit şəbəkəsində açıq) və istifadəçinin Drive qovluğu **"OpenMontage Kitabxana"** (2026-11-25-dən yeni Drive hesabı; köhnə hesab bağlantısı kəsilib) (`musiqi/`, `broll/`; fayl adı `teq1_teq2_ad.ext`;
qovluq "Linki olan hər kəs — Baxan" olmalıdır; sonra `sync`). Mixkit kataloqu avtomatik yığılıb (`python -m montaj.library seed` + `probe`): ~360 B-roll (çoxu üfüqi 1280×720 — pəncərə kimi; ~30 şaquli 720×1280 — `search --orient vertical`, tam ekran) və ~100 musiqi. İstifadəçi fayl yükləmir; kitabxananı agent özü genişləndirir. Drive qovluğu isteğe bağlıdır.
Müştəriyə məxsus və ya məxfi material bu ortaq kitabxanaya qoyulmur.

**Musiqi qaydası müştəri profilindədir** (`music_policy.use: true|false` + əhval/lisenziya). Qayda yazılmayıbsa — musiqisiz, soruşulmur.

**Rejissor:** hər video üçün montajdan əvvəl konsept seçilir (`skills/meta/edit-director.md`, `python -m montaj.director brief`). "Oturub danışır, düz edit" avtomatizmi yoxdur;
düz edit yalnız əsaslandırılıb seçilir. Konsept 5–8 sətirdir; storyboard/alternativ/uzun hesabat yoxdur (müştəri profili tələb edənə qədər).

**Kadraj standartı (`montaj/framefix.py`):** əyrilik düzəlir; oturduğu xəttdən kəsilir (ayaq/diz kadrda görünürsə omba+6%, yaxınlaşma həddi 1.6×); omba masa/kadr tərəfindən örtülürsə kəsmə yoxdur
(masa aşağıda görünə bilər); başın üstündə ~10% boşluq (müştəri profili kart üçün artıra bilər). Əl kamerası hərəkəti izlənmir (sabit kamera fərziyyəsi).

**Rəngdə ağ/qara nöqtə:** nümunə və yekun yoxlama qara nöqtənin 3-dən çox qalxmasını (bulanıq qara) və ağ nöqtənin 4-dən çox enməsini (solğun ağ) problem sayır.

**Drive (2026-11-25):** bütün giriş materialı (video linkləri, kitabxana) və kitabxana yeni Drive hesabından götürülür. Hazır videolar üçün qovluq: **"OpenMontage Hazır videolar/<müştəri>"**.
Məhdudiyyət: Drive bağlantısı (MCP) bir fayl üçün **10 MB**-a qədər yükləməyə icazə verir — tam keyfiyyətli MP4 (40–60 MB) bu yolla Drive-a yüklənə bilmir; hazır video söhbətə fayl kimi göndərilir.

**Mənbə siyasəti (kitabxananı agent özü yığır):** Mixkit — bəli (pulsuz lisenziya, açar lazım deyil, birbaşa Mixkit-dən endirilir, Drive-a yüklənmir). Pexels/Pixabay — yalnız pulsuz API açarı və mühit şəbəkə icazəsi olduqda
(açar istifadəçi tərəfindən mühitə verilir). **Pinterest — istifadə olunmur:** məzmun üçüncü tərəfin müəllif hüququ altındadır, lisenziya göstərilmir, avtomatik yükləmə şərtlərə ziddir; mühitin şəbəkəsində də bağlıdır.

**Referans video linki (Instagram):** `watch-skill` (üçüncü tərəf, MIT; `third_party/watch-skill`, ayrıca `.venv-watch`) — qaydalar `skills/meta/video-reference-analyst.md`-dədir.
Məhdudiyyət: video baytları üçün dinamik CDN alt-domenlərinə (wildcard) mühit icazəsi lazımdır; yoxdursa yalnız altyazı/transkript.
