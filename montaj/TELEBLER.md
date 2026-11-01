# Montaj paneli — tələblər siyahısı (izlənən)

Status açarları:
- ✅ **hazır + yoxlanılıb**: avtomatik test və ya brauzer testi ilə yoxlanılıb (sintetik materialla)
- 🟡 **hazır, real cihaz/material ilə yoxlanılmayıb**
- ⛔ **çatışmır / maneə var**: səbəbi yazılıb

Son yeniləmə: v2 (telefon axını). Hər commit-də bu fayl yenilənir.

Yoxlama əsası: `tests/montaj/` (Node 12, pytest 19) və brauzer testləri `e2e_flow.mjs`, `e2e_browser.mjs` (Chromium + iPhone ölçüsü emulyasiyası — real Safari deyil).

## 0. Büdcə və telefon yolu (v3)
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 0.1 | Əlavə ödənişli xidmət aktivləşdirilmir (VPS, API, hosting, saxlama) | ✅ | Heç biri aktiv deyil |
| 0.2 | Yalnız iPhone ilə bir videonu başdan sona hazırlamaq | 🟡 | Seçilən yol: Claude Code sessiyası + `montaj.session` CLI (`BUDCE_YOLU.md`). Real iPhone və real video ilə yoxlanılmayıb |
| 0.3 | Drive linkindən orijinal fayl (sessiyada) | 🟡 | Drive serverinə çıxış var; real paylaşımlı fayl ilə yoxlanılmayıb |
| 0.4 | Sessiyada hazırlanmış plan panel layihə faylı kimi | ✅ | `export` panelin öz `montaj.json` formatını verir (test) |
| 0.5 | Brauzerdə tam montaj paneli telefondan | ⛔ | Pulsuz daimi server yoxdur. Yerinə: telefon redaktoru (0.6) |
| 0.6 | Telefonda interaktiv redaktor (claude.ai artifact, sessiyadan dərc olunur) | 🟡 | Dərc olundu, önizləmə videosu artifact-ın şəxsi asset yerində; səhifənin db-yə yazdığı düzəliş sessiyada oxunub tətbiq olundu (cihaz məlum deyil). Real iPhone Safari/Claude tətbiqində təsdiqlənməyib |
| 0.7 | Yazını barmaqla başqa yerə çəkmək; yalnız o yazı dəyişir; render-də eyni yer | ✅ | Emulyasiya + render testi |
| 0.8 | Klipin başlanğıc/sonunu uzadıb kəsilmiş hissəni qaytarmaq; öz səsi sinxron; sonrakı kliplər, bağlı yazı və subtitrlər uyğunlaşır | ✅ | Emulyasiya + render sinxron testi (0 ms) |
| 0.9 | Düzəlişlər sabit ID və layihə versiyası ilə; köhnə/yanlış layihə aşkarlanır; undo/redo; qaralama saxlanılır | ✅ | |
| 0.10 | Düzəlişi Claude sessiyasına qaytarmaq | ✅ | Avtomatik (artifact db) və ya “Düzəlişi kopyala” |
| 0.11 | Analiz keşi (mənbə + parametrlər dəyişməyibsə təkrar transkripsiya yoxdur) | ✅ | |
| 0.13 | Müştəri profili (expert-reels `experts/*.json`) montaja tətbiq olunur | ✅ | Yalnız seçilən müştərinin faylı oxunur; törəmə rənglər “təsdiqlənməyib” kimi qeyd olunur |
| 0.14 | Redaktor: başlıq/altyazının mətni, şrifti (Montserrat, Caveat — OFL), ölçüsü, rəngi, fonu, yeri, vaxtı; bütün altyazıların ümumi üslubu | ✅ | Real layihədə emulyasiya + render müqayisəsi |
| 0.15 | Redaktor: klipi bölmək, uzatmaq, silmək, sırasını dəyişmək; öz səsi və altyazılar uyğunlaşır | ✅ | Altyazı ID-ləri bölmədən sonra sabit qalır (sərhəddəki biri istisna) |
| 0.16 | Redaktor: musiqi/səs effekti faylı əlavə etmək, yeri, hissəsi, səsi; danışıq/musiqi/effekt səviyyələri; danışıqda musiqinin azalması | 🟡 | Real səhifədə asset yükləmə sınaq əvəzi ilə yoxlanılıb; iPhone-da fayl seçimi yoxlanılmayıb. Lisenziyalı musiqi kitabxanası ⛔ |
| 0.17 | Redaktor: kadr, yaxınlaşma, güzgü (yazıları çevirmir), işıq, kontrast, doyumluluq, temperatur, filtr şablonları | ✅ | Rəng önizləməsi təxminidir |
| 0.18 | Yüngül yumşaltma (bütün kadr, kənarları qoruyur) | ✅ | Üzü ayrıca seçən retuş ⛔ — düymə qoyulmayıb |
| 0.19 | Altyazı sətri kadra sığır, cümlə/vergüldən keçmir | ✅ | ffmpeg mətni bölmədiyi üçün simvol limiti |
| 0.12 | Token istifadəsinin ölçülməsi | ⛔ | Bu sessiyadan token sayğacına giriş yoxdur — ölçülmür |

## 1. Telefondan açılan panel
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 1.1 | HTTPS ünvanından açılır | ⛔ | Server (VPS) hesabı lazımdır. `deploy/` hazırdır (Docker + Caddy, avtomatik sertifikat). Docker image bu sessiyada qurula bilmədi (sandbox-da DNS yoxdur, Docker Hub 429) — ilk quruluş serverdə yoxlanmalıdır. Ödənişli resurs təsdiqsiz aktivləşdirilmir |
| 1.2 | Video emalı və render serverdə | ✅ | Bütün emal server işləridir |
| 1.3 | Layihə və media daimi saxlanılır | ✅ | `MONTAJ_DATA_DIR` (Docker volume) |
| 1.4 | Giriş qorunur | ✅ | Parol + HMAC imzalı HttpOnly/Secure cookie; bütün API və media qorunur |
| 1.5 | Müştəri videoları və açarlar açıq yayımlanmır | ✅ | Media yalnız girişlə; açarlar yalnız mühit dəyişəni; status yalnız “var/yox” göstərir |
| 1.6 | Telefon kilidlənsə iş davam edir; yenidən açanda vəziyyət bərpa olunur | ✅ | İş diskdə (test: restart təqlidi); storyboard düzəlişi səhifəni yenidən açanda qalır (brauzer testi). Real iPhone kilidi ilə yoxlanılmayıb. İşlər diskdə saxlanılır, panel açılanda aktiv işləri göstərir. Server restartında yarımçıq iş “dayandı — yenidən başlat” kimi görünür |
| 1.7 | Hesab/ödəniş maneəsi, xidmət və xərc göstərilir | 🟡 | `deploy/README.md` (VPS — hazırkı büdcəyə daxil deyil, aktivləşdirilməyib). Əlavə xərcsiz yol: `BUDCE_YOLU.md` |

## 2. Sadə istifadə axını
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 2.1 | Drive linki daxil etmək | 🟡 | “Linki olan hər kəs” paylaşımlı fayl; orijinal baytlar saxta Drive serveri ilə yoxlanılıb, real Drive faylı ilə yox. Qovluq linki və şəxsi fayl üçün Google OAuth lazımdır (⛔) |
| 2.2 | Telefondan video və şəkil yükləmək | ✅ | Bir neçə fayl; şəkillər 4 s-lik klip olur |
| 2.3 | Bir neçə fayldan layihə | ✅ | |
| 2.4 | Ardıcıl “indi bunu edirəm” mətnləri yoxdur; sadə göstərici | ✅ | Proses zolağı |
| 2.5 | Xətada səbəb + istifadəçi addımı | ✅ | |
| 2.6 | Texniki loglar ayrıca diaqnostika bölməsində | ✅ | |

## 3. Müştəri seçimi
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 3.1 | “Kimin videosudur?” pəncərəsi, axtarış | ✅ | |
| 3.2 | 17 ilkin ad | ✅ | Brend məlumatı boşdur — uydurulmayıb |
| 3.3 | Yeni müştəri / birdəfəlik layihə | ✅ | |
| 3.4 | Ad, sahə, rəng kodları, şrift, loqo, montaj üstünlükləri | ✅ | Şrift adı saxlanılır və göstərilir; render hələ standart şriftlə (DejaVu Sans) — şrift faylı yükləmə yoxdur (🟡) |
| 3.5 | Seçəndə rəng nümunələri, şrift, loqo görünür | ✅ | |
| 3.6 | “Yalnız bu layihəyə” / “Müştəri profilində saxla” | ✅ | |

## 4. Montaj seçimləri
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 4.1 | Bütün formatlar hamı üçün açıq | ✅ | |
| 4.2 | Format / Məqsəd / Üslub / Əlavələr qrupları, çoxlu seçim | ✅ | |
| 4.3 | Hər qrupda “Sistem təklif etsin” | ✅ | |
| 4.4 | Müddət ayrıca, məcburi 30/60 yoxdur | ✅ | |

## 5. Kəsim qaydaları
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 5.1 | Kəsim rejimi: olduğu kimi / təklif et (standart) / avtomatik təmizlə | ✅ | |
| 5.2 | Pauza, nəfəs, vurğu səssizliyi səhv sayılmır | 🟡 | Yalnız uzun (≥1,2 s) sükut namizəddir, 0,25 s nəfəs payı saxlanılır. Real danışıqla yoxlanılmayıb |
| 5.3 | Söz və hecaların yarıda kəsilməməsi (hədəf) | 🟡 | ZƏMANƏT DEYİL: kəsim nöqtəsi Whisper-in söz vaxtlarına və səssizlik ölçüsünə görə seçilir. Whisper sözlərin sərhədini səhv verə və ya səssizlikdə söz uydura bilir (sintetik testdə görüldü). Real Azərbaycan danışığı ilə yoxlanılmayıb |
| 5.4 | Avtomatik təmizləmə də storyboard təsdiqindən sonra | ✅ | |
| 5.5 | Mənbə silinmir; kənarı uzadaraq geri qaytarmaq | ✅ | |
| 5.6 | Video + öz səsi birlikdə | ✅ | |
| 5.7 | Əl ilə düzəlişləri AI əvəz etmir | ✅ | |

## 6. Kadraj
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 6.1 | Avtomatik 9:16 təklifi | 🟡 | Kadraj məntiqi testlə, MediaPipe işləyir; real insan üzü olan video ilə yoxlanılmayıb |
| 6.2 | Əyriliyin düzəldilməsi | 🟡 | Yalnız əl ilə fırlatma sürgüsü; avtomatik əyrilik aşkarlanması ⛔ yoxdur |
| 6.3 | Baş üstü boşluq / kənarların azaldılması, baş-çənə kəsilmir | 🟡 | MediaPipe üz aşkarlanması; real insan videosu ilə yoxlanılmayıb |
| 6.4 | Məhsul/geyim/iki nəfər/tədbir — vacib obyektlər qorunur | 🟡 | Bir neçə üz varsa hamısı kadra salınır; obyekt (məhsul) aşkarlanması ⛔ yoxdur — bu növlərdə kadraj “əl ilə” rejimdə təklif edilir |
| 6.5 | Hər videonu üzə yaxınlaşdırmır | ✅ | Ölçü dəyişmir, yalnız 9:16 pəncərənin yeri |
| 6.6 | Yumşaq izləmə | ✅ | Hamarlanmış açar kadrlar |
| 6.7 | Orijinal / təklif müqayisəsi, əl ilə dəyişmək, sıfırlamaq | ✅ | |
| 6.8 | Həddindən artıq crop xəbərdarlığı, uydurma doldurma yoxdur | ✅ | |

## 7. Vizual storyboard və AI
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 7.1 | Faktiki AI bağlantısı | 🟡 | Claude API kodu hazırdır, amma API büdcəyə daxil deyil — açar yoxdur, aktivləşdirilməyəcək. Əlavə xərcsiz yolda plan istifadəçinin başlatdığı Claude Code sessiyasında hazırlanır (avtomatik/daimi bağlantı deyil) |
| 7.2 | Səssizlik/doldurucu söz AI kimi təqdim edilmir | ✅ | Açar olmadan “qaydalara əsaslanan təklif” kimi işarələnir |
| 7.3 | Real kadrlarla şəkilli storyboard: hissələr, açılış, mətn, qrafika/B-roll, musiqi, keçid | ✅ | |
| 7.4 | Qısa hərəkətli önizləmə | 🟡 | “▶ Önizlə” kartın hissəsini oynadır; avtomatik testlə yoxlanılmayıb |
| 7.5 | Təsdiqlə / Bu hissəni dəyiş / Alternativ göstər; tək kart | ✅ | Açarsız rejimdə alternativ — qonşu söz sərhədləri |
| 7.6 | Təsdiqsiz tətbiq yoxdur | ✅ | |
| 7.7 | Paneldaxili AI bağlantısı sessiyadakı Claude-dan ayrıdır; xidmət, açar, xərc | ✅ | Açar yoxlaması yalnız “var/işləyir” göstərir |

## 8. Əl ilə görüntü düzəlişləri
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 8.1 | Avtomatik filtr/retuş tətbiq edilmir | ✅ | |
| 8.2 | Güzgü (klip / bütün çəkiliş), mətn və loqo çevrilmir | ✅ | |
| 8.3 | Dəri yumşaltma, üzün işığı | ⛔ | Hərəkət boyunca izlənən üz maskası ilə kadr-kadr emal hələ yazılmayıb — düymə qoyulmayıb |
| 8.4 | Paltarı tündləşdirmə/ton | ⛔ | Paltar seqmentasiya modeli yoxdur — düymə qoyulmayıb |
| 8.5 | Arxa fon bulanıqlığı | ⛔ | Seqmentasiya ilə kadr-kadr render keçidi yazılmayıb — düymə qoyulmayıb |
| 8.6 | Parlaqlıq, kontrast, temperatur, doyumluluq | ✅ | Render-də FFmpeg; önizləmədə CSS (temperatur önizləmədə təxminidir) |
| 8.7 | Əvvəl/sonra, sıfırlama | ✅ | |
| 8.8 | Rəng korreksiyası: `session looks` 3 təmsilçi kadr × (Orijinal, A təbii, B yumşaq-isti, C təmiz-neytral), render ilə eyni filtrlər; seçim planda `look`; fərqli işıqlı kliplər yaxınlaşdırılır; əl ilə rəngə toxunulmur; süni kəskinlik yoxdur | ✅ | Testlər: `test_plan_look_choice_and_manual_color_kept`, `test_looks_sheet`. Günel videosunda vizual yoxlanıb |

## 9. Musiqi, effektlər, qrafika, sonluq
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 9.1 | Mövzuya uyğun musiqi təklifi, hüququ məlum mənbə | ⛔ | Repoda lisenziyası təsdiqlənmiş musiqi yoxdur; Pixabay/Freesound açarı yoxdur. Öz musiqini yükləmək ✅ |
| 9.2 | Danışıq/musiqi/səsləndirmə/effekt səviyyələri ayrıca | ✅ | |
| 9.3 | Musiqinin hissəsi və vaxtı | ✅ | Klip kənarları və yeri |
| 9.4 | Danışıq zamanı musiqinin azalması — ayrıca seçim | 🟡 | Render-də sidechain işləyir (test), azalmanın səviyyəsi ölçülməyib; önizləmədə təxmini |
| 9.5 | Subtitr/keçid/motion/B-roll yalnız uyğun olduqda | 🟡 | Storyboard-da təklif; subtitr transkriptdən; keçid/motion/B-roll render-də ⛔ |
| 9.6 | Qrafika və SFX alternativ kitabxanası | ⛔ | Lisenziyası məlum material yoxdur |
| 9.7 | Loqo: yükləmə, yer, ölçü | ✅ | |
| 9.8 | Animasiyalı sonluq, loqolu bitiş, əlaqə, CTA — söndürülə bilir | ✅ | Sadə fade animasiyası |
| 9.9 | Səsləndirmə (kişi/qadın, Azərbaycan dili) | ⛔ | Azure TTS (az-AZ) kodu yoxdur/açar yoxdur — hazır sayılmır |

## 10. Keyfiyyət
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 10.1 | Drive-dan orijinal fayl | 🟡 | Yükləmə birbaşa orijinal faylı götürür; real Drive ilə yoxlanılmayıb |
| 10.2 | Orijinal dəyişmir; render orijinaldan | ✅ | |
| 10.3 | Ölçü/fps/rəng səbəbsiz dəyişmir; çevrilmələr göstərilir | ✅ | İxrac pəncərəsində siyahı |
| 10.4 | HDR/SDR, iPhone HEVC | 🟡 | HDR (PQ/HLG) → SDR tonemap; sintetik HEVC/HLG ilə yoxlanılıb, real iPhone faylı ilə yox |
| 10.5 | “Sıfır sıxılma” vədi yoxdur, keyfiyyətli ixrac | ✅ | CRF 18 |
| 10.6 | Hər dəfə orijinaldan render | ✅ | |

## 11. Caption və paylaşma
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 11.1 | Azərbaycan dilində caption təklifi (real məzmun + üslub) | 🟡 | Claude API ilə; açar yoxdur → düymə söndürülüb |
| 11.2 | Redaktə və kopyalama | ✅ | |
| 11.3 | Son ekran: önizləmə, cover, caption, Paylaş, Instagram-ı aç, MP4 endir | ✅ | |
| 11.4 | “Paylaş” iPhone paylaşma menyusuna MP4 ötürür | 🟡 | Web Share API (fayl). Real iPhone-da yoxlanılmayıb |
| 11.5 | Instagram/TikTok-un videonu qəbul etməsi | ⛔ | Real cihaz lazımdır |
| 11.6 | Instagram keçidi ötürmə kimi təqdim edilmir; hesab iddiası yoxdur | ✅ | |
| 11.7 | İstifadəçinin son əməliyyatı olmadan paylaşım yoxdur | ✅ | |

## 12. Real material ilə təsdiq tələb edən yoxlamalar (hamısı ⛔ — material yoxdur)
Azərbaycan dilində transkripsiya, yarımçıq sözlər, real üz kadrajı, real iPhone HEVC/HDR,
real danışıqda səs sinxronu və görünən keyfiyyət, iPhone Safari, Instagram/TikTok qəbulu.

## 13. Peşəkar montaj qatı (istinad layihələrdən: expert-reels profilləri)
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 13.1 | Söz-söz altyazı, aktiv söz vurğu rəngində | ✅ | `graphics.js` (önizləmə) = Chromium rasterizasiya (render) |
| 13.2 | Hook başlıq, bölmə, vurğu, siyahı (maddələr vaxtla), məlumat kartı | ✅ | Hər biri ayrıca redaktə: mətn, şrift, ölçü, rəng, fon, yer, vaxt, animasiya |
| 13.3 | Ölçülü zoom, sintez SFX (whoosh/pop), musiqi/SFX fade | ✅ | `session plan`; B-roll yoxdur (material yoxdur) |
| 13.4 | Altyazı: söz düzəlişi, layihədə hər yerdə dəyiş, böl, birləşdir | ✅ | Səs/video dəyişmir; manual mətn avtomatik analizlə yazılmır |
| 13.5 | Redaktordakı dəyişiklik MP4-ə keçir, qalan montaj saxlanır | ✅ | `e2e_editor_gfx.mjs` + render yoxlanıldı (Chromium emulyasiyası, real Safari deyil) |
| 13.6 | Telefondan musiqi | 🟡 | Yalnız .m4a/.mp4 (artifakt mp3/wav qəbul etmir) |
| 13.7 | “Dataclone 3” motion qrafikası | ⛔ | Repoda tapılmadı |
| 13.8 | Üz/məhsul üçün avtomatik yer qoruyucusu, smooth push-zoom, PIP | ⛔ | Hələ köçürülməyib |

## 14. Əsas iş axını (IS_AXINI.md) — panelsiz
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 14.1 | Bir qısa sorğu (yalnız çatışmayan sahələr) | 🟡 | Sessiyadakı `AskUserQuestion` ilə; real istifadədə yoxlanılmayıb |
| 14.2 | 3 vizual storyboard variantı (real kadrlar + qrafika, 540p önizləmə), layihə dəyişmir; `choose` ilə tətbiq | ✅ | `test_variants_and_choose` (sintetik). Variantların yaradıcı fərqi hər video üçün sessiyadakı Claude-un işidir |
| 14.3 | Təkrar/alınmayan hissənin çıxarılması: sərhəd səsin ən sakit yerinə, söz kəsilmir, şübhədə material saxlanır | ✅ | `test_cut_safe_boundary_keeps_words` (sintetik). Real danışıqla yoxlanılmayıb |
| 14.4 | Yekun render yoxlaması: kəsim sərhədləri (enerji + söz), səs/görüntü, kliklər, kəsim yanındakı sözlərin yenidən tanınması | ✅ | Günel videosunda işlədildi; qulaqla dinləmə əvəz etmir (hesabatda yazılır) |
| 14.5 | Şübhəli sözlər siyahısı (vaxtla), düzəlişlərin yadda qalması | ✅ | `words`, `fix-word` (subtitles.corrections) |
| 14.6 | Dəqiq transkripsiya | ✅ | `large-v3-turbo` standart: Günel videosunda “small”-ın səhvləri (enişək, terəpiyası, məlim…) düzgün tanındı; 35 s səs ~18 s |
| 14.7 | Musiqi: dinləmə nümunələri, planla əlavə (fade, ducking) | 🟡 | Kod və test hazır; hüququ məlum musiqi kitabxanası ⛔ — istifadəçi faylı lazımdır |
| 14.8 | Kadraj düzəlişi hər videoda: əyrilik (fon xətləri, Hough) + üz ortalama, yaxınlaşma ≤1.12x; punch-in-də saxlanılır | ✅ | `test_framefix_tilt_and_center` (sintetik) + Günel videosu: -1.5° əyrilik tapılıb düzəldilib, üz ortalanıb. Stabilizasiya yoxdur |
| 14.9 | B-roll / araya kadr: `add-broll` (analizə düşmür); plan `broll`: cover (danışıq+altyazı davam edir), pip (mənbə nisbətində, üzü/altyazını örtməyən yer avtomatik), insert (təbii pauzada, söz/altyazı bölünmür, öz səsi ilə) | ✅ | `test_broll_cover_pip_insert` (kadr rəngi ilə render yoxlaması) + Günel videosunda sintetik materialla vizual yoxlama |
| 14.10 | Arxa səsin təmizlənməsi (DeepFilterNet3, yerli): auto — arxa səs azdırsa toxunulmur; zəiflətmə ≤20 dB; danışıq səviyyəsi bərpa; yalnız danışıq qatı | ✅ | Süni kafe səsi (SNR 8 dB) ilə yekun MP4: pauzada arxa səs −10 → −23 dB, SI-SDR 8.2 → 10.2 dB, danışıq səviyyəsi ±0.0 dB, gecikmə 0 ms. Günel (studiya): tətbiq edilmədi. `test_voice_clean_render_uses_clean_track`. Real kafe çəkilişi ilə yoxlanılmayıb |
| 14.11 | Claude-un hazırladığı B-roll: expert-reels şablonunun ~40 animasiyalı səhnəsi danışansız klip kimi (scene_clip.tsx), müştəri rəng ailəsində, keşlə; `scenes`, `make-broll`, plan `broll[].make` | ✅ | `test_claude_broll_scene_render_and_plan`; test layihəsində stat (cover) və checklist (insert) vizual yoxlandı. Səhnə mətni yalnız danışıqdan |
| 14.12 | Səs normallaşdırması: −14 LUFS, pik ≤ −1.5 dBTP (xətti loudnorm + limiter), video kopyalanır | ✅ | Günel −17.0 → −14.2 LUFS, pik −1.9; video axını bit-bərabər. `test_loudness_delivery_retakes` |
| 14.13 | Telefon/Instagram nüsxəsi (>40 MB olanda, eyni ölçü/fps) | ✅ | Günel 15 MB həddində SSIM 0.988 |
| 14.14 | Təkrar/yarımçıq cümlə köməkçisi (`retakes`) + hazır `cut` təklifi | ✅ | Sintetik testlə; real dublyajlı video ilə yoxlanılmayıb |
| 14.15 | Müştəri söz lüğəti: `glossary` (terms → Whisper hotwords, fixes → avtomatik düzəliş), `fix-word --remember` | ✅ | `test_glossary_save_restore_layout_lowlight` |
| 14.16 | Layihə paketi `save`/`restore` (orijinalsız ~1 MB; Drive-dan bərpa) | ✅ | Bərpa olunan layihənin renderi orijinalla piksel-bərabər (PSNR ∞) |
| 14.17 | `verify`: kart üzü örtürmü + Reels təhlükəsiz zonaları | ✅ | Günel videosunda 2 siyahının yuxarı zonaya toxunduğu düzgün tapıldı |
| 14.18 | Zəif işıq (D): zaman denoise (ştativ), kölgə qaldırma, gamma; qaranlıqda avtomatik təklif | ✅ | Süni qaranlıq+dən: parlaqlıq 51 → 95, nisbi dən 14.5% → 4.0%. Real kafe çəkilişi ilə yoxlanılmayıb |
| 15.1 | Reklam: `ad-scan` (təklif növü, qiymət köhnə/yeni, endirim, tarix, yer, çağırış+açar söz, faydalar — danışıqdan, uydurulmur) | ✅ | `test_ad_scan_plan_variants`; Azərbaycanca say sözləri (iki yüz əlli) də tanınır |
| 15.2 | Reklam: `ad-plan` — 3 variant (A M01+M02, B M03, C M04+punch-in), ardıcıllıq qorunur, `_review` siyahısı | ✅ | Test layihəsində plan → render |
| 15.3 | Yeni qrafikalar: `offer` (qiymət), `cta` (çağırış + açar söz), `badge` (nişan) — önizləmə = render | ✅ | Günel videosunda vizual yoxlama |
| 15.4 | Kartın avtomatik yeri: üzün altında (kiçilir ≥65%) / başın üstündə; plan qrafikasının standart yeri (əvvəl 0.5 idi) | ✅ | Günel: qiymət 79%, çağırış 84% ölçüdə, verify təmiz |
| 15.5 | `verify`: qrafikaların bir-birini örtməsi | ✅ | Nişan + başlıq toqquşması tapıldı və düzəldildi |
| 16.1 | Seminar: `highlights` — müstəqil hissələr (asılı və təşkilati başlanğıclar seçilmir, fikir sonunda bitir), bal + səbəb | ✅ | `test_seminar_highlights_extract`; sintetik seminar mətnində düzgün 2 hissə |
| 16.2 | `extract` — hissə ayrıca layihə (hard link, analiz təkrar istifadə) | ✅ | Eyni inode, təkrar transkripsiya yoxdur |
| 16.3 | Danışan şəxs (ağız hərəkəti, əlavə model yox) → `framefix` kadrajı ona qurur | ✅ | İki nəfərli 16:9 sınaq: hərəkət 17.4 vs 0.002, kadraj danışana |
| 16.4 | `new --size 1080x1920` — 16:9 → 9:16 kəsimi istəyə görə böyütmək | ✅ | Standart: böyütmə yoxdur |
| 17.1 | Motion graphics səhnələri: mg_bar, mg_line, mg_donut, mg_compare, mg_steps, mg_code, mg_kpi (müştəri rəngi, az yazılışı) | ✅ | 7-si də render olunur; Data Clone Academy rəngində vizual yoxlama |
| 17.2 | `cover_pip`: səhnə tam kadr, danışan dairədə (sol-aşağı) | ✅ | `test_motion_graphics_scenes_scan_cover_pip` (kadr piksel yoxlaması) + Günel videosunda vizual |
| 17.3 | `mg-scan`: danışıqdakı rəqəmlər + səhnə təklifi (il şəkilçisi, say sözləri; rəqəmlər birləşmir) | ✅ | Unit test |
| 18.1 | Nağıl obraz kitabxanası (tülkü, dovşan, ayı, pişik, uşaq) + fonlar, hərəkətlər (nəfəs, göz qırpma, danışma, əl, tullanma, giriş) | ✅ | Günel rəngində vizual yoxlama; qolların yeri düzəldildi |
| 18.2 | `tale-plan`: danışıqdan obraz/məkan/hərəkət, obraz yeri sabit, olmayan obraz uydurulmur | ✅ | `test_tale_plan_scenes_sticker` |
| 18.3 | `sticker`: şəffaf obraz (ProRes 4444 alfa) real videonun üstündə | ✅ | Kadr piksel yoxlaması + Günel videosunda vizual |
| 18.4 | Nağıl səhnəsində danışanın dairəsi səmada (obrazları örtmür) | ✅ | Vizual |
| 19.1 | `carousel-plan`: fikir slaydları (sıra sözləri "Birincisi/İkincisi", pauza, bərabər bölgü), örtük + CTA, qısa hook birləşir, üst-üstə düşmür | ✅ | `test_video_carousel` + Günel videosu (3 slayd) |
| 19.2 | `carousel`: slayd əsas montajdan kəsilir (əsas dəyişmir), 1080x1350, sayğac/başlıq/altyazı, örtük + ümumi şəkil | ✅ | `test_video_carousel` (ölçü, müddət) + `karusel.jpg` vizual |
| 20.1 | Növ reyestri `montaj/types.py`: 17 növ (VIDEO_TYPES 1–15 + motion graphics + loqo), M01–M14, hər növün statusu/çatışmayanı, 3 storyboard variantı, əmrləri, qaydaları; `types`, `types <N>`, `types --approaches` | ✅ | `test_video_type_registry` (reyestr ↔ VIDEO_TYPES.md uyğunluğu) |
| 20.2 | Sorğu reyestrdən: `types --survey` (ailə → növ → məqsəd; sual başına ≤4 seçim; planlaşdırılan növ çıxmır) | ✅ | Unit test |
| 20.3 | Layihədə növ qeydi: `new --type/--extra/--subtype/--uncertain`, `set-type`; növün formatı (15 → 16:9) | ✅ | Test: 16:9 layihə |
| 20.4 | `storyboard` sonunda növün variantları + müştərinin son 3 seçimi; `choose` → profil `history` (növ, yanaşma, variant, rəng, altyazı) | ✅ | Test (müvəqqəti profil) |
| 20.5 | `verify` növ qaydaları: qrafikada danışıqda olmayan rəqəm, mətnin ardıcıllığı (3, 8, 15), üfüqi dərs (15) | ✅ | Test: 350 AZN uydurma → problem; sıra dəyişəndə → problem |

